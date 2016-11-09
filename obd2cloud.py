#!/usr/bin/env python

import sys
import httplib

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import getpass

import socket
import ssl

from obd_utils import scanSerial

PRODUCT_ID = "y7o6tu5q115opqfr"
SERIAL_NUM = "als7061"
SHOW_HTTP_REQUESTS = False

#gpsSer = serial.Serial('/dev/ttyUSB0', 4800, timeout=None)

class FakeSocket:
    def __init__(self, response_str):
        if PYTHON == 2:
            self._file = StringIO(response_str)
        else:
            self._file = BytesIO(response_str)

    def makefile(self, *args, **kwargs):
        return self._file

try:
    from StringIO import StringIO
    import httplib
    input = raw_input
    PYTHON = 2
except ImportError:
    from http import client as httplib
    from io import StringIO, BytesIO

    PYTHON = 3 


class FakeSocket:
    def __init__(self, response_str):
        if PYTHON == 2:
            self._file = StringIO(response_str)
        else:
            self._file = BytesIO(response_str)

    def makefile(self, *args, **kwargs):
        return self._file


def SOCKET_SEND(http_packet, host_address, https_port):
    # SEND REQUEST
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_s = ssl.wrap_socket(s)
    ssl_s.connect((host_address, https_port))
    if SHOW_HTTP_REQUESTS:
        print("--- Sending ---\r\n {} \r\n----".format(http_packet))
    if PYTHON == 2:
        ssl_s.send(http_packet)
    else:
        ssl_s.send(bytes(http_packet, 'UTF-8'))
    # GET RESPONSE
    response = ssl_s.recv(1024)
    ssl_s.close()
    if SHOW_HTTP_REQUESTS:
        print("--- Response --- \r\n {} \r\n---")

    # PARSE REPONSE
    fake_socket_response = FakeSocket(response)
    parsed_response = httplib.HTTPResponse(fake_socket_response)
    parsed_response.begin()
    return parsed_response

def ACTIVATE(productid, identifier):
    try:
        # print("attempt to activate on Murano")
        host_address = productid+".m2.exosite.com"

        http_body = 'vendor=' + productid + '&model=' + productid + '&sn=' + identifier
        # BUILD HTTP PACKET
        http_packet = ""
        http_packet += 'POST /provision/activate HTTP/1.1\r\n'
        http_packet += 'Host: ' + host_address + '\r\n'
        http_packet += 'Connection: Close \r\n'
        http_packet += 'Content-Type: application/x-www-form-urlencoded; charset=utf-8\r\n'
        http_packet += 'content-length:' + str(len(http_body)) + '\r\n'
        http_packet += '\r\n'
        http_packet += http_body

        response = SOCKET_SEND(http_packet, host_address, 443)

        # HANDLE POSSIBLE RESPONSES
        if response.status == 200:
            new_cik = response.read().decode("utf-8")
            print("Activation Response: New CIK: {} ..............................".format(new_cik[0:10]))
            return new_cik
        elif response.status == 409:
            print("Activation Response: Device Aleady Activated, there is no new CIK")
        elif response.status == 404:
            print("Activation Response: Device Identity ({}) activation not available or check Product Id ({})".format(
                identifier,
                productid
                ))
        else:
            print("Activation Response: failed request: {} {}".format(str(response.status), response.reason))
            return None

    except Exception as e:
        # pass
        print("Exception: {}".format(e))
    return None


def GET_STORED_CIK(productid, identifier):
    print("get stored CIK from non-volatile memory")
    try:
        f = open(productid + "_" + identifier + "_cik", "r+")  # opens file to store CIK
        local_cik = f.read()
        f.close()
        print("Stored cik: {} ..............................".format(local_cik[0:10]))
        return local_cik
    except Exception as e:
        print("Unable to read a stored CIK: {}".format(e))
        return None


def STORE_CIK(cik_to_store, productid, identifier):
    print("storing new CIK to non-volatile memory")
    f = open(productid + "_" + identifier + "_cik", "w")  # opens file that stores CIK
    f.write(cik_to_store)
    f.close()
    return True


def WRITE(WRITE_PARAMS, productid, identifier):
    # print "write data to Murano"
    host_address = productid+".m2.exosite.com"

    http_body = WRITE_PARAMS
    # BUILD HTTP PACKET
    http_packet = ""
    http_packet += 'POST /onep:v1/stack/alias HTTP/1.1\r\n'
    http_packet += 'Host: ' + host_address + '\r\n'
    http_packet += 'X-EXOSITE-CIK: ' + cik + '\r\n'
    http_packet += 'Connection: Close \r\n'
    http_packet += 'Content-Type: application/x-www-form-urlencoded; charset=utf-8\r\n'
    http_packet += 'content-length:' + str(len(http_body)) + '\r\n'
    http_packet += '\r\n'
    http_packet += http_body

    response = SOCKET_SEND(http_packet, host_address, 443)

    # HANDLE POSSIBLE RESPONSES
    if response.status == 204:
        # print "write success"
        return True, 204
    elif response.status == 401:
        print("401: Bad Auth, CIK may be bad")
        return False, 401
    elif response.status == 400:
        print("400: Bad Request: check syntax")
        return False, 400
    elif response.status == 405:
        print("405: Bad Method")
        return False, 405
    else:
        print(str(response.status), response.reason, 'failed:')
        return False, response.status

    # This code is unreachable and should be removed
    # 		except Exception as err:
    # pass
    # print("exception: {}".format(str(err)))


    # return None

