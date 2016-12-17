#!/usr/bin/env python3

import re
import subprocess
import yaml

DEBUG = False

movementVector = [0,0]
movementVectorSum = [0,0]


# This function gets the finger count from the libinput-debug-events output line
# The line is not formatted really beautiful so it is quite a pain to get the information needed out of it.
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

def getDirection(movementVector):
  if abs(movementVector[0]) > abs(movementVector[1]):
    if movementVector[0] > 0:
      return 'right'
    return 'left'

  if movementVector[1] > 0:
    return 'down'
  return 'up'


def getGestureType(line):
  return re.findall(r'GESTURE_(.*)_', line)[0].lower()


def getGestureEvent(line):
  return re.findall(r'GESTURE_.+_(\S*)', line)[0].lower()



def executeCommand(gType, fingerCount, direction, event):
  try:
    executeCommandCall(conf[gType][fingerCount][direction][event]['command'])
  except Exception as e:
    pass

  if event == 'end':
    try:
      executeCommandCall(conf[gType][fingerCount][direction]['command'])
    except Exception as e:
      pass


def executeCommandCall(command):
  commandList = []
  if type(command) is str:
    if command == '':
      return
    commandList = command.split(' ')
  
  else:
    if len(command) == 0:
      return
    commandList = command

  env = {
    "x": movementVector[0],
    "y": movementVector[1]
  }

  # evaluate all expressions in ${}
  for n,i in enumerate(commandList):
    commandList[n] = re.sub(r'[^\\|\s]?\${(\S*)}', 
                            lambda c: str(eval(c.group(1).lower(), {}, env)), 
                            commandList[n])

  if DEBUG:
    print(commandList)

  subprocess.call(commandList)



def getDeviceName():
  proc = subprocess.Popen(['libinput-list-devices'], stdout=subprocess.PIPE, universal_newlines=True)
  output, err = proc.communicate()
  matches = re.findall(r'Kernel:\s+(\S+).{0,}?Tap-to-click:\s+(\S+)', output, re.M | re.S)
  return sorted(device[0] for device in matches if device[1] != 'n/a')[0]

INPUT_DEVICE = getDeviceName()


conf = None
with open('config.yml', 'r') as stream:
  try:
    conf = yaml.load(stream)
  except yaml.YAMLError as e:
    print('Exception while loading config file: {}'.format(e))



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

      if event == 'begin':
        movementVectorSum = [0,0]

      if event == 'update':
        movementVector = getMovementVector(output)
        movementVectorSum[0] += movementVector[0]
        movementVectorSum[1] += movementVector[1]
        direction = getDirection(movementVector);

      if event == 'end':
        direction = getDirection(movementVectorSum)

      if direction != '':
        executeCommand(gtype, fingerCount, direction, event)

      executeCommand(gtype, fingerCount, 'all', event)