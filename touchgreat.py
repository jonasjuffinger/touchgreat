#!/usr/bin/env python3

import re
import subprocess
import yaml
import math

DEBUG = False

movementVector = [0,0]
movementVectorSum = [0,0]


# This function gets the finger count from the libinput-debug-events output line
def getFingerCount(line):
  return re.findall(r'\t.*\t(\w+)', line)[0]

# This function gets the direction of the swipe
def getMovementVector(line):
  match = re.findall(r'(.{1}\d+\.\d+)/(.{1}\d+\.\d+)', line)

  if match == False:
    return [0,0]

  return [
    float(match[0][0]),
    float(match[0][1])
  ]

# This function returns the type of the gesture (swipe or pinch)
def getGestureType(line):
  return re.findall(r'GESTURE_(.*)_', line)[0].lower()

# This function returns the event (begin, update, end)
def getGestureEvent(line):
  return re.findall(r'GESTURE_.+_(\S*)', line)[0].lower()


# This function returns the direction of a vector as string (up, right, down, left)
def getDirection(vector):
  if abs(vector[0]) > abs(vector[1]):
    if vector[0] > 0:
      return 'right'
    return 'left'

  if vector[1] > 0:
    return 'down'
  return 'up'


# This function calls the executeCommandCall function with the command
# that should be executed on this specific event
def executeCommand(gType, fingerCount, direction, event):
  executeCommandCall(getValueFromConf(gType, fingerCount, direction, event, 'command'))
  # if a command is directly a child of a direction end it is executed at the end
  if event == 'end':
    executeCommandCall(getValueFromConf(gType, fingerCount, direction, 'command'))

# This function executes the command
def executeCommandCall(command):
  if command is None:
    return

  # if the command is a string split it in a list
  commandList = []
  if type(command) is str:
    if command == '':
      return
    commandList = command.split(' ')
  
  else:
    if len(command) == 0:
      return
    commandList = command

  # evironment for the eval()
  # only this variables are accessable from there
  env = {
    "x": movementVector[0],
    "y": movementVector[1]
  }

  # evaluate all expressions in ${}
  # big thanks to http://stackoverflow.com/a/36222262/2531813
  for n,i in enumerate(commandList):
    commandList[n] = re.sub(r'(?:^|[^\\]{1})\${(.{0,}?)}', 
                            lambda c: str(eval(c.group(1).lower(), None, env)), 
                            commandList[n])
    # And remove \ from \${
    commandList[n] = re.sub(r'\\\$\{', '${', commandList[n])

  if DEBUG:
    print(commandList)

  # call the command
  subprocess.call(commandList)

# tries to get a value from the configuration. Returns None if
# the given path doesn't exist
def getValueFromConf(*path):
  try:
    value = conf;
    for p in path:
      value = value[p]
    return value;
  except Exception as e:
    return None


# Get the device name of the touchpad
def getDeviceName():
  # run libinput-list-devices and get the output
  proc = subprocess.Popen(['libinput-list-devices'], stdout=subprocess.PIPE, universal_newlines=True)
  output, err = proc.communicate()
  # extract all devices paths and the value of Tap-to-click of every device
  matches = re.findall(r'Kernel:\s+(\S+).{0,}?Tap-to-click:\s+(\S+)', output, re.M | re.S)
  # the device where Tap-to-click != 'n/a' is the touchpad
  return sorted(device[0] for device in matches if device[1] != 'n/a')[0]

INPUT_DEVICE = getDeviceName()



# PROGRAM START

# Load the config.yml file and parse it.
conf = None
with open('config.yml', 'r') as stream:
  try:
    conf = yaml.load(stream)
  except yaml.YAMLError as e:
    print('Exception while loading config file: {}'.format(e))
    exit(1)


# run libinput-debug-events
# the --device INPUT_DEVICE argument lets libinput-debug-events print only events of this device
# stdbuf -oL is very important, because the standard libc functions always buffer if the output is written
# into a pipe. stdbuf -oL prevents this.
proc = subprocess.Popen(str('stdbuf -oL -- libinput-debug-events --device '+INPUT_DEVICE).split(' '), stdout=subprocess.PIPE)


# get the output of libinput-debug-events forever
while True:
  # get a line of libinput-debug-events
  output = proc.stdout.readline().decode('ascii').rstrip()

  if output == '' and proc.poll() is not None:
    break #stop if libinput-debug-events stops, but this should not happen

  if output:
    # run the actions for the different events
    if 'GESTURE' in output:
      direction = ''
      event = getGestureEvent(output)
      fingerCount = getFingerCount(output)
      gtype = getGestureType(output)

      # if a new gesture begins reset the movementVectorSum
      if event == 'begin':
        movementVectorSum = [0,0]

      # on an update add the movement vector
      if event == 'update':
        movementVector = getMovementVector(output)
        movementVectorSum[0] += movementVector[0]
        movementVectorSum[1] += movementVector[1]
        direction = getDirection(movementVector);

      # at the end of a gesture get the direction
      if event == 'end':
        direction = getDirection(movementVectorSum)

      if direction != '':
        executeCommand(gtype, fingerCount, direction, event)

      executeCommand(gtype, fingerCount, 'all', event)