def READ(READ_PARAMS, productid, identifier):
    try:
        # print("read data from Murano")
        host_address = productid+".m2.exosite.com"

        # BUILD HTTP PACKET
        http_packet = ""
        http_packet += 'GET /onep:v1/stack/alias?' + READ_PARAMS + ' HTTP/1.1\r\n'
        http_packet += 'Host: ' + host_address + '\r\n'
        http_packet += 'X-EXOSITE-CIK: ' + cik + '\r\n'
        # http_packet += 'Connection: Close \r\n'
        http_packet += 'Accept: application/x-www-form-urlencoded; charset=utf-8\r\n'
        http_packet += '\r\n'

        response = SOCKET_SEND(http_packet, host_address, 443)

        # HANDLE POSSIBLE RESPONSES
        if response.status == 200:
            # print "read success"
            return True, response.read().decode('utf-8')
        elif response.status == 401:
            print("401: Bad Auth, CIK may be bad")
            return False, 401
        elif response.status == 400:
            print("400: Bad Request: check syntax")
            return False, 400
        elif response.status == 405:
            print("405: Bad Method")
            return False, 405
        else:
            print(str(response.status), response.reason, 'failed:')
            return False, response.status

    except Exception as e:
        # pass
        print("Exception: {}".format(e))
    return False, 'function exception'


def LONG_POLL_WAIT(READ_PARAMS, productid, identifier):

    host_address = productid+".m2.exosite.com"
    try:
        # print "long poll state wait request from Murano"
        # BUILD HTTP PACKET
        http_packet = ""
        http_packet += 'GET /onep:v1/stack/alias?' + READ_PARAMS + ' HTTP/1.1\r\n'
        http_packet += 'Host: ' + host_address + '\r\n'
        http_packet += 'Accept: application/x-www-form-urlencoded; charset=utf-8\r\n'
        http_packet += 'X-EXOSITE-CIK: ' + cik + '\r\n'
        http_packet += 'Request-Timeout: ' + str(LONG_POLL_REQUEST_TIMEOUT) + '\r\n'
        if last_modified.get(READ_PARAMS) != None:
            http_packet += 'If-Modified-Since: ' + last_modified.get(READ_PARAMS) + '\r\n'
        http_packet += '\r\n'

        response = SOCKET_SEND(http_packet, host_address, 443)

        # HANDLE POSSIBLE RESPONSES
        if response.status == 200:
            # print "read success"
            if response.getheader("last-modified") != None:
                # Save Last-Modified Header (Plus 1s)
                lm = response.getheader("last-modified")
                next_lm = (datetime.datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S GMT") + datetime.timedelta(seconds=1)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                last_modified[READ_PARAMS] = next_lm
            return True, response.read()
        elif response.status == 304:
            # print "304: No Change"
            return False, 304
        elif response.status == 401:
            print("401: Bad Auth, CIK may be bad")
            return False, 401
        elif response.status == 400:
            print("400: Bad Request: check syntax")
            return False, 400
        elif response.status == 405:
            print("405: Bad Method")
            return False, 405
        else:
            print(str(response.status), response.reason)
            return False, response.status

    except Exception as e:
        pass
        print("Exception: {}".format(e))
    return False, 'function exception'

class Obd2Cloud():
    def __init__(self, logItems, cik):
        self.port = None
        self.sensorlist = []
        self.cik = cik

        for item in logItems:
            self.addLogItem(item)

    def connect(self):
        portnames = scanSerial()
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

        writeData = ""
        isFirst = True;
        for index in self.sensorlist:
            (name, value, unit) = self.port.sensor(index)
            if not isFirst:
                writeData += "&"
            
            isFirst = False;
            writeData += obd_sensors.SENSORS[index].shortname + "=" + str(value)

        gpsSer = serial.Serial('/dev/ttyUSB0', 4800, timeout=None)
        gpsData = gpsSer.readline()
	if gpsData[1:6] != "GPGGA":
            gpsData = "NODATA"

        writeData += "&gps="+gpsData
        gpsSer.close()

        print "Send " + writeData
        WRITE(writeData, PRODUCT_ID, SERIAL_NUM) 

cik = GET_STORED_CIK(PRODUCT_ID, SERIAL_NUM);
logItems = ["rpm", "speed", "maf", "throttle_pos", "ecu_volt", "amb_temp", "acc_pedal_pos_d", "engine_fuel_rate", "load", "fuel_air_comm_equ_rat", "rel_acc_pedal_pos"]

o = Obd2Cloud(logItems, cik)

o.connect()

if not o.isConnected():
    print "Not connected"

while 1:
    o.sendDataToCloud();
    time.sleep(1)
