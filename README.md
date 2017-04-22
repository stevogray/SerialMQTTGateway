# SerialMQTTGateway Script
Python program to convert serial traffic to MQTT and vice versa.

Serial data arrives as comma delimited in the following form (comma delimited, colons separate MQTT topic and message):
[sending_node_number],[topic]:[message],[topic]:[message]
using the topic and message from the serial read, the MQTT topics are updated:
sensors/</[sending_node_number]/[topic] [message]

MQTT topic sensors/>/# is subscribed to. MQTT Topics should be:
sensors/>/[nodeid] [message]
Any new data is sent to serial as:
[nodeid]:[message]
Which the attached arduino broadcasts over the wireless network.
Anything destined for node 1 (the gateway ardunio) is written to serial without sending mode. 

Developed for use with Moteinos https://lowpowerlab.com/guide/moteino/ using a slightly modified gateway sketch (to format serial data as comma delimited).

Primary functionality from Python MQTT client from Eclipse Paho http://www.eclipse.org/paho/
Paho documentation at https://pypi.python.org/pypi/paho-mqtt/1.1
