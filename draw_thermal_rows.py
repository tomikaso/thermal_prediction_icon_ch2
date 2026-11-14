import numpy as np
import locations
import json
import thermal_model_ch2
import datetime as dt

fc_day = 0
start_time = dt.datetime.now()
init = start_time.strftime("%Y%m%d")
# init = "20261114"
path = "data/"
with open("load_status.json", "r") as file:
    load_status = json.load(file)
print(f"Last Leadtime: {load_status["leadtime"]}, model run: z{load_status["model_run"]}")
model_run = f'ICON-CH2, run: {init} z{load_status["model_run"]}'

temperature = np.load(f'{path}temperature_icon_ch2_{init}.npy')
altitude = np.load(f'{path}altitude_icon_ch2_{init}.npy')
dewpoint = np.load(f'{path}dewpoint_icon_ch2_{init}.npy')
wind_speed = np.load(f'{path}wind_speed_icon_ch2_{init}.npy')
wind_direction = np.load(f'{path}wind_direction_icon_ch2_{init}.npy')
radiation = np.load(f'{path}radiation_icon_ch2_{init}.npy')
cloudcover = np.load(f'{path}cloudcover_icon_ch2_{init}.npy')
percipitation = np.load(f'{path}percipitation_icon_ch2_{init}.npy')

# wind-direction
def wind_dir_str(grad):
    wd = ['N', 'NO', 'O', 'SO', 'S', 'SW', 'W', 'NW', 'N']
    return wd[int(0.5 + grad / 45)]


def wind_string(grad):
    wd = ['Nordwind', 'NO-Wind', 'Ostwind', 'SO-Wind', 'Südwind', 'SW-Wind', 'Westwind', 'NW-Wind', 'Nordwind']
    return wd[int(0.5 + grad / 45)]



# preparing a dictionary for thermal data and wind
def add_thermal(data_dict, height, thermals, clouds, wind, wind_deg):
    model_data = {
        "thermals":thermals,
        "clouds": clouds,
        "wind": wind,
        "wind_deg": wind_deg
        }
    data_dict.setdefault(height, model_data)
model_datas = {}

# preparing the JSON
def add_entry(data_dict, day, location, hour, sun, cloudcover, lift, base, wind, pfd, model_datas):
    # ensure integers
    day = int(day)
    location = int(location)
    hour = int(hour)

    # create a Dictionary from the parameters
    parameters = {
        "sun": str(sun),
        "cloudcover": str(cloudcover),
        "lift": str(lift),
        "base": str(base),
        "wind": str(wind),
        "potential": int(pfd),
        "model_data": model_datas,
    }

    # Add another set
    data_dict.setdefault(day, {}).setdefault(location, {})[hour] = parameters

# 1. Start with an empty dictionary
thermal_data = {}

loc = 0
level = 80
file_location = "emagrams/"

while fc_day < 5:    
    while loc < locations.max_locations:
    
        print(f"Day {fc_day}: Location {loc}: {locations.name_start[loc]}")

        lt_time = 9 + fc_day * 24
        while lt_time <= 20 + fc_day * 24:

            # here we start. We are in which level?
            level = 38
            while altitude[loc, level, lt_time] > locations.start_height[loc]:
                level += 1
            wind_start = int(wind_speed[loc, level, lt_time])
            wind_dir_start = wind_direction[loc, level, lt_time]
            wind_top = int(wind_speed[loc, level-5, lt_time])
            wind_high = int(wind_speed[loc, level-10, lt_time])
            wind_dir_high = wind_direction[loc-10, level, lt_time]

            sun = round(radiation[loc,lt_time]/800 * 100) # radiation in % of possible maximum
            cch = int (cloudcover[loc,lt_time] / 100)
            ccm = int ((cloudcover[loc,lt_time] % 100) / 10)
            ccl = int ((cloudcover[loc,lt_time] % 10) / 1)
            cc = f'{ccl}-{ccm}-{cch}'


            # here comes the call of the thermal model
            model_result, best_lift, base = thermal_model_ch2.calculate_thermals(loc, lt_time, locations.start_height[loc], 
                                            locations.mountain_top[loc], 600, 0, 12, locations.terrains[loc])
            # calculate the PFD
            distance = 0
            if best_lift >= 1:  # root-function gets 1 with a base of 2'000 meters
                distance = int(distance + 4 * best_lift * locations.xc_potential[loc]
                            * pow(max((base - locations.flight_range_low[loc]), 0), 0.5) / 28.2)
            elif best_lift > 0.5:
                distance = distance + 1

            # write to the JSON
            add_entry(thermal_data, fc_day, loc, lt_time, sun, cc,     
                lift=str(best_lift),
                base=str(base),
                wind=str(wind_start) + " " + wind_dir_str(wind_dir_start),
                pfd = distance,
                model_datas=model_result,
            )
            lt_time += 1
        loc += 1
    loc = 0
    fc_day +=1
# save the .json :-)
with open(f"{file_location}thermal_forecast.json", "w", encoding="utf-8") as f:
    json.dump(thermal_data, f, indent=4, ensure_ascii=False)

print("JSON sucessfully exported!")
