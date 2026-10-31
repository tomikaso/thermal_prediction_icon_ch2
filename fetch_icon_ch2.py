import datetime as dt
from zoneinfo import ZoneInfo
import earthkit.data as ekd
import numpy as np
import math
import locations
import gc

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

number_of_locations = locations.max_locations

# define temperature
temperature = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
altitude = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
dewpoint = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
wind_speed = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
wind_direction = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
wind_u = np.full((number_of_locations, 81, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps
radiation = np.full((number_of_locations, 120), 0.00, dtype=np.float32) # 81 levels, 14 locations, 120 time steps

local_tz = ZoneInfo("Europe/Zurich")
start_time = dt.datetime.now(local_tz)
utc_offset = start_time.utcoffset()
start_date = start_time.strftime("%Y%m%d")
start_hour = ((start_time.hour - 3 ) // 6) * 6  
if start_hour < 6: # we begin with the corrent day
    target_date = dt.date.today().isoformat()
    leadtime = int(8 + start_time.utcoffset() / 3600)
    z00_reference_time = f"{target_date}T00:00:00Z"
else:
    leadtime = int(24 - start_hour + 8 + utc_offset.total_seconds() / 3600)
print(f'Start hour: z{start_hour}, leadtime: {leadtime}')

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

dimensions = 5
var1 = ["T", "QV","U", "V", "ASOD_S" ]

leadtime_max = leadtime + 10
while leadtime < leadtime_max:
    dim = 0
    while dim < dimensions:
        # required data is Temperature
        forecast = ekd.from_source(
            "meteoswiss-opendata",
            collection="ogd-forecasting-icon-ch2",
            variable=var1[dim], 
            perturbed=False,
            ref_time="latest",
            lead_time=[
                dt.timedelta(hours=leadtime)
            ],
        )
    
        dataset = forecast.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
        load_hour = int(dataset["forecast_reference_time"].dt.hour[0].values) # 0, 6, 12, 18
        print(f'Dataset {var1[dim]}: ', dataset)
        init_time = dataset["forecast_reference_time"].values
        
    
    # loop through all locations and extract the temperature and altitude for each level
        loc = 0
        while loc < number_of_locations:
            ziel_lat = locations.coordinates[loc][0]
            ziel_lon = locations.coordinates[loc][1]

            distanz = (dataset["latitude"] - ziel_lat)**2 + (dataset["longitude"] - ziel_lon)**2
            # 2. find the index (values-ID) of the nearest grid point
            next_index = distanz.argmin().item()

            # Measures without levels
            if var1[dim] == "ASOD_S":
                radiation_w = dataset["avg_sdswrf"].sel(values=next_index)
                radiation[loc, leadtime + load_hour] = radiation_w.values.item()

            level = 1
            while level <= 80:
                desired_level: int = level
                # 3. extraxt the value over the correct dimensions ('level' and 'values')
                if var1[dim] == "T":
                    abs_temp = dataset["t"].sel(
                        level=desired_level,
                        values=next_index)
                    temperature[loc, level, leadtime + load_hour] = abs_temp.values.item() - 273.15

                if var1[dim] == "QV": # calculate Humidity and Altitude in one clause, as altitude is needed for spec humidity.
                    specific_humidity = dataset["q"].sel(
                        level=desired_level,
                        values=next_index)
                    height = ds_hhl_ch2["h"].sel(
                        level=desired_level,
                        values=next_index)
                    dew_point = calculate_dew_point(temperature[loc, level, 0], specific_humidity.values.item(), height.values.item())
                    dewpoint[loc, level, leadtime + load_hour] = dew_point
                    altitude[loc, level, leadtime + load_hour] = height.values.item()
                if var1[dim] == "U":
                    u_wind = dataset["u"].sel(
                        level=desired_level,
                        values=next_index)
                    wind_u[loc, level, leadtime + load_hour] = u_wind.values.item()
                if var1[dim] == "V": # Wind vertical and the calculation of wind_speed and wind direction
                    v_wind = dataset["v"].sel(
                        level=desired_level,
                        values=next_index)
                    wind_speed[loc, level, leadtime + load_hour] = math.sqrt(wind_u[loc, level, leadtime + load_hour] ** 2 + v_wind.values.item() ** 2) * 3.6  # km/h
                    wind_direction[loc, level, leadtime + load_hour] = (math.atan2(wind_u[loc, level, leadtime + load_hour], v_wind.values.item()) * 180 / math.pi + 180 ) % 360
                
                # test code: print(f"Temperatur {loc} Level {desired_level}, {height.values.item()}: {temp_celsius:.2f} °C, Dew Point: {dew_point:.2f} °C")
                level += 1
            x = dt.datetime.now()
            loc = loc + 1
        # printing results
        print(f"Leadtime: {leadtime}, z{load_hour}, dim {var1[dim]}. Now calling the next dimension")

        # cleaning up
        dataset.close()
        del dataset
        del forecast
        gc.collect()

        # get the next dimension
        dim = dim + 1
    # get the next our
    leadtime = leadtime +1
np.save(f"temperature_icon_ch2_{start_date}.npy", temperature)
np.save(f"altitude_icon_ch2_{start_date}.npy", altitude)
np.save(f"dewpoint_icon_ch2_{start_date}.npy", dewpoint)
np.save(f"wind_speed_icon_ch2_{start_date}.npy", wind_speed)
np.save(f"wind_direction_icon_ch2_{start_date}.npy", wind_direction)
np.save(f"radiation_icon_ch2_{start_date}.npy", radiation)
print(f"Process successfully finished")