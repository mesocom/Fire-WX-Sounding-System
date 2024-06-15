import pandas as pd
import numpy as np
from scipy.signal import medfilt
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from metpy.plots import SkewT, Hodograph
from metpy.units import units
from metpy.calc import cape_cin, lcl, lfc, el, mixed_layer_cape_cin, parcel_profile
import matplotlib.gridspec as gridspec
from PIL import Image
from firesounding import *

##################
# Config
##################

facecolor = 'white'
textcolor = 'black'

dpi = 250

# Define RAOB standard / other desired levels in hPa
raob_levels = np.array([1000, 925, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10]) * units.hPa

hodo_max_velocity_kts = 100

# Define the input file path
input_file = './sounding_data.csv'
logo1_path = './logo1.png'  # Replace with your actual logo file path
logo2_path = './logo2.png'  # Replace with your actual logo file path
info_text = 'FAMSEE Man Creek 0340 Launch 2'
output_file = 'sounding_plot.png'


##################
# Process data
##################

# Read the data
data = pd.read_csv(input_file)

# Ensure the data is sorted by pressure in descending order
data = data.sort_values(by='pressure', ascending=False)

# Apply median filter to smooth out pressure values
data['pressure'] = medfilt(data['pressure'], kernel_size=3)

# Drop rows where any value is -99.9
data = data[(data[['pressure', 'temperature', 'dewpoint', 'u_wind', 'v_wind']] != -99.9).all(axis=1)]

# Convert data to appropriate units
pressure = data['pressure'].values * units.hPa
temperature = data['temperature'].values * units.degC
dewpoint = data['dewpoint'].values * units.degC
u_wind = data['u_wind'].values * units.knots
v_wind = data['v_wind'].values * units.knots


##################
# Global figure
##################

# Set global font properties to a common monospace font
plt.rcParams['font.family'] = 'monospace'
plt.rcParams['font.monospace'] = ['Courier New', 'Consolas', 'DejaVu Sans Mono']
plt.rcParams['font.size'] = 10
plt.rcParams['font.weight'] = 'bold'

# Golden ratio
golden_ratio = (1 + 5 ** 0.5) / 2

# Create a new figure with golden ratio dimensions. The dimensions here give a good aspect ratio
fig = plt.figure(figsize=(9, 9 / golden_ratio), facecolor=facecolor)

# Grid for plots
gs = gridspec.GridSpec(3, 3, height_ratios=[1, 1, 1])


##################
# Skew-T
##################

skew = SkewT(fig, rotation=45, subplot=gs[:, :2])

# Set black background for the plot
skew.ax.set_facecolor(facecolor)

# Plot the data using normal plotting functions, in this case using
# log scaling in Y, as dictated by the typical meteorological plot
skew.plot(pressure, temperature, 'r')
skew.plot(pressure, dewpoint, 'g')

# Filter data to the specified RAOB + custom pressure levels
closest_levels = []
for level in raob_levels:
    idx = (np.abs(pressure - level)).argmin()
    closest_levels.append(idx)

closest_levels = np.unique(closest_levels)  # Remove duplicates

# Filter the data to only include the closest levels
pressure_filtered = pressure[closest_levels]
u_wind_filtered = u_wind[closest_levels]
v_wind_filtered = v_wind[closest_levels]

# Plot wind barbs at the filtered pressure levels
skew.plot_barbs(pressure_filtered, u_wind_filtered, v_wind_filtered,
	length=5, sizes=dict(emptybarb=0.1, spacing=0.2, height=0.4, width=0.1))

skew.ax.set_ylim(1050, 100)

# Add the relevant special lines
skew.plot_dry_adiabats(linewidth=0.5)
skew.plot_moist_adiabats(linewidth=0.5)
skew.plot_mixing_lines(linewidth=0.5)

# Good bounds for aspect ratio
skew.ax.set_xlim(-30, 50)

skew.ax.set_xlabel('')
skew.ax.set_ylabel('')


##################
# Hodograph
##################
ax = fig.add_subplot(gs[0:2, -1], facecolor=facecolor)
h = Hodograph(ax, component_range=hodo_max_velocity_kts)
h.add_grid(increment=20)

# Select data at every 250 meters increment
altitudes = data['altitude'].values

# Convert to pandas DataFrame
df = pd.DataFrame({
    'altitude': altitudes,
    'u_wind': u_wind,
    'v_wind': v_wind
})

# Calculate rolling mean with a window size (e.g., window of 10 points)
window_size = 50
df['u_wind_mean'] = df['u_wind'].rolling(window=window_size).mean()
df['v_wind_mean'] = df['v_wind'].rolling(window=window_size).mean()

# Drop NaN values resulting from rolling mean calculation
df = df.dropna()

# Define altitude ranges and corresponding colors
ranges = [
    (0, 500, 'magenta'),
    (500, 3000, 'red'),
    (3000, 7000, 'green'),
    (7000, 10000, 'blue')
]

# Plot each segment with the specified color, selecting every nth data point
n = 25
for lower, upper, color in ranges:
    mask = (df['altitude'] >= lower) & (df['altitude'] < upper)
    df_segment = df[mask]
    selected_indices = df_segment.index[::n]  # Select every nth index within the masked data
    h.plot(df_segment.loc[selected_indices, 'u_wind_mean'], df_segment.loc[selected_indices, 'v_wind_mean'], color=color, linewidth=1.5)

