import datetime as dt

import earthkit.data as ekd

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

# Ziel-Koordinaten und gewünschtes Level
ziel_lat = 47.289
ziel_lon = 8.915

distanz = (dataset["latitude"] - ziel_lat)**2 + (dataset["longitude"] - ziel_lon)**2
# 2. Finde den Index (values-ID) des nächstgelegenen Gitterpunkts
naechster_index = distanz.argmin().item()

level = 1
while level <= 80:
    gewuenschtes_level = level
    # 3. Extrahiere den Wert über die korrekten Dimensionen ('level' und 'values')
    spezifischer_wert = dataset["t"].sel(
        level=gewuenschtes_level,
        values=naechster_index)
    temp_celsius = spezifischer_wert.values.item() - 273.15
    height = ds_hhl_ch2["h"].sel(
            level=gewuenschtes_level,
            values=naechster_index)
    h_m = height.values.item()
    print(f"Temperatur Wald ZH Level {gewuenschtes_level}: {spezifischer_wert.values.item():.2f} K ({temp_celsius:.2f} °C)")

    print(f"Level {gewuenschtes_level}: HHL = {h_m:.2f} m")
    level += 1