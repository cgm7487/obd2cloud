# Goal
Create an application to send car's obd2 data to the cloud.
This application will be created based on pyobd-py and pyonep projects. 

#Auto-start setting
copy run-obd2 to /etc/init.d/
sudo update-rc.d run-obd2 defaults

if you want to remove auto-start:
sudo update-rc.d -f run-obd2 remove


