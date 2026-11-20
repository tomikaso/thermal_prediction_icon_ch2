#!/bin/bash
# 1. activate my virtual environment
source /home/meteoman/icon_ch2/.venv/bin/activate
# 2. run the python scipt 6 times
for i in {1..5}
do
    echo "run fetch-icon no. $i of 5..."
    python3 /home/meteoman/icon_ch2/fetch_icon_raspi.py
    echo "I'm waiting for 8 seconds to cool down..."
    sleep 8
done
echo "all data fetched"
python3 /home/meteoman/icon_ch2/draw_emagrams.py
echo "emagrams plotted"
sleep 8
python3 /home/meteoman/icon_ch2/draw_thermal_rows.py
echo "thermals calculated"
sleep 8
python3 /home/meteoman/icon_ch2/file_transfer_dczo.py
echo "everything sent to DCZO, ready :-)"