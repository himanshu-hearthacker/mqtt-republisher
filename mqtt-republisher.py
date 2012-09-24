#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

__author__ = "Kyle Gordon"
__copyright__ = "Copyright (C) Kyle Gordon"

import mosquitto
import os
import time
import csv
import logging

MQTT_HOST="localhost"
MQTT_PORT=1883
MQTT_TOPIC="/raw/#"
MAPFILE='/etc/mqtt-republisher/map.csv'
LOGFILE='/var/log/mqtt-republisher.log'
DEBUG=1

mypid = os.getpid()
client_uniq = "Republisher_"+str(mypid)
mqttc = mosquitto.Mosquitto(client_uniq)

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

if DEBUG == 0: logging.basicConfig(filename=LOGFILE,level=logging.INFO)
if DEBUG == 1: logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)

logging.info('Starting mqtt-republisher')
logging.info('INFO MODE')
logging.debug('DEBUG MODE')

def cleanup():
    logging.info("Disconnecting from broker")
    mqttc.disconnect()

# Turn the mapping file into a dictionary for internal use
# Valid from Python 2.7.1 onwards
with open(MAPFILE, mode='r') as inputfile:
    reader = csv.reader(inputfile)
    mydict = dict((rows[0],rows[1]) for rows in reader)

#define what happens after connection
def on_connect(rc):
	logging.info("Connected to broker")

#On recipt of a message print it
def on_message(msg):
	logging.debug("Received: " + msg.topic)
	# print "Received", msg.topic, msg.payload
	if msg.topic in mydict:
		## Found an item. Replace it with one from the dictionary
		# print "Replacing " + msg.topic + " with " + mydict[msg.topic]
		mqttc.publish(mydict[msg.topic], msg.payload)
		logging.debug("Republishing: " + msg.topic + " -> " + mydict[msg.topic])
	else:
		# Recieved something with a /raw/ topic, but it didn't match. Push it out with /unsorted/ prepended
		mqttc.publish("/unsorted" + msg.topic, msg.payload)
		logging.debug("Unknown: " + msg.topic)

try:
	#connect to broker
	mqttc.connect(MQTT_HOST, MQTT_PORT, 60, True)

	#define the callbacks
	mqttc.on_message = on_message
	mqttc.on_connect = on_connect

	mqttc.subscribe(MQTT_TOPIC, 2)

	#remain connected and publish
	while mqttc.loop() == 0:
		try:
			logging.info("Looping")
			pass
		except (KeyboardInterrupt):
			logging.info("Keyboard interrupt received")
			cleanup()
		except (RuntimeError):
			logging.info("Program crashed")
			cleanup()

except (KeyboardInterrupt):
    logging.info("Keyboard interrupt received")
    cleanup()
except (RuntimeError):
    logging.info("Program crashed")
    cleanup()
