#!/usr/bin/python
#
# Python script to convert serial traffic to MQTT and vice versa.
# Stephen Gray 2017/04/15
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

##############Configuration##############
#MQTT settings
broker="192.168.1.190"
port=1883
#Serial port settings
serialdev='/dev/ttyAMA0'
baud=19200
#########################################

#MQTT callbacks
#the callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code "+str(rc))
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
    if len(list1)==3 and list1[2]<>"1":
        sendstr=(list1[2]+":"+msg.payload)
#        print "Send string: "+ sendstr
    	ser.write(sendstr)

def on_publish(client, userdata, mid):
#    print "Published ", mid
    pass

#called on program exit
def cleanup():
    print "Ending and cleaning up"
	#Close Serial
    ser.close()
	#Disconnect from MQTT
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)

#connect to serial port
try:
    print "Connecting to serial device", serialdev
    ser = serial.Serial(
        port=serialdev,
        baudrate=baud,
        parity=serial.PARITY_NONE,
#        stopbits=serial.STOPBITS_ONE,
#        timeout=0.5
)
except:
    print "Failed to open serial port"
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
    mqttc.connect(broker, port, 60)
    #start background thread to monitor MQTT. Recieved messages will be handled by on_message function
    mqttc.loop_start()

    #main program loop: read serial and publish
    while 1:
        serialreadline=ser.readline()
        items=serialreadline.split(",")
#        print(serialreadline)
        #Format of serial line is:
        #<sending_node_number>,<topic>:<payload>,<topic>:<payload>, etc, <RSSI>:<value>,ACK:<sent or not>
        try:
            nodenum=items[0]
            #crash out of the try if the first item is not a number
            int(nodenum)
#            print "From node number: "+nodenum
            for item in items[1:]:
                if ":" in item:
                    data=item.split(":")
                    #first element is topic, second is payload
                    topic="sensors/</"+nodenum+"/"+data[0]
                    mqttc.publish(topic, data[1])
#                    print("topic: "+topic+", Data: "+data[1])
        except Exception,e:
#            print "Error parsing data: " + str(e)
            pass
except KeyboardInterrupt:
    cleanup()
except RuntimeError:
    cleanup()
