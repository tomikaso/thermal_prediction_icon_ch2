import numpy as np
import locations
import datetime as dt

leadtime = 21
init = "20261030"
loc = 0
radiation = np.load(f'radiation_icon_ch2_{init}.npy')

while  loc < locations.max_locations:
    time = 10
    while time < 21:
        rad = radiation[loc,  time]
        print(f"Location {loc}: {locations.name_start[loc]}, at {time} o'clock: {rad}")
        time = time + 1
    print(rad)
    loc = loc + 1