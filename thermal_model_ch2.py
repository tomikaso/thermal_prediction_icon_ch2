# thermal model to simulate a rising air parcel in the given atmosphere.
import numpy as np
import locations
import math
from datetime import datetime
import time

# settig thermodynamic parameters
updraft_factor = 48
dry_adiabatic = 0.979
moisture_adiabatic = 0.562
mixing_dry = 0.1
mixing_wet = 0.10
std_pressure = 101325

# calculate density
def density(pressure, temp, humi):
    Rda = 287.058  # R dry air
    Rva = 461.51  # R vapor
    Pp_sat = 611 * math.exp(17.62 * temp / (243.12 + temp))
    Rma = Rda / (1 - (humi * (Pp_sat / pressure)) * (1 - Rda / Rva))  # R moisturized air
    return pressure / Rma / (temp + 273.15)

# calculate pressure, depending on the altitude
def alt2pres(altitude):
    return 100 * ((44331.514 - altitude) / 11880.516) ** (1 / 0.1902632)

# relative humidity
def rh_from_tdew(temp_air, temp_dew):
    # Calculate vapor pressure (e) and saturation vapor pressure (es)
    e = 6.112 * 2.718281 ** ((17.62 * temp_air) / (243.12 + temp_air))
    es = 6.112 * 2.718281 ** ((17.62 * temp_dew) / (243.12 + temp_dew))
    return es / e

# Loading ICON Data
temperature = np.load('temperature_icon_ch2.npy')
altitude = np.load('altitude_icon_ch2.npy')
dewpoint = np.load('dewpoint_icon_ch2.npy')


