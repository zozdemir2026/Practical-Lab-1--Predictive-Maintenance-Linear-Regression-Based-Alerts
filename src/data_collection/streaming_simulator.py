
## Streaming Simulator Class

import pandas as pd

class StreamingSimulator:
   def __init__(self, file_path):
       self.file_path = file_path
       self.data = pd.read_csv(file_path)
       self.current_index = 0

   def nextDataPoint(self):
    if self.current_index < len(self.data):
        data_point = self.data.iloc[[self.current_index]]
        self.current_index += 1
        return data_point
    else:
        print("End of file reached.")
        return None