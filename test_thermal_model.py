import thermal_model_ch2
import locations
loc = 0
while loc < locations.max_locations:
    html_string = thermal_model_ch2.calculate_thermals(loc, locations.start_height[loc], locations.mountain_top[loc],
                                                       600, 0, 12, locations.terrains[loc])
    print('Result for :', locations.name_start[loc] , ' -> ',html_string)
    loc += 1