# here the model begins
def calculate_thermals( loc, start_height, mountain_top, radiation, precipitation, time_hr, terrain):
    ground_level = 400
    parcel_temperature = [-100] * 81
    parcel_dewpoint = [-100] * 81
    condensation = ['no'] * 80
    parcel_density = [0] * 80
    air_density = [0] * 80
    parcel_updraft = [0] * 80
    calculation_base = max(ground_level, start_height - 400)
    condensed = 0
    updraft = 0
    # more variables
    best_lift = 0
    base_top = 0
    html_string = []
    # astro parameters for alpine starting places.
    latitude = 47.255
    date = datetime.now()
    post_winter_solstice = date.month * 30 + date.day - 20
    if post_winter_solstice >= 360:
        post_winter_solstice = post_winter_solstice - 360
    # calculate the position of the sun
    maxdeclination = 90 - latitude - 23.5 * math.cos(post_winter_solstice / 360 * 6.28)
    if time.localtime().tm_isdst > 0:  # adjust midday to daylight saving time
        midday = 13.5
    else:
        midday = 12.5
    daylength = 12.2 - 3.74 * math.cos(post_winter_solstice / 360 * 6.28)
    delta_zenit = (midday - time_hr) * 12 / daylength
    sun_angle = max(math.asin(math.sin(math.radians(maxdeclination))
                              * math.cos(math.radians(delta_zenit * 15))) * 180 / math.pi, 0)
    rad90 = radiation / math.sin(max(math.radians(sun_angle), 0.1))
    print('time: ', time_hr, ' sun angle: ', sun_angle, ' post winter solstice:', post_winter_solstice,
          ' max decl. ', maxdeclination, ' Terrain: ', terrain, ' radiation:', radiation, ' 90-deg:', rad90)

    # calculate the distribution of sun in the valley and in the mountains from the declination of the sun
    if terrain == 'alpine':
        rad_effective = math.sin(math.radians(sun_angle + 40)) * rad90  # 40° steepness
    elif terrain == 'pre-alpine':
        rad_effective = math.sin(math.radians(sun_angle + 20)) * rad90  # 20° steepness
    else:
        rad_effective = 0  # hotplate case

    # Setting of the loop variables
    level = 80 # the calcalation starts at 80, the lowest level of the ICON model
    print(f"Location {loc}: {locations.name_start[loc]}")
    # initialize the bottem values
    t0 = temperature[loc, level, 0]
    h0 = altitude[loc, level, 0]
    i = max (math.ceil(h0 / 200) * 200, 800)
    j = 800
    while j < i: # prefill string with green svg
        html_string.append(str(j) + ',Green')
        j = j + 200

    # Loop over all levels beginning from 80 down to 39   
    while level > 38:
        level -= 1
        t1 = temperature[loc, level, 0]
        h1 = altitude[loc, level, 0]
        thickness = h1 - h0
        temp = (t1 - t0) / thickness * 100
        
        # init Parcel
        if h1 < calculation_base: # below the start, ambient atmospheric values are taken over
            parcel_temperature[level] = t1
            parcel_dewpoint[level] = dewpoint[loc, level, 0]
        else:
            factor = max(1, 2 - updraft) * thickness / 100 # the weaker the updraft, the more mixes ambient air into the parcel
            if t1 > parcel_dewpoint[level] + 0.5: # no condensation case
                if h1 <= mountain_top:  # add some energy as long as the peaks of the mountains are reached
                    parcel_temperature[level] = (parcel_temperature[level + 1] - dry_adiabatic * thickness / 100
                                                 + std_pressure / alt2pres(h1) * rad_effective / 3300 * thickness / 100)
                else:
                    parcel_temperature[level] = ((parcel_temperature[level + 1] - dry_adiabatic * thickness / 100)
                                                 * (1 - mixing_dry * factor) + mixing_dry * factor * t1)

                parcel_dewpoint[level] = (parcel_dewpoint[level + 1] * (1 - mixing_dry * thickness / 100 * factor)
                                            + mixing_dry * thickness / 100 * factor * dewpoint[loc, level, 0])
                condensation[level] = 'no'

            else: #condensation case
                condensation[level] = 'yes'
                parcel_temperature[level] = ((parcel_temperature[level + 1] - moisture_adiabatic * thickness / 100)
                                             * (1 - mixing_wet * factor) + mixing_wet * factor * t1)

                parcel_dewpoint[level] = (parcel_dewpoint[level + 1] * (1 - mixing_wet * factor)
                                          + mixing_wet * factor * dewpoint[loc, level, 0])
        #  density of the air parcel
        parcel_density = density(alt2pres(h1), parcel_temperature[level], rh_from_tdew(parcel_temperature[level], parcel_dewpoint[level]))
        #  density of the ambient air
        air_density = density(alt2pres(h1),t1, rh_from_tdew(t1, dewpoint[loc, level, 0]))
        #  updraft
        updraft = max(0, (updraft_factor * max(air_density - parcel_density, 0) ** 0.6))
        parcel_updraft[level] = updraft
            

        # Test printout of data
        print(f"Level {level}: {h1:.0f} m, Temp {t1:.1f} °C, Dewpt {dewpoint[loc, level, 0]:.1f} °C, "
              f"Temp: {temp:.1f} K/100 m, Parcel_t {parcel_temperature[level]:.1f}°C, Parcel_dp {parcel_dewpoint[level]:.1f}°C "
              f"Cond= {condensation[level]}, updraft: {updraft:.1f}")

        if h0 <= i <= h1 and i <= 4000:  # one data point each 200 meters until 4'000 meters
            if i <= calculation_base:
                html_string.append(str(i) + ',Green')
            else:
                if condensation[level] == 'yes':
                    if precipitation > 10:
                        if t1 >= 0:
                            html_string.append(str(i) + ',cloud_flash')
                        else:
                            html_string.append(str(i) + ',cloud_flash_snow')
                    elif precipitation > 2:
                        if t1 >= 0:
                            html_string.append(str(i) + ',cloud_rain2')
                        else:
                            html_string.append(str(i) + ',cloud_snow2')
                    elif precipitation > 0:
                        if t1 >= 0:
                            html_string.append(str(i) + ',cloud_rain1')
                        else:
                            html_string.append(str(i) + ',cloud_snow1')
                    elif updraft > 0:
                        html_string.append(str(i) + ',cloud_cumulus')
                    condensed = 1
                elif condensed == 0 and updraft > 0:
                    html_string.append(str(i) + ',' + str(round(updraft, 1)))
            i = i + 200


        # best lift and base / top
        if i > start_height and updraft > 0.5 and condensed == 0:
            best_lift = round(max(updraft, best_lift), 1)
            base_top = i


    
        # prepare for the next level
        t0 = t1
        h0 = h1
        
    return html_string
