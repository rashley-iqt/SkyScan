#!/usr/bin/env python3



import argparse
import threading
import json
import sys
import os
import logging
import logging
import coloredlogs
import calendar
from datetime import datetime, timedelta
import signal
import random
import time
import re
import errno
import paho.mqtt.client as mqtt 
from json.decoder import JSONDecodeError
import pantilthat

args = None
pan = 0
tilt = 0
actualPan = 0
actualTilt = 0

# https://stackoverflow.com/questions/45659723/calculate-the-difference-between-two-compass-headings-python

# The camera hat takes bearings between -90 and 90. 
# h1 is the target heading
# h2 is the heading the camera is pointed at
def getHeadingDiff(h1, h2):
    if h1 > 360 or h1 < 0 or h2 > 360 or h2 < 0:
        raise Exception("out of range")
    diff = h1 - h2
    absDiff = abs(diff)

    if absDiff == 180:
        return absDiff
    elif absDiff < 180:
        return diff
    elif h2 > h1:
        return 360 - absDiff
    else:
        return absDiff - 360

def setPan(bearing):
    global pan
    camera_bearing = args.bearing
    diff_heading = getHeadingDiff(bearing, camera_bearing)
    
    if diff_heading  > -85 and diff_heading < 85:
        if abs(pan - diff_heading) > 2:
            logging.info("Heading Diff %d for Bearing %d & Camera Bearing: %d"% (diff_heading, bearing, camera_bearing))
    
            pan = diff_heading
            logging.info("Setting Pan to: %d"%pan)
            
        return True
    return False

def setTilt(azimuth):
    global tilt
    if azimuth < 90:
        if abs(tilt-azimuth) > 2:
            tilt = azimuth
            
            logging.info("Setting Tilt to: %d"%azimuth)

def moveCamera():
    global actualPan
    global actualTilt
    while True:
        if actualTilt != tilt:
            logging.info("Moving Tilt to: %d Goal: %d"%(actualTilt, tilt))
            if actualTilt < tilt:
                actualTilt += 1
            else:
                actualTilt -= 1
        if actualPan != pan:
            logging.info("Moving Pan to: %d Goal: %d"%(actualPan, pan))
            if actualPan < pan:
                actualPan += 1
            else:
                actualPan -= 1
        pantilthat.tilt(actualTilt)
        # Turns out that negative numbers mean to move the right and positive numbers mean move to the left... 
        # I think this is backwards, I am going to switch it, so here I am going to multiply by -1
        pantilthat.pan(actualPan * -1)
        # Sleep for a bit so we're not hammering the HAT with updates
        time.sleep(0.005)
#############################################
##         MQTT Callback Function          ##
#############################################
def on_message(client, userdata, message):
    command = str(message.payload.decode("utf-8"))
    #rint(command)
    try:
        update = json.loads(command)
        #payload = json.loads(messsage.payload) # you can use json.loads to convert string to json
    except JSONDecodeError as e:
    # do whatever you want
        print(e)
    except TypeError as e:
    # do whatever you want in this case
        print(e)
    except ValueError as e:
        print(e)
    except:
        print("Caught it!")
    
    #logging.info("Bearing: {} Azimuth: {}".format(update["bearing"],update["azimuth"]))
    bearingGood = setPan(update["bearing"])
    setTilt(update["azimuth"])


def main():
    global args
    global logging
    global pan
    global tilt
    parser = argparse.ArgumentParser(description='An MQTT based camera controller')

    parser.add_argument('-b', '--bearing', help="What bearing is the font of the PI pointed at (0-360)", default=0)
    parser.add_argument('-m', '--mqtt-host', help="MQTT broker hostname", default='127.0.0.1')
    parser.add_argument('-t', '--mqtt-topic', help="MQTT topic to subscribe to", default="SkyScan")
    parser.add_argument('-v', '--verbose',  action="store_true", help="Verbose output")

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO

    styles = {'critical': {'bold': True, 'color': 'red'}, 'debug': {'color': 'green'}, 'error': {'color': 'red'}, 'info': {'color': 'white'}, 'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True}, 'success': {'bold': True, 'color': 'green'}, 'verbose': {'color': 'blue'}, 'warning': {'color': 'yellow'}}
    level = logging.DEBUG if '-v' in sys.argv or '--verbose' in sys.argv else logging.INFO
    if 1:
        coloredlogs.install(level=level, fmt='%(asctime)s.%(msecs)03d \033[0;90m%(levelname)-8s '
                            ''
                            '\033[0;36m%(filename)-18s%(lineno)3d\033[00m '
                            '%(message)s',
                            level_styles = styles)
    else:
        # Show process name
        coloredlogs.install(level=level, fmt='%(asctime)s.%(msecs)03d \033[0;90m%(levelname)-8s '
                                '\033[0;90m[\033[00m \033[0;35m%(processName)-15s\033[00m\033[0;90m]\033[00m '
                                '\033[0;36m%(filename)s:%(lineno)d\033[00m '
                                '%(message)s')

    logging.info("---[ Starting %s ]---------------------------------------------" % sys.argv[0])
    pantilthat.pan(pan)
    pantilthat.tilt(tilt)
    threading.Thread(target = moveCamera, daemon = True).start()
        # Sleep for a bit so we're not hammering the HAT with updates
    time.sleep(0.005)
    print("connecting to MQTT broker at "+ args.mqtt_host+", channel '"+args.mqtt_topic+"'")
    client = mqtt.Client("pan-tilt-pi-camera") #create new instance

    client.on_message=on_message #attach function to callback

    client.connect(args.mqtt_host) #connect to broker
    client.loop_start() #start the loop
    client.subscribe(args.mqtt_topic+"/#")
    #############################################
    ##                Main Loop                ##
    #############################################
    while True:
        time.sleep(0.1)



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(e, exc_info=True)
