import pandas as pd
import numpy as np
import re

# Define the input and output file paths
input_file = './FASMEE_MAN_CREEK_0340_B2.txt'
output_file = './sounding_data.csv'

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
data['P [h Pa]'] = data['P [h Pa]'].astype(float)
data['T [°C]'] = data['T [°C]'].astype(float)
data['Dew [°C]'] = data['Dew [°C]'].astype(float)
data['Wsp [kn]'] = data['Wsp [kn]'].astype(float)
data['Wdir [°]'] = data['Wdir [°]'].astype(float)
data['Altitude [m]'] = data['Altitude [m]'].astype(float)


# Rename the columns to match the expected format
data.rename(columns={
    'P [h Pa]': 'pressure',
    'T [°C]': 'temperature',
    'Dew [°C]': 'dewpoint',
    'Wsp [kn]': 'wind_speed',
    'Wdir [°]': 'wind_direction',
    'Altitude [m]': "altitude"
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