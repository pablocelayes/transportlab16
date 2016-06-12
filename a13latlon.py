from rd_coords_convert import *
import pandas as pd

conv = RDWGSConverter()
df = pd.read_csv('a13/Rechts_RDCoordinaten_2011.csv', header=None)

for i, row in df.iterrows():
    new_rows.append(conv.fromRdToWgs(row))

df_new = pd.DataFrame(new_rows)
df_new.columns=['lat','lon']

df_new.to_csv('a13/Rechts_LatLonCoordinaten_2011.csv')
