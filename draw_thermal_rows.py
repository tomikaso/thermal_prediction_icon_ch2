import numpy as np
import locations
import json
import math

fc_day = 0
init = "20261101"
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

loc = 0
level = 80
file_location = "emagrams/"


# SVG-Basics
width = 450
height = 600
border = 50
t_dist = 150
ty = height - 2 * border
tx = width - 2 * border
line_height = (height - 2 * border) / 18

while loc < locations.max_locations:
   
    print(f"Location {loc}: {locations.name_start[loc]}")
    SVG = f'<svg width="{width}" height="{height}" style="background-color:ivory" xmlns="http://www.w3.org/2000/svg">'
    
    # initialize the headline
    fill_color = "gainsboro"
    SVG += f'<rect x="0" y="{border}" fill="{fill_color}" stroke="{fill_color}" width="{width-border}" height="{line_height}" />'
    text = "Zeit         Wind        Sonne       Wolken       Temp       Lift       Base/Top"
    SVG += f'<text x="10" y="{border + 12}" fill="black" font-family="sans-serif" font-size="12" font-weight="bold" word-spacing="10px">{text}</text>'
    text = " LT          km/h                  l-m-h           K/100m       m/s         m"
    SVG += f'<text x="10" y="{border + 24}" fill="black" font-family="sans-serif" font-size="12" font-weight="bold" word-spacing="20px">{text}</text>'

    lt_time = 10
    while lt_time <= 20:
        if lt_time % 2 == 0:
            fill_color = "cornsilk"
        else:
            fill_color = "mintcream"
        SVG += f'<rect x="0" y="{border + line_height * (lt_time - 9)}" fill="{fill_color}" stroke="{fill_color}" width="{width-border}" height="{line_height}" />'
        SVG += f'<text x="10" y="{border + 18 + line_height * (lt_time - 9)}" fill="black" font-family="sans-serif" font-size="12">{lt_time}:00</text>'
        
        
        
        lt_time += 1
    
    SVG += '</svg>'
    SVG_file = open(f"{file_location}summary_loc{loc:02d}_day{fc_day:02d}.svg", "w")
    SVG_file.write(SVG)
    SVG_file.close()
    loc += 1

