import pandas as pd

df = pd.read_csv('C:/Users/escal/Documents/DSA/Homefinder/data/chicago_data_cleaned.csv', low_memory= False)

df_110k = df.head(110000)

df_110k.to_csv('properties_110k.csv', index=False)

print(f"Done")