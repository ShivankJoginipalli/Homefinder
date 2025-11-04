import pandas as pd

df = pd.read_csv('../data/chicago_prop_data.csv')

df_110k = df.head(110000)

df_110k.to_csv('properties_110k.csv', index=False)

print(f"Done")