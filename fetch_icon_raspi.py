import datetime as dt
from zoneinfo import ZoneInfo
import earthkit.data as ekd
import numpy as np
import math
import locations
import json
from pathlib import Path

def calculate_dew_point(T_celsius, q, h):
    # calculate the pressure in hPa
    P_hpa = 1013.25 * (1 - 0.0000225577 * h)**5.25588
    
    # 1. convert specific humidity (q) in the mixing ratio (r)
    r = q / (1.0 - q)
    
    # 2. calculate steam pressure (e) in hPa
    e = (r * P_hpa) / (0.622 + r)
    
    # check if e is less than or equal to zero to avoid math domain error
    if e <= 0:
        return float('-inf')
    # 3. calculate dew point (Td) with the Magnus formula
    alpha = math.log(e / 6.112)
    Td = (243.12 * alpha) / (17.62 - alpha)
    return Td

with open("load_status.json", "r") as file:
    loaded_data = json.load(file)
print(f"Last Leadtime: {loaded_data["leadtime"]}")
leadtime_original = loaded_data["leadtime"]
if (leadtime_original + loaded_data["model_run"]) % 24 >= 20: # jump to the next day
    leadtime_original = leadtime_original + 24

# basic parameters
path = "data/"
load_hour = 0
leadtime = 0
number_of_locations = locations.max_locations
new_day_flag = False
local_tz = ZoneInfo("Europe/Zurich")
start_time = dt.datetime.now(local_tz)
start_date = start_time.strftime("%Y%m%d")
local_tz = ZoneInfo("Europe/Zurich")
utc_offset = int(start_time.utcoffset().total_seconds() / 3600)
start_date = start_time.strftime("%Y%m%d")
start_hour = ((start_time.hour - 3 ) // 6) * 6 
print(f'Starting load at: {start_time}')

# is there already data for this date?
datei_pfad = Path(f"{path}temperature_icon_ch2_{start_date}.npy")
if datei_pfad.is_file():
    temperature = np.load(f"{path}temperature_icon_ch2_{start_date}.npy")
    altitude = np.load(f"{path}altitude_icon_ch2_{start_date}.npy")
    dewpoint = np.load(f"{path}dewpoint_icon_ch2_{start_date}.npy")
    wind_speed = np.load(f"{path}wind_speed_icon_ch2_{start_date}.npy")
    wind_direction = np.load(f"{path}wind_direction_icon_ch2_{start_date}.npy")
    radiation = np.load(f"{path}radiation_icon_ch2_{start_date}.npy")
    leadtime = leadtime_original # we are in an ongoing load
else:
    # define temperature
    temperature = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    altitude = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    dewpoint = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    wind_speed = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    wind_direction = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    radiation = np.full((number_of_locations, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
    new_day_flag = True

    # calculating the leadtimes
    if start_hour < 12: # we begin with the corrent day for z00 and z06
        leadtime = 9 - utc_offset - start_hour
    else:
        leadtime = 9 - utc_offset - start_hour + 24
    print(f'Start hour: z{start_hour}, leadtime: {leadtime}')
    leadtime_original = leadtime


while leadtime < leadtime_original + 2:
# required data is Temperature
    forecast_t = ekd.from_source(
        "meteoswiss-opendata",
        collection="ogd-forecasting-icon-ch2",
        variable="T",
        perturbed=False,
        ref_time="latest",
        lead_time=[
            dt.timedelta(hours=leadtime)
        ],
    )
    
    dataset_t = forecast_t.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    print('Dataset T: ', dataset_t)
    init_time = dataset_t["forecast_reference_time"].values
    print(f'Init Time Dataset Temperature: {init_time}')
    
    # required data is QV absolute humidity [kg/kg]
    forecast_qv = ekd.from_source(
        "meteoswiss-opendata",
        collection="ogd-forecasting-icon-ch2",
        variable="QV",
        perturbed=False,
        ref_time="latest",
        lead_time=[
            dt.timedelta(hours=leadtime)
        ],
    )
    
    dataset_qv = forecast_qv.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    init_time = dataset_t["forecast_reference_time"].values
    print(f'Init Time Dataset humidity: {init_time}, Leadtime: {leadtime}')

    # dataset U for the U-component of the wind
    forecast_u = ekd.from_source(
        "meteoswiss-opendata",
        collection="ogd-forecasting-icon-ch2",
        variable="U",
        perturbed=False,
        ref_time="latest",
        lead_time=[
            dt.timedelta(hours=leadtime)
        ],
    )
    
    dataset_u = forecast_u.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    init_time = dataset_u["forecast_reference_time"].values
    print(f'Init Time Dataset U-Wind: {init_time}, Leadtime: {leadtime}')

    # dataset V for the V-component of the wind
    forecast_v = ekd.from_source(
        "meteoswiss-opendata",
        collection="ogd-forecasting-icon-ch2",
        variable="V",
        perturbed=False,
        ref_time="latest",
        lead_time=[
            dt.timedelta(hours=leadtime)
        ],
    )
    
    dataset_v = forecast_v.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    load_hour = int(dataset_v["forecast_reference_time"].dt.hour[0].values) # 0, 6, 12, 18
    print(f"Ladezeit: z{load_hour}")
    
    print(f'Init Time Dataset V-Wind: {init_time}, Leadtime: {leadtime}')

    # Downward direct short wave radiation flux at surface (mean over forecast time)
    forecast_r = ekd.from_source(
            "meteoswiss-opendata",
            collection="ogd-forecasting-icon-ch2",
            variable="ASOD_S",
            perturbed=False,
            ref_time="latest",
            lead_time=[
                dt.timedelta(hours=leadtime)
            ],
        )
        
    dataset_r = forecast_r.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    init_time = dataset_r["forecast_reference_time"].values
    print("My Radiation: ", dataset_r)
    print(f'Init Time Radiation: {init_time}, Leadtime: {leadtime}')
    
    # now get the vertical levels from the ICON-CH2 dataset
    vertical_ch2 = ekd.from_source(
        "meteoswiss-opendata-constants",
        collection="ogd-forecasting-icon-ch2",
        asset="vertical",
    )
    
    vertical_fl_ch2 = vertical_ch2.to_fieldlist()
    vertical_fl_ch2.ls()
    
    ds_hhl_ch2 = vertical_ch2.to_xarray(
        time_dims=["forecast_reference_time", "step"],
        squeeze=False
        )
    
    print(f"Vertical Levels Object:", leadtime)
    
    # loop through all locations and extract the temperature and altitude for each level
    loc = 0
    while loc < number_of_locations:
        ziel_lat = locations.coordinates[loc][0]
        ziel_lon = locations.coordinates[loc][1]
    
        distanz = (dataset_t["latitude"] - ziel_lat)**2 + (dataset_t["longitude"] - ziel_lon)**2
        # 2. find the index (values-ID) of the nearest grid point
        next_index = distanz.argmin().item()

        # Measures without levels
        radiation_w = dataset_r["avg_sdswrf"].sel(values=next_index)
        radiation[loc, leadtime + load_hour] = radiation_w.values.item()
    
        level = 1
        while level <= 80:
            desired_level: int = level
            # 3. extraxt the value over the correct dimensions ('level' and 'values')
            abs_temp = dataset_t["t"].sel(
                level=desired_level,
                values=next_index)
            temperature[loc, level, leadtime + load_hour + utc_offset] = abs_temp.values.item() - 273.15
            height = ds_hhl_ch2["h"].sel(
                    level=desired_level,
                    values=next_index)
            specific_humidity = dataset_qv["q"].sel(
                level=desired_level,
                values=next_index)
            u_wind = dataset_u["u"].sel(
                level=desired_level,
                values=next_index)
            v_wind = dataset_v["v"].sel(
                level=desired_level,
                values=next_index)
            dew_point = calculate_dew_point(temperature[loc, level, leadtime + load_hour + utc_offset], specific_humidity.values.item(), height.values.item())
            dewpoint[loc, level, leadtime + load_hour + utc_offset] = dew_point
            altitude[loc, level, leadtime + load_hour + utc_offset] = height.values.item()
            temp_celsius = abs_temp.values.item() - 273.15
            wind_speed[loc, level, leadtime + load_hour + utc_offset] = math.sqrt(u_wind.values.item() ** 2 + v_wind.values.item() ** 2) * 3.6  # km/h
            wind_direction[loc, level, leadtime + load_hour + utc_offset] = (math.atan2(u_wind.values.item(), v_wind.values.item()) * 180 / math.pi + 180 ) % 360
            # test code: print(f"Temperatur {loc} Level {desired_level}, {height.values.item()}: {temp_celsius:.2f} °C, Dew Point: {dew_point:.2f} °C")
            level += 1
        now = dt.datetime.now()
        print(f'Next Objects at: {now}')
        loc = loc + 1
    # printing results
    print(f"Leadtime: {leadtime}, z{load_hour}saving temperature, altitude and dewpoint to numpy arrays")
    leadtime = leadtime +1

# everything worked well, write out results
np.save(f"{path}temperature_icon_ch2_{start_date}.npy", temperature)
np.save(f"{path}altitude_icon_ch2_{start_date}.npy", altitude)
np.save(f"{path}dewpoint_icon_ch2_{start_date}.npy", dewpoint)
np.save(f"{path}wind_speed_icon_ch2_{start_date}.npy", wind_speed)
np.save(f"{path}wind_direction_icon_ch2_{start_date}.npy", wind_direction)
np.save(f"{path}radiation_icon_ch2_{start_date}.npy", radiation)

load_status = {
    "status": "ok",
    "leadtime": leadtime,
    "model_run": load_hour,
    "last_change": now.isoformat()
}
# write the dictionary to a file
with open("load_status.json", "w") as file:
    # indent=4 makes the file human-readable (pretty-printed)
    json.dump(load_status, file, indent=4)
print("leadtime successfully saved to disk as JSON!")
print(f"Process successfully finished")