import pandas as pd
from pandas import json_normalize
import json



# Load JSON data from the file
with open('top_artists_info.json', 'r') as file:
    json_data = json.load(file)

# Use json_normalize to convert the JSON object to a DataFrame
df = pd.json_normalize(json_data, sep='_')
df.to_csv('output_file.csv', index=False)


# Now, df should have your normalized data
print(df.head())