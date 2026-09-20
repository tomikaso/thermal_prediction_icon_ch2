import datetime as dt
import earthkit.data as ekd
import numpy as np

number_of_locations = 14
locations = ['Scheidegg', 'Locarno', 'Hüsliberg', 'Pany', 'Solothurn', 'Scuol', 'Fiesch', 'Niesen',
             'Braunwald-Gumen', 'Cari', 'Ebenalp', 'Galgenen', 'Zugerberg', 'Engelberg']
coordinates = np.array([[47.289, 8.915], [46.175384, 8.793927], [47.181896, 9.051195], [46.927030, 9.771950],
                        [47.233629, 7.497267], [46.798445, 10.299627], [46.404585, 8.13389], [46.617260, 7.671066],
                        [46.927241, 9.001098], [46.511744, 8.820113], [47.279408, 9.419929], [47.175256, 8.880510],
                        [47.162343, 8.516407], [46.821780, 8.406177]])
# define temperature
temperature = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps
altitude = np.full((number_of_locations, 81, 12), 0.00) # 81 levels, 14 locations, 12 time steps

# required data is Temperature, Dewpoint and vertical Levels (HHL)
forecast = ekd.from_source(
    "meteoswiss-opendata",
    collection="ogd-forecasting-icon-ch2",
    variable="T",
    perturbed=False,
    ref_time="latest",
    lead_time=[
        dt.timedelta(hours=1)
    ],
)

dataset = forecast.to_xarray(time_dims=["forecast_reference_time", "step"], squeeze=False)
print(dataset)

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

for loc in locations:
    ziel_lat = coordinates[locations.index(loc)][0]
    ziel_lon = coordinates[locations.index(loc)][1]

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
        temperature[locations.index(loc), level, 0] = abs_temp.values.item() - 273.15
        height = ds_hhl_ch2["h"].sel(
                level=desired_level,
                values=next_index)
        altitude[locations.index(loc), level, 0] = height.values.item()
        temp_celsius = abs_temp.values.item() - 273.15
        print(f"Temperatur {loc} Level {desired_level}: {abs_temp.values.item():.2f} K ({temp_celsius:.2f} °C)")
        level += 1
print(f"Temperature Array: {temperature}")
np.save('temperature_icon_ch2.npy', temperature)
np.save('altitude_icon_ch2.npy', altitude)
