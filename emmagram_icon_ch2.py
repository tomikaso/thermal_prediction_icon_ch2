import numpy as np

# Load it back
temperature = np.load('temperature_icon_ch2.npy')
altitude = np.load('altitude_icon_ch2.npy')
dewpoint = np.load('dewpoint_icon_ch2.npy')

for loc in range(temperature.shape[0]):
    print(f"Location {loc}:")
    for level in range(temperature.shape[1]):
        temp_celsius = temperature[loc, level, 0]
        dew_point = dewpoint[loc, level, 0]
        h_m = altitude[loc, level, 0]
        print(f"Level {level}: Temperature = {temp_celsius:.2f} °C, Dew Point = {dew_point:.2f} °C, Altitude = {h_m:.2f} m")