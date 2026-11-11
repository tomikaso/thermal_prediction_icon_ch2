import numpy as np
import locations
import json
import math

fc_day = 0
init = "20261109"
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

# preparing the JSON
def add_entry(data_dict, day, location, hour, sun, cloudcover, lift, base, wind, pot):
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
        "potential": int(pot),
    }

    # Add another set
    data_dict.setdefault(day, {}).setdefault(location, {})[hour] = parameters

# 1. Start with an empty dictionary
thermal_data = {}


# html definitions
style = '<style> html {font-family: "brandon-grotesque-n7","brandon-grotesque", sans-serif; font-size: 10pt; ' \
         'background: #eef6fa; color: #4f5a80; } table, td, th, a, p {font-size: 10pt; padding: 4pt;} ' \
         'tr { background-color: aliceblue;} tr:not(:first-child):hover {background-color: skyblue;} ' \
         '.new{background-color: cornsilk;} a:link {color: darkred; text-decoration: none;} ' \
         '.layout-container {display: flex; align-items: center; justify-content: center; gap: 20px;'\
         ' margin: 50px auto; max-width: 1000px;}' \
         '</style>'
script = '<script>function show_ema(n) {document.getElementById("ema-svg").src = `emagram_loc04_d1lt${n}.svg`;}</script>'
loc = 0
level = 80
file_location = "emagrams/"


while loc < locations.max_locations:
   
    print(f"Location {loc}: {locations.name_start[loc]}")
    # Table basics
    ema_svg = f"emagram_loc{loc:02d}_d{fc_day:01d}lt10.svg"
    svg = f'<div class="layout-container"><img id="ema-svg" src="{ema_svg}">'
    print(ema_svg)
    html_string = style + svg + '<table style="width:550px"><tr><th>Zeit<br>LT</th><th>Wind<br>km/h</th><th>Sonne<br>%</th>\
        <th>Wolken<br>l-m-h</th><th>Lift<br>m/s</th><th>Base/Top<br>m</th></tr>'
    lt_time = 10
    while lt_time <= 20:
        sun = round(radiation[loc,lt_time]/800 * 100) # radiation in % of possible maximum
        cch = int (cloudcover[loc,lt_time] / 100)
        ccm = int ((cloudcover[loc,lt_time] % 100) / 10)
        ccl = int ((cloudcover[loc,lt_time] % 10) / 1)
        cc = f'{ccl}-{ccm}-{cch}'
        if lt_time % 2 == 0:
            fill_color = "cornsilk"
        else:
            fill_color = "mintcream"

        ema_svg = f"emagram_loc{loc:02d}_d{fc_day:01d}lt{lt_time:2d}.svg"
        html_string += f'<tr onmouseover="show_ema({lt_time})"><td>{lt_time:2d}:00</td><td></td><td>{sun}</td><td>{cc}</td><td></td><td></td></tr>'
        
        # write to the JSON
        add_entry(thermal_data, fc_day, loc, lt_time, sun, cc,     
            lift="2.0",
            base="2100",
            wind="12 W",
            pot = loc,
        )
        lt_time += 1
    
    html_string += '</table></div>' + script
    html_file = open(f"{file_location}summary_loc{loc:02d}_day{fc_day:01d}.html", "w")
    html_file.write(html_string)
    html_file.close()
    loc += 1
# save the .json :-)
with open(f"{file_location}thermal_forecast.json", "w", encoding="utf-8") as f:
    json.dump(thermal_data, f, indent=4, ensure_ascii=False)

print("JSON sucessfully exported!")
