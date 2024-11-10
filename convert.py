import pandas as pd
import numpy as np
import re

# Define the input and output file paths
input_file = 'input_graw.txt'
output_file = 'output_standard.csv'

# Read the data
data = pd.read_csv(input_file, sep='\t', encoding = 'Latin')

# Function to replace dashes or multiple spaces with -99.9 and strip whitespace
def clean_data(value):
    if isinstance(value, str):
        value = re.sub(r'-+', '-99.9', value)  # Replace dashes with -99.9
        value = re.sub(r'\s+', ' ', value).strip()  # Replace multiple spaces/tabs with a single space and strip
    return value

# Apply the cleaning function to all data
data = data.applymap(clean_data)

# Convert necessary columns to float
data['P [hPa]'] = data['P [hPa]'].astype(float)
data['T [°C]'] = data['T [°C]'].astype(float)
data['Dew [°C]'] = data['Dew [°C]'].astype(float)
data['Ws [m/s]'] = data['Ws [m/s]'].astype(float)
data['Wd [°]'] = data['Wd [°]'].astype(float)
data['Geopot [m]'] = data['Geopot [m]'].astype(float)


# Rename the columns to match the expected format
data.rename(columns={
    'P [hPa]': 'pressure',
    'T [°C]': 'temperature',
    'Dew [°C]': 'dewpoint',
    'Ws [m/s]': 'wind_speed',
    'Wd [°]': 'wind_direction',
    'Geopot [m]': "altitude"
}, inplace=True)

# Calculate u and v wind components and round to 3 decimal points
data['u_wind'] = (data['wind_speed'] * np.sin(np.radians(data['wind_direction']))).round(3)
data['v_wind'] = (data['wind_speed'] * np.cos(np.radians(data['wind_direction']))).round(3)

# Drop rows where any value is -99.9
data = data[(data[['pressure', 'temperature', 'dewpoint', 'u_wind', 'v_wind']] != -99.9).all(axis=1)]

# Filter duplicate pressure levels
data = data.drop_duplicates(subset='pressure')

# Select and reorder the necessary columns
data = data[['pressure', 'temperature', 'dewpoint', 'u_wind', 'v_wind', 'altitude']]

# Save the data to a CSV file
data.to_csv(output_file, index=False)

print(f'Data converted and saved to {output_file}')