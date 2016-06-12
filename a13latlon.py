from rd_coords_convert import *
import pandas as pd

conv = RDWGSConverter()

df = pd.read_csv('a13/Rechts_RDCoordinaten_2011.csv', header=None)
new_rows = [conv.fromRdToWgs(row) for i, row in df.iterrows()]
df_new = pd.DataFrame(new_rows)
df_new.columns=['lat','lon']
df_new.to_csv('a13/Rechts_LatLonCoordinaten_2011.csv', index=False)

df = pd.read_csv('a13/Links_RDCoordinaten_2011.csv', header=None)
new_rows = [conv.fromRdToWgs(row) for i, row in df.iterrows()]
df_new = pd.DataFrame(new_rows)
df_new.columns=['lat','lon']
df_new.to_csv('a13/Links_LatLonCoordinaten_2011.csv', index=False)
