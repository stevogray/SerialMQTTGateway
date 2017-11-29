# SerialMQTTGateway Script
#### Python program to convert serial traffic to MQTT and vice versa.

Serial data arrives as comma delimited in the following form (comma delimited, colons separate MQTT topic and message):
```
{sending_node_number},{topic}:{message},{topic}:{message}
```
example:
```
5,Temperature:5,Battery:LOW
```
using the topic and message from the serial read, the MQTT topics are updated:
```
sensors/</[sending_node_number]/{topic} {message}
```
example from above:
```
Topic: sensors/</5/Temperature Message: 20.6
Topic: sensors/</5/Battery     Message: LOW
```

MQTT topic sensors/>/# is subscribed to. MQTT Topics should be:
```
sensors/>/{nodeid} {message}
or
sensors/>/{nodeid}/{topic} {message}
```
Any new data is sent to serial as:
```
<{nodeid}:{topic}:{message}>
```
eg Topic: sensors/>/5/LED Message:ON would be sent to serial as:
```
<5:LED:ON>
```
Which the attached arduino broadcasts over the wireless network. The code in the arduino should look for the start marker "<" and the end marker ">". Any message destined for node 1 (the gateway ardunio) is written to serial without sending node.

##### Developed for use with Moteinos https://lowpowerlab.com/guide/moteino/ using a modified gateway sketch (to format serial data as comma delimited).
##### Primary functionality from Python MQTT client from Eclipse Paho http://www.eclipse.org/paho/
##### Paho documentation at https://pypi.python.org/pypi/paho-mqtt/1.1
