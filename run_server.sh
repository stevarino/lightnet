#!/bin/bash

source /home/pi/lightnet/env/bin/activate
hciconfig hci0 piscan
python /home/pi/lightnet/rfcomm-server.py
