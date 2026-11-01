#!/bin/bash
# 1. activate my virtual environment
source env/bin/activate
# 2. run the python scipt 6 times
for i in {1..6}
do
    echo "run fetch-icon no. $i of 6..."
    python3 fetch_icon_raspi.py
    echo "I'm waiting for 8 seconds to cool down..."
    sleep 8
done

echo "ready :-)"