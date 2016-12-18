
# TOUCHGREAT

Touchgreat makes your touchpad great.

There are many programs out there that let you bind key shortcuts to gestures on your touchpad. But they all use a very simple approach of just executing an key combo when a gesture ends. Touchgreat can do way more. It is possible to execute commands on a gesture start, an update of the gesture and at the end. On the update it is possible to use the finger movement as argument for the command.

Thats for example possible: [click](https://www.jonasjuffinger.com/2016/12/08/natural-swipe-workspace-switcher/#Result)

## Installation
### libinput
Touchgreat uses libinput to recognize gestures. Libinput can be installed from the software repository of your distro, but I highly recommend to compile it from source, because the gesture recognition drastically improved in the last versions. For example in the Ubuntu 16.04 repository is libinput 1.2.3 which was released in February 2016 the current version is 1.5.3.

Unprivileged users must be in the `input` group to be able to get the debug output from `libinput-debug-events`. So they have to be added
```
# gpasswd -a $USER input
```

### Python
Touchgreat is written in Python 3 so this is needed. It also uses the yaml package which can be installed with
```
# apt-get install python3-yaml
```
in Ubuntu.


## Usage
1. Clone or download the code
1. Configure touchgreat
1. Run it

### Configuration
The configuration is in the config.yml file that must be in the same directory as the touchgreat.py file. I will add user config files with the next update.

The config.yml file in this repository also contains a full configuration for advanced cube rotation with compiz. See [this](https://www.jonasjuffinger.com/touchgreat) for more information.

```yaml
# The gesture type is swipe or pinch
gestureType:
  # The finger count as string
  # A swipe can have '3' or '4' fingers
  # A pinch '2', '3' or '4'
  fingerCount:
    # The direction is up, right, down, left or all
    direction:
      # If the direction is not all there is no event key. The command is executed at the end of the gesture.
      # If the direction is all there can be an event key (begin, update, end).
      [event]:
        # The command can be string or a list.
        # The string is splited using space as the delimiter.
        command: 'echo Hello World'
        # If it is a list, the first entry is the program and the others are the arguments.
        command: ['echo', 'Hello World']
    all:
      update:
        # ${} is a special string. It can be masked with \${}
        # Everything between it is evaluated with eval before passing it to the program
        # In all: update: the variables x and y can be used and represent the moved pixels since the last update
        command: 'echo ${x} \${y} ${math.atan2(y, x)}'
```


### Run
To run touchgreat simply execute it
```
./touchgreat
```

## Insights
For more insights visit my blog:
[more](https://www.jonasjuffinger.com/touchgreat)