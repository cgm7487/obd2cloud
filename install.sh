#!/bin/sh

sudo cp run-obd2 /etc/init.d
cd /etc/init.d
sudo update-rc.d run-obd2 defaults

exit 0 
