#!/bin/bash

resultcode=1
hidval=0
while [ $resultcode -ne  0 ] && [ $hidval -lt 5 ]
do
    echo trying /dev/hidraw$hidval...
    python3 glucometer.py --driver=fslibre --device=/dev/hidraw$hidval dump --to-file --with-ketone --output-folder Libre
    resultcode=$?
    if (( hidval==0 ))
    then
        let hidval=4
    else 
        let hidval=hidval+1
    fi
done



