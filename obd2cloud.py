#!/usr/bin/env python

import sys
import httplib

#import pyonep
#from pyonep.provision import Provision
#from pyonep.onep import OneV1
#from pyonep.exceptions import ProvisionException
from pyonep import onep

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import getpass

from obd_utils import scanSerial

class Obd2Cloud():
	def __init__(self, logItems, cik):
		self.port = None
		self.sensorlist = []
		self.cik = cik

		for item in logItems:
			self.addLogItem(item)

	def connect(self):
		portnames = scanSerial()
		print protnames
		for port in portnames:
			self.port = obd_io.OBDPort(port, None, 2, 2)
			if(self.port.State == 0):
				self.port.close()
				self.port = None
			else:
				break

		if(self.port):
			print "Connected to " + self.port.port.name

	def isConnected(self):
		return self.port

	def addLogItem(self, item):
		for index, e in enumerate(obd_sensors.SENSORS):
			if(item == e.shortname):
				self.sensorlist.append(index)
				print "Logging item: " + e.name
				break

	def sendDataToCloud(self):
		if(self.port is None):
			return None

		print "start sending to cloud"

		o = onep.OnepV1()
		while 1:
			for index in self.sensorlist:
				(name, value, unit) = self.port.sensor(index)
				#results[obd_sensors.SENSORS[index].shortname] = value

				print "Send " + obd_sensors.SENSORS[index].shortname + " = " + value
				o.write(self.cik,
						{"alias": obd_sensors.SENSORS[index].shortname},
						value,
						{})
CIK = 'b7e588466225dde46de44b0017072b2ccb39a4a0' #for test
logItems = ["rpm", "speed", "load", "fuel_status"]
o = Obd2Cloud(logItems, CIK)

if not o.isConnected():
	print "Not connected"

o.sendDataToCloud();
