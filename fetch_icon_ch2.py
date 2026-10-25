import datetime as dt
import earthkit.data as ekd
import numpy as np
import math
import locations

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
temperature = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps
altitude = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps
dewpoint = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps
wind_speed = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps
wind_direction = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps

leadtime = 20 # tomorrow
while leadtime < 25:
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
    print(dataset_t)
    
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
    print(dataset_qv)

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
    print(dataset_u)

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
    print(dataset_v)
    
    
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
    
    print(f"Vertical Levels Object:", ds_hhl_ch2)
    
    # loop through all locations and extract the temperature and altitude for each level
    loc = 0
    while loc < number_of_locations:
        ziel_lat = locations.coordinates[loc][0]
        ziel_lon = locations.coordinates[loc][1]
    
        distanz = (dataset_t["latitude"] - ziel_lat)**2 + (dataset_t["longitude"] - ziel_lon)**2
        # 2. find the index (values-ID) of the nearest grid point
        next_index = distanz.argmin().item()
    
        level = 1
        while level <= 80:
            desired_level: int = level
            # 3. extraxt the value over the correct dimensions ('level' and 'values')
            abs_temp = dataset_t["t"].sel(
                level=desired_level,
                values=next_index)
            temperature[loc, level, 0] = abs_temp.values.item() - 273.15
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
            dew_point = calculate_dew_point(temperature[loc, level, 0], specific_humidity.values.item(), height.values.item())
            dewpoint[loc, level, 0] = dew_point
            altitude[loc, level, 0] = height.values.item()
            temp_celsius = abs_temp.values.item() - 273.15
            wind_speed[loc, level, 0] = math.sqrt(u_wind.values.item() ** 2 + v_wind.values.item() ** 2) * 3.6  # km/h
            wind_direction[loc, level, 0] = (math.atan2(u_wind.values.item(), v_wind.values.item()) * 180 / math.pi + 180 ) % 360
            # test code: print(f"Temperatur {loc} Level {desired_level}, {height.values.item()}: {temp_celsius:.2f} °C, Dew Point: {dew_point:.2f} °C")
            level += 1
        loc = loc + 1
    # printing results
    print(f"Leadtime: {leadtime}, saving temperature, altitude and dewpoint to numpy arrays")
    np.save(f"temperature_icon_ch2_{leadtime}.npy", temperature)
    np.save(f"altitude_icon_ch2_{leadtime}.npy", altitude)
    np.save(f"dewpoint_icon_ch2_{leadtime}.npy", dewpoint)
    np.save(f"wind_speed_icon_ch2_{leadtime}.npy", wind_speed)
    np.save(f"wind_direction_icon_ch2_{leadtime}.npy", wind_direction)
    leadtime = leadtime +1
print(f"Process successfully finished")