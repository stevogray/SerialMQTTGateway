#!/usr/bin/python
#
# Python script to convert serial traffic to MQTT and vice versa.
# Stephen Gray 2017/04/15
# David deMarco 2017/07/9 - Updated to Python 3.5 and added logging
#
# Serial data arrives as comma delimited in the following form (comma delimited, colons separate MQTT topic and message):
# <sending_node_number>,<topic>:<message>,<topic>:<message>
# using the topic and message from the serial read, the MQTT topics are updated:
# sensors/</<sending_node_number><topic> <message>
#
# MQTT topic sensors/>/# is subscribed to. MQTT Topics should be:
# sensors/>/<nodeid> <message>
# Any new data is sent to serial as:
# <nodeid>:<message>
# Which the attached arduino broadcasts over the wireless network.
# Anything destined for node 1 (the gateway ardunio) is written to serial without sending mode. 
#
# Developed for use with Moteinos https://lowpowerlab.com/guide/moteino/ using a slightly modified 
# gateway sketch (to format serial data as comma delimited).
#
# Primary functionality from Python MQTT client from Eclipse Paho http://www.eclipse.org/paho/
# Paho documentation at https://pypi.python.org/pypi/paho-mqtt/1.1

import paho.mqtt.client as mqtt
import serial
import sys
import settings as s
import logging
import logging.handlers

##############Configuration##############
#Settings have been moved to the settings.py file so that different setting can exist between the development platform
#and the Pi Gatway.
#########################################


##############Logging Settings##############
#Added a logging routine so when the gateway is run as a process on the PI you can see what is going on.  Main change you
#you might want to make is the logging level.

# Change the above to .DEBUG for message infomation and .INFO for runtime minimal messages
logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

# Change this to as well.  Not entirely sure which one is controlling this.  Sorry!
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"


# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(s.LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)
#########################################

LOGGER.info('Starting up Pi/Moteino Gateway')

#MQTT callbacks
#the callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    LOGGER.info("Connected to MQTT broker with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("sensors/>/#")

#the callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #A message has been posted to sensors/>/#.
	#If node number is 1, pass through msg.payload
    list1=msg.topic.split("/")
    if len(list1)==3 and list1[2]=="1":
        ser.write(msg.payload)
    if len(list1)==3 and list1[2]!="1":
        sendstr=(list1[2]+":"+msg.payload)
        LOGGER.info ("Send string: "+ sendstr)
        ser.write(sendstr)

def on_publish(client, userdata, mid):
#    print "Published ", mid
    pass

#called on program exit
def cleanup():
    LOGGER.info("Ending and cleaning up")
    #Close Serial
    ser.close()
    #Disconnect from MQTT
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)

#connect to serial port
try:
    LOGGER.info('Connecting to serial device %s', s.SERIALDEV)
    ser = serial.Serial(
        port=s.SERIALDEV,
        baudrate=s.BAUD,
        parity=serial.PARITY_NONE,
#        stopbits=serial.STOPBITS_ONE,
#        timeout=0.5
)
except:
    LOGGER.info("Failed to open serial port")
    sys.exit(-1)

#connect to MQTT and main program loop
try:
    ser.flushInput()
    #create MQTT client
    mqttc=mqtt.Client()

    #attach MQTT callbacks
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_publish = on_publish
    #connect to broker (blocking function, callback when successful, callback subscribes to topics)
    mqttc.connect(s.BROKER, s.PORT, 60)
    #start background thread to monitor MQTT. Recieved messages will be handled by on_message function
    mqttc.loop_start()

    #main program loop: read serial and publish
    while 1:
        serialreadline=ser.readline()
        logger.debug(serialreadline)
        items=serialreadline.decode().split(",")

        #Format of serial line is:
        #<sending_node_number>,<topic>:<payload>,<topic>:<payload>, etc, <RSSI>:<value>,ACK:<sent or not>
        try:
            nodenum=items[0]
            #crash out of the try if the first item is not a number
            int(nodenum)
            logger.debug("From node number: %s", nodenum)
            for item in items[1:]:
                if ":" in item:
                    data=item.split(":")
                    #first element is topic, second is payload
                    topic="sensors/</"+nodenum+"/"+data[0]
                    mqttc.publish(topic, data[1])
                    logger.info('topic: %s Data: %s ', topic, data[1])
        except Exception as e:
            logger.info('Error parsing data %s',format(str(e)))
            pass
except KeyboardInterrupt:
    cleanup()
except RuntimeError:
    cleanup()
