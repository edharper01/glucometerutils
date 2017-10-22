#!/bin/bash

resultcode=1
hidval=0
while [ $resultcode -ne  0 ] && [ $hidval -lt 10 ]
do
    echo trying /dev/hidraw$hidval...
    python3 glucometer.py --driver=fslibre --device=/dev/hidraw$hidval dump
    resultcode=$?
    let hidval=hidval+1
done



