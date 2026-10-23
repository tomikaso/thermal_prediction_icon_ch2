import numpy as np
temperature = np.load('temperature_icon_ch2.npy')
altitude = np.load('altitude_icon_ch2.npy')
dewpoint = np.load('dewpoint_icon_ch2.npy')

loc = 0
level = 80

# SVG-Basics
width = 600
height = 600
border = 50
t_dist = 150
offset = 1
ty = height - 2 * border
SVG = f'<svg width="{width}" height="{height}" style="background-color:ivory" xmlns="http://www.w3.org/2000/svg">'
# initialize the bottem values
t0 = temperature[loc, level, 0]
h0 = altitude[loc, level, 0]
hmax = altitude[loc, 40, 0]
d0 = dewpoint[loc, level, 0]
hd = hmax - h0

# prepare canvas with an rectangle and a border
SVG += f'<rect x="{border}" y="{border}" fill="cornsilk" width="{width - 2 * border}" height="{height - 2 * border}" />'

print(f"Location Scheidegg {loc}:")
while level >= 40:
    level -= 1
    t1 = temperature[loc, level, 0]
    d1 = dewpoint[loc, level, 0]
    h1 = altitude[loc, level, 0]
    temp = (t1 - t0) / (h1 - h0) * 100
    # Temperature line in red
    x0=border + t_dist * t0 * 0.1 + h0 / hmax + t_dist * offset
    x1=border + t_dist * t1 * 0.1 + h1 / hmax + t_dist * offset
    y0 = border + (hmax - h0) / hd * ty
    y1 = border + (hmax - h1) / hd * ty
    SVG += f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="red" stroke-width="3"/>'

    # Dewpoint line in blue
    x0=max(border, border + t_dist * d0 * 0.1 + h0 / hmax + t_dist * offset)
    x1=max(border, border + t_dist * d1 * 0.1 + h1 / hmax + t_dist * offset)
    y0 = border + (hmax - h0) / hd * ty
    y1 = border + (hmax - h1) / hd * ty
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
SVG_file = open("temperature_profile.svg", "w")
SVG_file.write(SVG)
SVG_file.close()   

