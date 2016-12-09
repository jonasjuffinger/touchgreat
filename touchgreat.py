#!/usr/bin/python3
import subprocess

#CONFIG
# The number of the fingers, 3 or 4
FINGER_COUNT = 4
# Factor of the mouse speed. Higher makes the cube rotating faster
SPEED = 1.5
# Only rotate the cube on the x-axis
ONLY_X = False
# Key combination to initiate the cube rotation
KEYCOMBO = 'Control_L+Alt_L'
# The path to the touchpad input device
INPUT_DEVICE = '/dev/input/event5'


# This function gets the finger count from the libinput-debug-events output line
# The line is not formatted really beautiful so it is quite a pain to get the information needed out of it.
def getFingerCount(line):
    fingerCountDirection = line.split('\t')[2]

    fingerCountStr = ''
    if fingerCountDirection.find(' ') == -1:
        fingerCountStr = fingerCountDirection
    else:
        fingerCountStr = fingerCountDirection[:fingerCountDirection.find(' ')]

    fingerCount = -1;
    try:
        fingerCount = int(fingerCountStr)
    except ValueError:
        pass

    return fingerCount

# This function gets the direction of the swipe
def getDirection(line):
    parts = line.split('\t')[2].split(' ')
    direction = [0,0]

    yDirectionInNextPart = False

    for part in parts:
        if yDirectionInNextPart and len(part) != 0:
            yDirectionInNextPart = False
            direction[1] = float(part)
            break;

        if '/' in part:
            directionStrings = part.split('/')
            direction[0] = float(directionStrings[0])

            if len(directionStrings[1]) == 0:
                yDirectionInNextPart = True
            else:
                direction[1] = float(directionStrings[1])
                break;

    return direction

# run libinput-debug-events
# the --device INPUT_DEVICE argument lets libinput-debug-events print only events of this device
# stdbuf -oL is very important, because the standard libc functions always buffer if the output is written
# into a pipe. stdbuf -oL prevents this.
proc = subprocess.Popen(['stdbuf', '-oL', '--', 'libinput-debug-events', '--device', INPUT_DEVICE], stdout=subprocess.PIPE)

# get the output of libinput-debug-events forever
while True:
    # get a line of libinput-debug-events
    output = proc.stdout.readline().decode('ascii').rstrip()

    if output == '' and proc.poll() is not None:
        break #stop if libinput-debug-events stops, but this should not happen

    if output:
        # run the actions for the different events
        if 'GESTURE_SWIPE_BEGIN' in output:
            fingerCount = getFingerCount(output)
            if fingerCount == FINGER_COUNT:
                subprocess.call(['xdotool', 'keydown', KEYCOMBO, 'mousedown', '1'])


        if 'GESTURE_SWIPE_UPDATE' in output:
            fingerCount = getFingerCount(output)
            direction = getDirection(output)
            if fingerCount == FINGER_COUNT:
                if ONLY_X:
                    direction[1] = 0
                subprocess.call(['xdotool', 'mousemove_relative', '--', str(int(direction[0]*SPEED)), str(int(direction[1]*SPEED))])

        if 'GESTURE_SWIPE_END' in output:
            fingerCount = getFingerCount(output)
            if fingerCount == FINGER_COUNT:
                subprocess.call(['xdotool', 'mouseup', '1', 'keyup', KEYCOMBO])
