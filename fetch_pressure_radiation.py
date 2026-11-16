import datetime as dt
from zoneinfo import ZoneInfo
import earthkit.data as ekd
import numpy as np
import locations
from pathlib import Path

sytem_path = '/home/meteoman/icon_ch2/'
# sytem_path = ''  # activate for WSL


# basic parameters
path = sytem_path + "data/"
load_hour = 0
leadtime = 0
number_of_locations = locations.max_locations
new_day_flag = False
local_tz = ZoneInfo("Europe/Zurich")
start_time = dt.datetime.now(local_tz)
start_date = start_time.strftime("%Y%m%d")
utc_offset = int(start_time.utcoffset().total_seconds() / 3600)
start_hour = ((start_time.hour - 3 ) // 6) * 6 
print(f'Starting load at: {start_time}')
z_time = "latest"
# z_time = "2026-11-15T00:00:00Z"
start_hour = 0

# is there already data for this date?

radiation = np.full((number_of_locations, 140), 0.00, dtype=np.float32) # surface, 14 locations, 120 time steps
pressure = np.full((number_of_locations, 140), 0.00, dtype=np.float32) # surface, 14 locations, 120 time steps
new_day_flag = True

# calculating the leadtimes
leadtime = 0
print(f'Start hour: z{start_hour}, leadtime: {leadtime}')
leadtime_original = leadtime

# sums of sunshine radiation for each location
radiation_old_sum = [0] * locations.max_locations

while leadtime + utc_offset < 120:  

    # Downward direct short wave radiation flux at surface (mean over forecast time)
    forecast_r = ekd.from_source(
            "meteoswiss-opendata",
            collection="ogd-forecasting-icon-ch2",
            variable="ASOB_S",
            perturbed=False,
            ref_time=z_time,
            lead_time=[
                dt.timedelta(hours=leadtime)
            ],
        )
        
    dataset_r = forecast_r.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    init_time = dataset_r["forecast_reference_time"].values
    print(f'Init Time Radiation: {init_time}, Leadtime: {leadtime}')

    # pressure reduced to sea level
    forecast_pressure = ekd.from_source(
                    "meteoswiss-opendata",
                    collection="ogd-forecasting-icon-ch2",
                    variable="PMSL",
                    perturbed=False,
                    ref_time=z_time,
                    lead_time=[
                        dt.timedelta(hours=leadtime)
                    ],
                )
                
    dataset_pressure = forecast_pressure.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
    init_time = dataset_pressure["forecast_reference_time"].values
    print(f'pressure to sea level: {init_time}, Leadtime: {leadtime}')
        
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
    
        distanz = (dataset_r["latitude"] - ziel_lat)**2 + (dataset_r["longitude"] - ziel_lon)**2
        # 2. find the index (values-ID) of the nearest grid point
        # next_index = distanz.argmin().item()
        next_index = int(np.argmin(distanz.data))

        # Measures without levels
        rad = dataset_r["avg_snswrf"].sel(values=next_index)
        accumulated_rad = rad.values.item() * leadtime  # the total sum of energy in the model run
        radiation[loc, leadtime + load_hour + utc_offset] = accumulated_rad - radiation_old_sum[loc]
        radiation_old_sum[loc] = accumulated_rad # store the pre-hour value
                
        # pressure at sea level
        press = dataset_pressure["prmsl"].sel(values=next_index)
        pressure[loc, leadtime + load_hour + utc_offset] = press.values.item() / 100 # hPa

        now = dt.datetime.now()
        print(f'Next Objects at: {now}')
        loc = loc + 1
    # printing results
    print(f"Leadtime: {leadtime}, z{load_hour}saving pressure and radiation to numpy arrays")
    leadtime = leadtime +1

# everything worked well, write out results

np.save(f"{path}radiation_icon_ch2_{start_date}.npy", radiation)
np.save(f"{path}pressure_icon_ch2_{start_date}.npy", pressure)
print(f"Process successfully finished")