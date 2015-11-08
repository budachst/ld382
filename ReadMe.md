# ReadeMe.md for ld382a.py

## Introduction
ld382a.py is a little Python server, that is able to communicate with a LD382A LED device driver. It handles either single set operations for RGBW or HSI based operations, like transitions. It's basic function is to be create as smooth transistions as possible with those devices.

Originally, it has been written to be a companion for a FHEM server, but it can be used by any application or even by a shell script. It is very lightweight and doesn't hog the system or consumes much resources. Even on a RasPI it will create very smooth transitions.

Additionally, to performing simple transitions, it has the ability to create more complex effects, like a fireplace effect.

## How to use
ld382a.py has two basic modes: server mode and one-shot mode
In server mode, a socket will be created on Port 5382, where it will listen for commads that are sent it's way. In one-shot mode, it will simply perform the desired action and then quit

### Parameters
In server mode, the only mandantory parameter is the IP of the LED controller, that will be utilized. Proivide the IP by invoking it using -C [IP].

In one-shot mode, the are additional parameters, that need to be provided, otherwise the script will terminate and show some help on which params are missing.

### Functions of ld382a.py
There are currently four operations, that can be send to the server process. Each command is simply made up of a command block in text format. The four command are:

(s) perform a single HSI set
(r) perform a single RGBW set
(t) perform a transition
(e) run an effect that is built-in into the ld382a.py script

#### (s) perform single HSI set
To set a single HSI value on the LD device use this command block:
"[s|S],hue, sat, int" where
- s|S indicates the operation
- hue in 0 to 360 degrees
- sat saturation, range from 0 to 100
- int intensity (of the colors), range from 0 to 100

#### (r) perform single RGBW set
To set a single RGBW value on the LD device use this command block:
"[r|R],red, green, blue, white" where
- r|R indicates the operation
- red in range from 0 to 255
- green in range from 0 to 255
- blue in range from 0 to 255
- white in range from 0 to 255

This command enables the maximum amount of brightness, one get get from the device, as it enables to set all LEDs at once to full brightness. However, the resulting 'white' might not look the way, one would expect.

#### (t) perform a transition
There are two ways to define how a transistion in the HSI space should be performed. One variant used two HSI value sets plus a duration value while the other only uses one HSI value set plus a duration value. So there two possible invokations for the command block:
"[t|T],hue, sat, int, hue',sat',int', duration" where
- t|T indicates the operation
- hue at start of transition in range from 0 to 359 degrees
- sat at start of transition in range from 0 to 100
- int at start of transition in range from 0 to 100
- hue' at end of transition in range from 0 to 359 degrees
- sat' at end of transition in range from 0 to 100
- int' at end of transition in range from 0 to 100
- duration transition time in seconds

The short variant utilizes the last saved values inside the server process and thus only indicates the target values and the duration of the transition:
"[t|T],hue, sat, int, duration" where
- t|T indicates the operation
- hue at end of transition in range from 0 to 359 degrees
- sat at end of transition in range from 0 to 100
- int at end of transition in range from 0 to 100
- duration transition time in seconds