# Turn off axis ticks and labels
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel('')
ax.set_ylabel('')

# Add velocity labels on concentric rings along each axis
hodofont = 5
offset_x = 6
offset_y = 4
increments = range(20, hodo_max_velocity_kts+1, 20)
for i in increments:
    ax.text(i-offset_x, 0+offset_y, str(i), color=textcolor, fontsize=hodofont, ha='center', va='center')
    ax.text(-i+offset_x, 0+offset_y, str(i), color=textcolor, fontsize=hodofont, ha='center', va='center')
    ax.text(0+offset_x, i-offset_y, str(i), color=textcolor, fontsize=hodofont, ha='center', va='center')
    ax.text(0+offset_x, -i+offset_y, str(i), color=textcolor, fontsize=hodofont, ha='center', va='center')


##################
# Sounding indices
##################

# Compute the parcel profile
parcel_prof = parcel_profile(pressure, temperature[0], dewpoint[0])

# Compute CAPE and CIN using the parcel profile
cape, cin = cape_cin(pressure, temperature, dewpoint, parcel_prof)

# Compute other indices
lcl_pressure, lcl_temperature = lcl(pressure[0], temperature[0], dewpoint[0])
lfc_pressure, lfc_temperature = lfc(pressure, temperature, dewpoint)
el_pressure, el_temperature = el(pressure, temperature, dewpoint)
cape = cape.magnitude
cin = cin.magnitude
lcl_pressure = lcl_pressure.magnitude
lfc_pressure = lfc_pressure.magnitude
el_pressure = el_pressure.magnitude

# Calculate Haines Index (low, mid, high)
haines = haines_index(pressure, temperature, dewpoint, p_levels=[50, 850, 700])

# Calculate mixing height
# mixing_ht = mixing_height(pressure, temperature, height=pressure, pblh=None, method='parcel')

# Compute the surface wind speed and direction
surface_u_wind = u_wind[0]
surface_v_wind = v_wind[0]
surface_wind_speed = np.sqrt(surface_u_wind**2 + surface_v_wind**2)
surface_wind_dir = (270 - np.arctan2(surface_v_wind.m, surface_u_wind.m) * (180 / np.pi)) % 360  # Convert to degrees and normalize

# Strip units from temperature and dewpoint
temperature_celsius = temperature.to(units.degC).magnitude
dewpoint_celsius = dewpoint.to(units.degC).magnitude

# Compute relative humidity
rh = 100 * (np.exp((17.625 * dewpoint_celsius) / (243.04 + dewpoint_celsius)) /
            np.exp((17.625 * temperature_celsius) / (243.04 + temperature_celsius))) * units.percent

# Dew point depression
dew_point_dep = temperature - dewpoint

# Plot indices text
indices_ax = fig.add_subplot(gs[-1, -1])
indices_ax.axis('off')

indices_text = (
    f"CAPE: {cape:.0f} J/kg\n"
    f"CIN: {cin:.0f} J/kg\n"
    f"LCL: {lcl_pressure:.0f} hPa\n"
    f"LFC: {lfc_pressure:.0f} hPa\n"
    f"EL: {el_pressure:.0f} hPa\n"
    f"Haines: {haines}\n"
    # f"Haines Index (Mid): {haines_mid}\n"
    # f"Haines Index (High): {haines_high}\n"
    # f"Mixing Height: {mixing_ht.magnitude:.2f} m\n"
    f"Sfc Wind: {surface_wind_speed.magnitude:.0f} kts @ {surface_wind_dir:.0f}°\n"
    f"Sfc T: {temperature.magnitude[0]:.1f} °C\n"
    f"Sfc RH: {rh.magnitude[0]:.0f} %\n"
    f"Sfc DD: {dew_point_dep.magnitude[0]:.1f} °C\n"

)

indices_ax.text(0.5, 0.5, indices_text, horizontalalignment='center', verticalalignment='center',
                transform=indices_ax.transAxes, fontsize=10, bbox=None)


##################
# Logos and text
##################

# Load the logos
logo1 = Image.open(logo1_path)
logo2 = Image.open(logo2_path)

# Calculate new sizes while maintaining aspect ratio
logo1_scale=0.7
logo2_scale=0.18
logo1_size = (int(logo1.width * logo1_scale), int(logo1.height * logo1_scale))
logo2_size = (int(logo2.width * logo2_scale), int(logo2.height * logo2_scale))

# Resize the logos
logo1 = logo1.resize(logo1_size, Image.ANTIALIAS)
logo2 = logo2.resize(logo2_size, Image.ANTIALIAS)

# Add logos to the figure
fig_width, fig_height = fig.get_size_inches() * dpi
height_factor = 2.7
fig.figimage(logo1, 20, fig_height - logo1.height*height_factor, zorder=1)
fig.figimage(logo2, logo1.width + 30, fig_height - logo2.height*height_factor, zorder=1)

# Add info text
fig.text(0.95, 0.95, info_text, horizontalalignment='right', verticalalignment='top', color=textcolor, fontsize=10)


##################
# Export
##################

# Save the plot
plt.savefig(output_file, facecolor=facecolor, dpi = dpi, bbox_inches='tight')

print(f'Plot saved to {output_file}')
