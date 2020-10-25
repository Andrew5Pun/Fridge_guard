#! /bin/bash

# This script is a modified version of San Bergmans' original script. Credit goes to him.
#         https://www.sbprojects.net/projects/raspberrypi/temperature.php
#
# Modified by Andrew Pun to include curl API communication. Does not take temperature.
#         andrewpun.com

W1DIR="/sys/bus/w1/devices"

# Exit if 1-wire directory does not exist
if [ ! -d $W1DIR ]
then
    echo "Can't find 1-wire device directory"
    exit 1
fi

# Get a list of all devices
DEVICES=$(ls $W1DIR)

# Username and password
NAME="[user]"
PASS="[password]"

echo $NAME

# Loop through all devices
for DEVICE in $DEVICES
do
    # Ignore the bus master device
    if [ $DEVICE != "w1_bus_master1" ]
    then

      EXECU="curl -u "$NAME":"$PASS" -i -H \"Content-Type: application/json\" -X POST -d '{\"name\":\""$NAME"\", \"serial\":\""$DEVICE"\", \"comment\":\"no comment\"}' [API address]"

      echo "$EXECU"

      eval "$EXECU"
    fi
done
