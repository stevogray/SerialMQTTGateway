#--------------------------
# Settings file that can be used to run the code on development platform and on the raspberry PI without having to change the base code
# On initial install place both files onto the PI gatway then edit this file
# Further deploys should only need the SerialGateway.py file sent to the Pi Gateway and it will pickup the local settings


#Change to the approptiate Serial device on the target system.
SERIALDEV='/dev/cu.usbserial-A603G0H1'
#SERIALDEV='/dev/ttyAMA0'

#Change to the appropriate log file location on the target system.
LOG_FILENAME = "/Users/david/PycharmProjects/SerialMQTTGateway/gateway.log"
#LOG_FILENAME = "/home/pi/gateway.log"
#Log levels are CRITICAL (50), ERROR (40), WARNING (30), INFO (20), DEBUG (10), NOTSET (0)
#Any message with importance of this level or higher will be logged
LOG_LEVEL = "WARNING"

#MQTT Server Settings - Most likely the same for test and prod, but lets be consistent with the settings.
BROKER="10.88.87.180"
PORT=1883

#Serial Port Settings
BAUD=115200
