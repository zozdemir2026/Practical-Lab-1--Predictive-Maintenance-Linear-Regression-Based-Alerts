import time
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from IPython.display import clear_output, display


def draw_dashboard(
    dashboard_df,
    events_df,
    axes,
    total_records
):

    if dashboard_df.empty:
        return

    latest_row = dashboard_df.iloc[-1]
    latest_time = latest_row["recorded_at"]
    current_record = int(latest_row["record_number"])

    latest_statuses = [
        latest_row[f"{axis}_status"]
        for axis in axes
    ]

    if "ERROR" in latest_statuses:
        overall_status = "ERROR"
        action = "MAINTENANCE REQUIRED"

    elif "ALERT" in latest_statuses:
        overall_status = "ALERT"
        action = "MAINTENANCE RECOMMENDED"

    else:
        overall_status = "NORMAL"
        action = "NO ACTION REQUIRED"


    # =====================================================
    # FIGURE
    # =====================================================

    fig = plt.figure(figsize=(16, 10))

    gs = fig.add_gridspec(
        3,
        1,
        height_ratios=[0.8, 5, 1.6],
        hspace=0.42
    )


    # =====================================================
    # HEADER
    # =====================================================

    header_ax = fig.add_subplot(gs[0])
    header_ax.axis("off")

    header_ax.text(
        0.5,
        0.82,
        "Predictive Maintenance Dashboard",
        ha="center",
        fontsize=20,
        fontweight="bold"
    )

    header_ax.text(
        0.5,
        0.45,
        (
            f"{latest_time.strftime('%Y-%m-%d %H:%M:%S')}   |   "
            f"Records checked: {current_record} / {total_records}"
        ),
        ha="center",
        fontsize=10
    )

    header_ax.text(
        0.5,
        0.08,
        (
            f"CURRENT STATUS: {overall_status}   |   "
            f"{action}   |   "
            f"CONFIRMED EVENTS: {len(events_df)}"
        ),
        ha="center",
        fontsize=12,
        fontweight="bold"
    )


    # =====================================================
    # GRAPH
    # =====================================================

    ax = fig.add_subplot(gs[1])

    for axis in axes:

        ax.plot(
            dashboard_df["recorded_at"],
            dashboard_df[f"{axis}_actual"],
            linewidth=1.4,
            label=axis.replace("_", " ").title()
        )


    # Confirmed events visible in current window
    if not events_df.empty:

        window_start = dashboard_df["recorded_at"].min()
        window_end = dashboard_df["recorded_at"].max()

        visible_events = events_df[
            (events_df["confirmed_at"] >= window_start)
            &
            (events_df["confirmed_at"] <= window_end)
        ]

        for _, event in visible_events.iterrows():

            axis = event["axis"]

            event_row = dashboard_df[
                dashboard_df["recorded_at"]
                == event["confirmed_at"]
            ]

            if not event_row.empty:

                y_value = event_row.iloc[0][
                    f"{axis}_actual"
                ]

                marker = (
                    "X"
                    if event["event"] == "ERROR"
                    else "o"
                )

                size = (
                    180
                    if event["event"] == "ERROR"
                    else 140
                )

                ax.scatter(
                    event["confirmed_at"],
                    y_value,
                    marker=marker,
                    s=size,
                    zorder=10
                )


    ax.set_title(
        "Robot Current by Axis — Latest ~90 Seconds",
        fontsize=14,
        fontweight="bold",
        pad=14
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("Axis Current")

    ax.grid(
        True,
        alpha=0.25
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M:%S")
    )

    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator(
            minticks=5,
            maxticks=9
        )
    )

    plt.setp(
        ax.get_xticklabels(),
        rotation=35,
        ha="right"
    )

    ax.legend(
        loc="upper right",
        fontsize=8,
        ncol=2
    )


    # =====================================================
    # EVENTS TABLE
    # =====================================================

    table_ax = fig.add_subplot(gs[2])
    table_ax.axis("off")

    table_ax.set_title(
        "Recent Confirmed Anomaly Events",
        fontsize=12,
        fontweight="bold",
        pad=10
    )


    if not events_df.empty:

        recent_events = events_df.tail(5)

        table_data = []

        for _, event in recent_events.iterrows():

            action = (
                "Maintenance required"
                if event["event"] == "ERROR"
                else "Maintenance recommended"
            )

            table_data.append([
                event["confirmed_at"].strftime("%H:%M:%S"),
                event["axis"],
                event["event"],
                f'{event["residual"]:.2f}',
                f'{event["duration_seconds"]:.2f} sec',
                action
            ])


        table = table_ax.table(
            cellText=table_data,
            colLabels=[
                "Time",
                "Axis",
                "Status",
                "Residual",
                "Duration",
                "Action"
            ],
            loc="center",
            cellLoc="center"
        )

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.45)

        for col in range(6):
            table[(0, col)].set_text_props(
                weight="bold"
            )

    else:

        table_ax.text(
            0.5,
            0.5,
            "No confirmed ALERT or ERROR events yet.",
            ha="center",
            va="center"
        )


    fig.subplots_adjust(
        left=0.07,
        right=0.97,
        top=0.97,
        bottom=0.06
    )

    display(fig)
    plt.close(fig)


