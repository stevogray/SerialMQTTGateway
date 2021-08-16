#!/usr/bin/python
#
# Python script to convert serial traffic to MQTT and vice versa.
# Stephen Gray 2017/04/15
# David deMarco 2017/07/9 - Updated to Python 3.5 and added logging
# SG 2019/06/15 Encode serial writes
# SG 2019/07/03 Strip newlines from topic and payload
# SG 2021/08/16 Add MQTT connection error codes. Change logging levels
#
# Serial data arrives as comma delimited in the following form (comma delimited, colons separate MQTT topic and message):
# {sending_node_number},{topic}:{message},{topic}:{message}
# eg: 5,Temperature:20.6,Battery:LOW
# using the topic and message from the serial read, the MQTT topics are updated:
# sensors/</[sending_node_number]/{topic} {message}
# eg from above:
# Topic: sensors/</5/Temperature Message: 20.6
# Topic: sensors/</5/Battery     Message: LOW
#
# MQTT topic sensors/>/# is subscribed to. MQTT Topics should be:
# sensors/>/{nodeid} {message}      or
# sensors/>/{nodeid}/{topic} {message}
# Any new data is sent to serial as:
# <{nodeid}:{topic}:{message}>
# eg Topic: sensors/>/5/LED Message:ON would be sent to serial as:
# <5:LED:ON>
# Which the attached arduino broadcasts over the wireless network. The code in the arduino should look for the start marker "<" and the end marker ">".
# Any message destined for node 1 (the gateway ardunio) is written to serial without sending node.
#
# Developed for use with Moteinos https://lowpowerlab.com/guide/moteino/ using a modified 
# gateway sketch (to format serial data as comma delimited).
#
# Primary functionality from Python MQTT client from Eclipse Paho http://www.eclipse.org/paho/
# Paho documentation at https://pypi.python.org/pypi/paho-mqtt/1.1

import paho.mqtt.client as mqtt
import serial
import sys
import SerialGatewaySettings as s
import logging
import logging.handlers

##############Configuration##############
#Settings are in the settings.py file so that different setting can exist between the development platform and the Pi Gatway.
#########################################


##############Logging Settings##############
#Added a logging routine so when the gateway is run as a process on the PI you can see what is going on.
#Set the logging level in the settings file.

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL (read from settings file)
logger.setLevel(s.LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(s.LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)
#########################################

logger.critical('Starting Pi/Moteino Gateway')
logger.info("Log level: "+ s.LOG_LEVEL)

def error(code):
    errorlist = {
        -1: "Socket Error",
        0: "Successful Connect",
        1: "Unsupported MQTT version",
        2: "Client ID rejected",
        3: "Server unavailable",
        4: "Invalid username/password",
        5: "Not authorized",
        }
    return errorlist.get(code, "Unknown error")

#MQTT callbacks
#the callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0: 
        logger.info("Connected to MQTT broker with result: "+ error(rc))
    else:
        logger.error("Connected to MQTT broker with result: "+ error(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("sensors/>/#")

#the callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #A message has been posted to sensors/>/#.
	#If node number is 1, pass through msg.payload
    #If topic has a fourth level, add this to the serial string
    list1=msg.topic.split("/")
    msg.payload = msg.payload.decode("utf-8")

    if len(list1)==3 and list1[2]=="1":
        sendstr=("<"+msg.payload+">")
        ser.write(sendstr.encode())
        logger.info("Send serial to gateway: "+ sendstr)
    elif len(list1)==3:
        sendstr=("<"+list1[2]+":"+msg.payload+">")
        logger.info("Send serial: "+ sendstr)
        ser.write(sendstr.encode())
    elif len(list1)==4:
        sendstr=("<"+list1[2]+":"+list1[3]+":"+msg.payload+">")
        logger.info("Send serial: "+ sendstr)
        ser.write(sendstr.encode())

def on_publish(client, userdata, mid):
    pass

#called on program exit
def cleanup():
    logger.info("Ending and cleaning up")
    #Close Serial
    ser.close()
    #Disconnect from MQTT
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)

#connect to serial port
try:
    logger.info('Connecting to serial device %s', s.SERIALDEV)
    ser = serial.Serial(
        port=s.SERIALDEV,
        baudrate=s.BAUD,
        parity=serial.PARITY_NONE,
#        stopbits=serial.STOPBITS_ONE,
#        timeout=0.5
)
except:
    logger.critical("Failed to open serial port")
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
            if len(items)==1:
                logger.warning(serialreadline)
            else:
                nodenum=items[0]
                #crash out of the try if the first item is not a number
                int(nodenum)
                logger.debug("From node number: %s", nodenum)
                for item in items[1:]:
                    if ":" in item:
                        data=item.split(":")
                        #first element is topic, second is payload
                        topic="sensors/</"+nodenum+"/"+data[0].strip()
                        mqttc.publish(topic, data[1].strip())
                        logger.info("Received data: topic: %s Data: %s ", topic, data[1].strip())
        except Exception as e:
            logger.warning('Error parsing data %s',format(str(e)))
            pass
except KeyboardInterrupt:
    cleanup()
except RuntimeError:
    cleanup()
