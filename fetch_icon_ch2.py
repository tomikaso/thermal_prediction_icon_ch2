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

leadtime = 24 # tomorrow

# required data is Temperature
forecast = ekd.from_source(
    "meteoswiss-opendata",
    collection="ogd-forecasting-icon-ch2",
    variable="T",
    perturbed=False,
    ref_time="latest",
    lead_time=[
        dt.timedelta(hours=leadtime)
    ],
)

dataset = forecast.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
print(dataset)

# required data is QV absolute humidity
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

    distanz = (dataset["latitude"] - ziel_lat)**2 + (dataset["longitude"] - ziel_lon)**2
    # 2. find the index (values-ID) of the nearest grid point
    next_index = distanz.argmin().item()

    level = 1
    while level <= 80:
        desired_level: int = level
        # 3. extraxt the value over the correct dimensions ('level' and 'values')
        abs_temp = dataset["t"].sel(
            level=desired_level,
            values=next_index)
        temperature[loc, level, 0] = abs_temp.values.item() - 273.15
        height = ds_hhl_ch2["h"].sel(
                level=desired_level,
                values=next_index)
        specific_humidity = dataset_qv["q"].sel(
            level=desired_level,
            values=next_index)
        dew_point = calculate_dew_point(temperature[loc, level, 0], specific_humidity.values.item(), height.values.item())
        dewpoint[loc, level, 0] = dew_point
        altitude[loc, level, 0] = height.values.item()
        temp_celsius = abs_temp.values.item() - 273.15
        # test code: print(f"Temperatur {loc} Level {desired_level}, {height.values.item()}: {temp_celsius:.2f} °C, Dew Point: {dew_point:.2f} °C")
        level += 1
    loc = loc + 1

# printing results
print(f"saving temperature, altitude and dewpoint to numpy arrays")
np.save(f"temperature_icon_ch2_{leadtime}.npy", temperature)
np.save(f"altitude_icon_ch2_{leadtime}.npy", altitude)
np.save(f"dewpoint_icon_ch2_{leadtime}.npy", dewpoint)
