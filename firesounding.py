import numpy as np

# Function to calculate the Haines Index
def haines_index(pressure, temperature, dewpoint, p_levels):
    """
    Calculate the Haines Index.
    
    Parameters:
    - pressure: array of pressure levels
    - temperature: array of temperatures
    - dewpoint: array of dewpoints
    - p_levels: list of pressure levels to use for the calculation (e.g., [950, 850, 700])
    
    Returns:
    - Haines Index value
    """
    from metpy.units import concatenate, units

    # Ensure p_levels are in the same units as pressure
    p_levels = np.array(p_levels) * units.hPa
    
    # Convert pressure, temperature, and dewpoint to arrays without units for interpolation
    pressure = pressure.to(units.hPa)
    temperature = temperature.to(units.degC)
    dewpoint = dewpoint.to(units.degC)
    
    # Interpolate temperature and dewpoint to the required pressure levels
    t_low = np.interp(p_levels.m, pressure.m, temperature.m)# * units.degC
    t_mid = np.interp(p_levels.m, pressure.m, temperature.m)# * units.degC
    t_high = np.interp(p_levels.m, pressure.m, temperature.m)# * units.degC
    dp_low = np.interp(p_levels.m, pressure.m, dewpoint.m)# * units.degC
    
    # Calculate components A and B
    A = t_mid - t_low
    B = t_mid - dp_low
    
    # Calculate the stability term
    print(p_levels)
    test = np.array([950, 850, 700])
    if np.all(p_levels == test):  # Low-level
        if np.all(A <= 3): a = 1
        elif np.all(A <= 6): a = 2
        else: a = 3
    else:  # Mid-level
        if np.all(A <= 4): a = 1
        elif np.all(A <= 8): a = 2
        else: a = 3
    
    # Calculate the moisture term
    if np.all(B <= 1): b = 1
    elif np.all(B <= 5): b = 2
    else: b = 3
    
    # Haines Index is the sum of A and B
    haines_index = a + b
    return haines_index


def mixing_height(pressure, temperature):
    """
    Calculate the Mixing Height.
    
    Parameters:
    - pressure: array of pressure levels
    - temperature: array of temperatures
    
    Returns:
    - Mixing height in meters
    """
    from metpy.calc import dry_lapse, moist_lapse
    from metpy.units import units

    # Surface pressure and temperature
    surface_pressure = pressure[0]
    surface_temperature = temperature[0]

    # Assume mixing height is where the temperature difference is minimal
    dry_adiabat = dry_lapse(pressure, surface_temperature)
    
    # Calculate the temperature difference
    temp_diff = temperature - dry_adiabat
    
    # Find the level where the temperature difference is smallest
    mixing_height_idx = np.argmin(np.abs(temp_diff))
    mixing_height_pressure = pressure[mixing_height_idx]
    
    # Convert pressure to height (assuming standard atmosphere)
    mixing_height = (surface_pressure - mixing_height_pressure) * 8.4  # Rough estimate: 8.4 meters per hPa
    
    return mixing_height
