# ReadeMe.md for ld382a.py

## Introduction
ld382a.py is a little Python server, that is able to communicate with a LD382A LED device driver. It handles either single set operations for RGBW or HSI based operations, like transitions. It's basic function is to be create as smooth transistions as possible with those devices.

Originally, it has been written to be a companion for a FHEM server, but it can be used by any application or even by a shell script. It is very lightweight and doesn't hog the system or consumes much resources. Even on a RasPI it will create very smooth transitions.

Additionally, to performing simple transitions, it has the ability to create more complex effects, like a fireplace effect.

## How to use
ld382a.py has two basic modes: server mode and one-shot mode
In server mode, a socket will be created on Port 5382, where it will listen for commads that are sent it's way. In one-shot mode, it will simply perform the desired action and then quit

### Parameters
In server mode, the only mandantory parameter is the IP of the LED controller, that will be utilized. Proivide the IP by invoking it using -C <IP>.

In one-shot mode, the are additional parameters, that need to be provided, otherwise the script will terminate and show some help on which params are missing.