# =========================================================
# MAIN MONITORING FUNCTION
# =========================================================

def run_monitoring(
    database_url,
    train_df,
    models,
    thresholds,
    axes,
    window_size=45,
    sleep_seconds=0.05,
    T=6,
    refresh_every=5,
    limit=500
):

    train_start = train_df["recorded_at"].min()

    state_tracker = {
        axis: {
            "status": "NORMAL",
            "start_time": None,
            "logged": False
        }
        for axis in axes
    }

    events = []
    monitoring_results = []


    # =====================================================
    # READ TEST DATA
    # =====================================================

    connection = psycopg2.connect(
        database_url
    )

    query = f"""
    SELECT *
    FROM synthetic_stream
    ORDER BY recorded_at
    LIMIT {int(limit)};
    """

    stream_df = pd.read_sql_query(
        query,
        connection
    )

    connection.close()


    stream_df["recorded_at"] = pd.to_datetime(
        stream_df["recorded_at"],
        utc=True
    )

    total_records = len(stream_df)


    # =====================================================
    # PROCESS RECORDS
    # =====================================================

    for record_number, (_, row) in enumerate(
        stream_df.iterrows(),
        start=1
    ):

        current_time = row["recorded_at"]

        time_seconds = (
            current_time - train_start
        ).total_seconds()


        result = {
            "record_number": record_number,
            "recorded_at": current_time,
            "time_seconds": time_seconds
        }

        abnormal_axes = []


        # =================================================
        # CHECK ALL AXES
        # =================================================

        for axis in axes:

            actual = float(
                row[axis]
            )

            predicted = models[axis].predict(
                pd.DataFrame({
                    "time_seconds": [
                        time_seconds
                    ]
                })
            )[0]

            residual = (
                actual - predicted
            )

            min_c = thresholds[axis]["MinC"]
            max_c = thresholds[axis]["MaxC"]


            # Candidate status
            if residual >= max_c:
                candidate = "ERROR"

            elif residual >= min_c:
                candidate = "ALERT"

            else:
                candidate = "NORMAL"


            tracker = state_tracker[axis]


            # =================================================
            # NORMAL
            # =================================================

            if candidate == "NORMAL":

                tracker["status"] = "NORMAL"
                tracker["start_time"] = None
                tracker["logged"] = False

                final_status = "NORMAL"
                duration = 0


            # =================================================
            # ABNORMAL
            # =================================================

            else:

                if tracker["status"] != candidate:

                    tracker["status"] = candidate
                    tracker["start_time"] = current_time
                    tracker["logged"] = False


                duration = (
                    current_time
                    - tracker["start_time"]
                ).total_seconds()


                # Confirm after T seconds
                if duration >= T:

                    final_status = candidate

                    if not tracker["logged"]:

                        events.append({
                            "axis": axis,
                            "event": candidate,
                            "start_time":
                                tracker["start_time"],
                            "confirmed_at":
                                current_time,
                            "duration_seconds":
                                duration,
                            "actual":
                                actual,
                            "predicted":
                                predicted,
                            "residual":
                                residual
                        })

                        tracker["logged"] = True

                else:

                    final_status = (
                        f"{candidate}_CANDIDATE"
                    )


            # =================================================
            # SAVE RESULT
            # =================================================

            result[f"{axis}_actual"] = actual
            result[f"{axis}_predicted"] = predicted
            result[f"{axis}_residual"] = residual
            result[f"{axis}_status"] = final_status
            result[f"{axis}_duration"] = duration


            if final_status != "NORMAL":

                abnormal_axes.append(
                    f"{axis}: {final_status}"
                )


        monitoring_results.append(
            result
        )


        monitoring_df = pd.DataFrame(
            monitoring_results
        )

        dashboard_df = monitoring_df.tail(
            window_size
        )

        events_df = pd.DataFrame(
            events
        )


        # =================================================
        # DASHBOARD REFRESH
        # =================================================

        if (
            record_number % refresh_every == 0
            or abnormal_axes
            or record_number == 1
        ):

            clear_output(
                wait=True
            )

            draw_dashboard(
                dashboard_df,
                events_df,
                axes,
                total_records
            )


        time.sleep(
            sleep_seconds
        )


    # =====================================================
    # FINAL DATAFRAMES
    # =====================================================

    monitoring_df = pd.DataFrame(
        monitoring_results
    )

    events_df = pd.DataFrame(
        events
    )

    dashboard_df = monitoring_df.tail(
        window_size
    )


    clear_output(
        wait=True
    )

    draw_dashboard(
        dashboard_df,
        events_df,
        axes,
        total_records
    )


    print(
        f"Records checked: {len(monitoring_df)}"
    )

    print(
        f"Dashboard records: {len(dashboard_df)}"
    )

    print(
        f"Confirmed events: {len(events_df)}"
    )


    return (
        monitoring_df,
        events_df,
        dashboard_df
    )