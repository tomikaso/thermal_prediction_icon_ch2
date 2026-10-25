import numpy as np
import locations

leadtime = 24

temperature = np.load(f'temperature_icon_ch2_{leadtime}.npy')
altitude = np.load(f'altitude_icon_ch2_{leadtime}.npy')
dewpoint = np.load(f'dewpoint_icon_ch2_{leadtime}.npy')
wind_speed = np.load(f'wind_speed_icon_ch2_{leadtime}.npy')
wind_direction = np.load(f'wind_direction_icon_ch2_{leadtime}.npy')

loc = 0
level = 80
file_location = "emagrams/"
def thermal_visualisation(temp):
    data = [(-100, 'Inversion', 'thistle'), (-0.1, 'isotherm', 'PowderBlue'), (0.1, 'sehr stabil', 'paleturquoise'),
            (0.3, 'stabil', 'lightcyan'), (0.5, 'eher stabil', 'azure'), (0.6, 'etwas labil', 'palegreen'),
            (0.7, 'labil', 'greenyellow'), (0.8, 'sehr labil', 'chartreuse'), (1, 'hyperlabil', 'yellowgreen')]
    ic = 0
    cont = 'unknown'
    color = 'white'
    while ic < 9:
        if temp >= data[ic][0]:
            cont = data[ic][1]
            color = data[ic][2]
        ic = ic + 1
    return cont, color
# SVG-Basics
width = 600
height = 600
border = 50
t_dist = 150
ty = height - 2 * border

while loc < locations.max_locations:
    level = 80
    print(f"Location {loc}: {locations.name_start[loc]}")
    SVG = f'<svg width="{width}" height="{height}" style="background-color:ivory" xmlns="http://www.w3.org/2000/svg">'
    # initialize the bottem values
    t0 = temperature[loc, level, 0]
    h0 = altitude[loc, level, 0]
    hmax = altitude[loc, 38, 0]
    d0 = dewpoint[loc, level, 0]
    h00 = altitude[loc, 80, 0]
    hd = hmax - h00
    # fix scale: for negative temperatures 1, then 0 for low positive and +1 if hot. Mean of 1500m and 3000m
    offset = - int((temperature[loc, 50, 0] + temperature[loc, 66, 0]) / 20)
    print(f"Location {loc}: offset = {offset}, hmax = {hmax}, h00 = {h00}, hd = {hd}")
    SVG = f'<svg width="{width}" height="{height}" style="background-color:ivory" xmlns="http://www.w3.org/2000/svg">'
    SVG += f'<text x="{border}" y="{16}" fill="dimgrey" font-size="12">{locations.name_start[loc]}</text>'
    # initialize the bottem values
    t0 = temperature[loc, level, 0]
    h0 = altitude[loc, level, 0]
    hmax = altitude[loc, 38, 0]
    d0 = dewpoint[loc, level, 0]
    h00 = altitude[loc, 80, 0]
    hd = hmax - h00
    # fix scale: for negative temperatures 1, then 0 for low positive and +1 if hot. Mean of 1500m and 3000m
    offset = - int((temperature[loc, 50, 0] + temperature[loc, 66, 0]) / 20)
    print(f"Location {loc}: offset = {offset}, hmax = {hmax}, h00 = {h00}, hd = {hd}")

    # draw the backgroung prior to the lines
    while level > 38:
        level -= 1
        t1 = temperature[loc, level, 0]
        h1 = altitude[loc, level, 0]
        temp = (t1 - t0) / (h1 - h0) * 100
        # Temperature line in red
        x0 = border + t_dist * t0 * 0.1 + (h0 - h00) / hd * ty + t_dist * offset
        x1 = border + t_dist * t1 * 0.1 + (h1 - h00) / hd * ty + t_dist * offset
        y0 = height - border - (h0-h00) / hd * ty
        y1 = height - border - (h1-h00) / hd * ty
        # Draw the background rectangle color depends of the temperature gradient
        fill_color = thermal_visualisation(-temp)[1]
        SVG += f'<rect x="{border}" y="{y1}" fill="{fill_color}" stroke="{fill_color}" width="{ty}" height="{y0-y1}" />'
        t0 = t1
        h0 = h1
    level = 80
    t0 = temperature[loc, level, 0]
    h0 = altitude[loc, level, 0]
    # draw the lines for temperature and dewpoint
    while level > 38:
        level -= 1
        t1 = temperature[loc, level, 0]
        d1 = dewpoint[loc, level, 0]
        h1 = altitude[loc, level, 0]
        temp = (t1 - t0) / (h1 - h0) * 100

        print(f"height: {h1:.1f}, wind_speed {wind_speed[loc, level, 0]:.1f} wind_dir: {wind_direction[loc, level, 0]:.1f}")

        # Temperature line in red
        x0 = border + t_dist * t0 * 0.1 + (h0 - h00) / hd * ty + t_dist * offset
        x1 = border + t_dist * t1 * 0.1 + (h1 - h00) / hd * ty + t_dist * offset
        y0 = height - border - (h0-h00) / hd * ty
        y1 = height - border - (h1-h00) / hd * ty
        # Draw the temperature line in red
        SVG += f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="red" stroke-width="3"/>'
        # Dewpoint line in blue
        x0=max(border, border + t_dist * d0 * 0.1 + (h0 - h00) / hd * ty + t_dist * offset)
        x1=max(border, border + t_dist * d1 * 0.1 + (h1 - h00) / hd * ty + t_dist * offset)
        y0 = height - border - (h0-h00) / hd * ty
        y1 = height - border - (h1-h00) / hd * ty
        SVG += f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="blue" stroke-width="3"/>'

        t0 = t1
        h0 = h1
        d0 = d1
    i = 0
    while i < 6:
        x = 10
        y = border + (hmax - i * 1000) / hd * ty
        text = str(i * 1000)
        SVG += f'<text x="{x}" y="{y}" fill="dimgrey" font-size="12">{text}</text>'
        if i < 4:
            x0 = border + t_dist * i
            y0 = height - border
            x1 = height - border
            y1 = border + t_dist * i 
            SVG += f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="lightgrey" stroke-width="1"/>'  # lines from the bottom
            if i > 0:
                x0 = border
                y0 = height - border - t_dist * i
                x1 = height - border - t_dist * i
                y1 = border
                SVG += f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="lightgrey" stroke-width="1"/>'  # lines from left
            x = border + t_dist * i
            y = height - border + 20
            text = str((i - offset) * 10)
            SVG += f'<text x="{x}" y="{y}" fill="dimgrey" font-size="12">{text}</text>'
            if i < 3:
                x = border + 60 + t_dist * i
                y = border - 12
                text = str((i - offset - 3) * 10)
                SVG += f'<text x="{x}" y="{y}" fill="dimgrey" font-size="12">{text}</text>'
        i = i + 1
    SVG += '</svg>'
    SVG_file = open(f"{file_location}emagram_loc{loc:02d}_{leadtime:02d}.svg", "w")
    SVG_file.write(SVG)
    SVG_file.close()
    loc += 1

