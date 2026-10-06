import numpy as np
import pandas as pd
from pathlib import Path


def generate_synthetic_data(
    train_df,
    models,
    axes,
    sampling_interval,
    project_root,
    n_test=500,
    random_seed=42
):
    np.random.seed(random_seed)

    synthetic_df = pd.DataFrame()

    # Start after the last training measurement
    last_time = train_df["time_seconds"].max()
    last_timestamp = train_df["recorded_at"].max()

    synthetic_df["time_seconds"] = (
        last_time
        + sampling_interval * np.arange(1, n_test + 1)
    )

    synthetic_df["recorded_at"] = (
        last_timestamp
        + pd.to_timedelta(
            sampling_interval * np.arange(1, n_test + 1),
            unit="s"
        )
    )

    synthetic_df["trait"] = "current"

    # Generate Axis 1 - Axis 8
    for axis in axes:

        predicted = models[axis].predict(
            synthetic_df[["time_seconds"]]
        )

        residual_std = train_df[
            f"{axis}_residual"
        ].std()

        noise = np.random.normal(
            loc=0,
            scale=residual_std,
            size=n_test
        )

        synthetic_df[axis] = predicted + noise

        # Prevent negative current values
        synthetic_df[axis] = synthetic_df[axis].clip(lower=0)

    # Save to data/generated/
    output_folder = Path(project_root) / "data" / "generated"
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / "synthetic_test.csv"

    synthetic_df.to_csv(
        output_path,
        index=False
    )

    print("Synthetic data created successfully.")
    print("Rows:", len(synthetic_df))
    print("Saved to:", output_path)

    return synthetic_df