import constants
import locations
import ftplib

system_path = '/home/meteoman/icon_ch2/'
file_location = system_path + 'emagrams/'

# send it to DCZO-webserver
session = ftplib.FTP('ftp.dczo.ch', constants.ftp_user, constants.ftp_pw)
file = open(f'{file_location}thermal_forecast.json', 'rb')  # the main file to send
session.storbinary(f'STOR icon_ch2/thermal_forecast.json', file)  # send the file
print ('JSON sent :-)')
lt_time = 9
loc = 0
while lt_time <= 20:
    while loc < locations.max_locations:
        print("sending: ", locations.name_start[loc])
        file0 = open(f'{file_location}emagram_loc{loc:02d}_d0lt{(lt_time):02d}.svg', 'rb')  # file to send
        file1 = open(f'{file_location}emagram_loc{loc:02d}_d1lt{(lt_time):02d}.svg', 'rb')  # file to send
        file2 = open(f'{file_location}emagram_loc{loc:02d}_d2lt{(lt_time):02d}.svg', 'rb')  # file to send
        file3 = open(f'{file_location}emagram_loc{loc:02d}_d3lt{(lt_time):02d}.svg', 'rb')  # file to send
        file4 = open(f'{file_location}emagram_loc{loc:02d}_d4lt{(lt_time):02d}.svg', 'rb')  # file to send
        session.storbinary(f'STOR icon_ch2/emagram_loc{loc:02d}_d0lt{(lt_time):02d}.svg', file0)  # send the file
        session.storbinary(f'STOR icon_ch2/emagram_loc{loc:02d}_d1lt{(lt_time):02d}.svg', file1)  # send the file
        session.storbinary(f'STOR icon_ch2/emagram_loc{loc:02d}_d2lt{(lt_time):02d}.svg', file2)  # send the file
        session.storbinary(f'STOR icon_ch2/emagram_loc{loc:02d}_d3lt{(lt_time):02d}.svg', file3)  # send the file
        session.storbinary(f'STOR icon_ch2/emagram_loc{loc:02d}_d4lt{(lt_time):02d}.svg', file4)  # send the file
        loc = loc + 1
    print('Sent all emagrams for local Time: ', lt_time)
    loc = 0
    lt_time +=1
print("Everything sent :-)")