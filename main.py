import csv
import pandas as pd

# PATH = 'samples/LOG-01-002-031-032.CSV'
# PATH = 'samples/LOG-01-032-033-002.CSV'
# PATH = 'samples/LOG-01-130-131-134.CSV'
PATH = 'samples/LOG-01-011AFB.CSV'
# PATH = 'samples/LOG-01-002-033-xxxx.CSV'

# df = pd.read_csv(PATH, sep='delimiter')
# print(df)

with open(PATH) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for idx, row in enumerate(csv_reader):
        print(f'{idx=} {row}')

