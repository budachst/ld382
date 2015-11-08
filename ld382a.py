#!/usr/bin/python
#############################################
# ld382a.py                                 #
#                                           #
# A simple python program that drives a     #
# LD382A RGBW LED controller via the H(ue)  #
# S(aturation) I(ntensity) color model      #
#############################################
#                                           #
# V. 0.2.5                                  #
#############################################

import binascii
import socket
import struct
import sys,errno
import math
import colorsys
import sys,getopt
import time
import argparse
import threading
import thread
import os
import select
import random

from sys import argv
from time import sleep

cmdSetLED = 49
maxFreq = 64
rsvd1 = 0
rsvd2 = 15
addrLD382A = '10.10.0.31'
portLD372A = 5577
HUE = 0
SAT = 0
INT = 100
# for server mode
HOST = '0.0.0.0'
PORT = 5382
BUFSIZ = 64
ADDR = (HOST, PORT)
transitionActive = False
transitionRingbuffer = []
transitionCurrentSlot = 0
transitionNextSlot = 0
transitionSlotsLeft = 0
transitionMaxSlots = 16
lastRed = 0;
lastGreen = 0;
lastBlue = 0;
lastWhite = 0;
lastHUE = 0;
lastSAT = 0;
lastINT = 0;

##############################################################
def setupSocket(address,port):
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (address, port)
	sock.connect(server_address)
	return sock
##############################################################	
def setRGBW(ctrlRed,ctrlGreen,ctrlBlue,ctrlWhite,controller):
	global lastRed
	global lastGreen
	global lastBlue
	global lastWHite
	
	# clamp ranges
	ctrlRed   = max(min(ctrlRed,   255),0)
	ctrlGreen = max(min(ctrlGreen, 255),0)
	ctrlBlue  = max(min(ctrlBlue,  255),0)
	ctrlWhite = max(min(ctrlWhite, 255),0)

	# calculate checksum
	chksum = (cmdSetLED + ctrlRed + ctrlGreen + ctrlBlue + ctrlWhite + rsvd1 + rsvd2) % 256
	# prepare array and packer
	values = (cmdSetLED,ctrlRed,ctrlGreen,ctrlBlue,ctrlWhite,rsvd1,rsvd2,chksum)
	packer = struct.Struct('B B B B B B B B')
	packed_data = packer.pack(*values)
	controller.sendall(packed_data)
	# save latest RGBW in global vars for reuse
	lastRed = ctrlRed
	lastGreen = ctrlGreen
	lastBlue = ctrlBlue
	lastWhite = ctrlWhite
##############################################################
def hsi2rgbw(H,S,I,controller):
	global lastHUE
	global lastSAT
	global lastINT
	
	# save latest HSI values in global vars
	lastHUE = H
	lastSAT = S
	lastINT = I

	r = 0
	g = 0
	b = 0
	w = 0
	# constants for trimming down LED colors, if they're too bright
	# should of course be between 0.0 < factor <= 1.0. This will be clamped
	# between those two values
	rFactor = 1.0
	gFactor = 0.5
	bFactor = 0.5
	rfactor = (max(min(rFactor, 1),0)/1.0)
	gfactor = (max(min(gFactor, 1),0)/1.0)
	bfactor = (max(min(bFactor, 1),0)/1.0)
	
	H = H % 360
	H = (math.pi * H / 180.0)
	
	S = (max(min(S, 100),0)/100.0)
	I = (max(min(I, 100),0)/100.0)
	
	
	if H < 2.09439:
		cos_h = math.cos(H)
		cos_1047_h = math.cos(1.047196667-H)
		r = S*255*I/3*(1+cos_h/cos_1047_h)
		g = S*255*I/3*(1+(1-cos_h/cos_1047_h))*gfactor
		b = 0
		w = 255*(1-S)*I

	if (H >= 2.09439 and H < 4.188787):
		H = H - 2.09439
		cos_h = math.cos(H)
		cos_1047_h = math.cos(1.047196667-H)
		g = S*255*I/3*(1+cos_h/cos_1047_h)*gfactor
		b = S*255*I/3*(1+(1-cos_h/cos_1047_h))*bfactor
		r = 0
		w = 255*(1-S)*I

	if (H >= 4.188787):
		H = H - 4.188787
		cos_h = math.cos(H)
		cos_1047_h = math.cos(1.047196667-H)
		b = S*255*I/3*(1+cos_h/cos_1047_h)*bfactor
		r = S*255*I/3*(1+(1-cos_h/cos_1047_h))
		g = 0
		w = 255*(1-S)*I
	# print "Set R: %d G: %d B: %d" % (int(r),int(g),int(b))
	setRGBW(int(r),int(g),int(b),int(w),controller)
##############################################################
def performTransition(cmdBlock,controller):
	#split command block
	msgBlock=cmdBlock.split( ',' )
	tmpCMD=msgBlock.pop(0)
	cycleTime = float(1/float(maxFreq))
	if len(msgBlock) == 7:
		# transition with start values requested, get and convert values from list
		hueStart = int(msgBlock.pop(0))
		satStart = int(msgBlock.pop(0))
		intStart = int(msgBlock.pop(0))
		hueEnd   = int(msgBlock.pop(0))
		satEnd   = int(msgBlock.pop(0))
		intEnd   = int(msgBlock.pop(0))
		timer    = float(msgBlock.pop(0))
	if len(msgBlock) == 4:
		# transition from previous state requested, get and convert target values from list
		hueStart = int(lastHUE)
		satStart = int(lastSAT)
		intStart = int(lastINT)
		hueEnd   = int(msgBlock.pop(0))
		satEnd   = int(msgBlock.pop(0))
		intEnd   = int(msgBlock.pop(0))
		timer    = float(msgBlock.pop(0))

	
	# print "Options: CMD: %s, hueStart: %d, satStart: %d, intStart: %d" % (msgBlock,hueStart,satStart,intStart)
	# print "Options: hueEnd: %d, satEnd: %d, intEnd: %d timer: %d" % (hueEnd,satEnd,intEnd, timer)
	
	# calculate transition increments
	hueSteps = int(hueEnd - hueStart)
	satSteps = int(satEnd - satStart)
	intSteps = int(intEnd - intStart)
	transitionSteps = int(timer * maxFreq)
	
	# print "Steps: hueSteps: %d, satSteps: %d, intSteps: %d, maxFreq: %d" % (hueSteps,satSteps,intSteps,maxFreq)
	hueStep = float(hueSteps)/float(timer)/float(maxFreq)
	satStep = float(satSteps)/float(timer)/float(maxFreq)
	intStep = float(intSteps)/float(timer)/float(maxFreq)
	# print "Steps: hueStep: %f, satStep: %f, intStep: %f" % (hueStep,satStep,intStep)
	# perform loop for time (seconds)
	while transitionSteps > 0:
		prevHue = int(hueStart)
		prevSat = int(satStart)
		prevInt = int(intStart)
		hueStart = float(hueStart + hueStep)
		satStart = float(satStart + satStep)
		intStart = float(intStart + intStep)
		transitionSteps =  transitionSteps -1
		if prevHue != int(hueStart) or prevSat != int(satStart) or prevInt != int(intStart):
			hsi2rgbw(int(hueStart),int(satStart),int(intStart),controller)
			# print "Output: Steps left: %d HUE: %d SAT: %d INT: %d" % (transitionSteps,int(hueStart),int(satStart),int(intStart))
		else:
			sleep(cycleTime)
##############################################################
def effectFire(duration,controller):
	ts = time.time() + float(duration)
	while (time.time() < ts) and (transitionSlotsLeft < 2):
		newHUE = random.randint(22,30)
		newSAT = random.randint(95,100)
		newINT = random.randint(20,30)
		newDelay = round(random.uniform(0.05, 0.3), 5)
		# if newDelay exceeds ts, then cap it
		if (time.time() + newDelay) > ts:
			print "newDelay capped, break..!"
			break
		newMsgBlock = "t,%d,%d,%d,%d,%d,%d,%f" % (lastHUE,lastSAT,lastINT,newHUE,newSAT,newINT,newDelay)
		performTransition(newMsgBlock,controller)
		sleep(float(newDelay))
		print "Time left: %f" % (float(ts-time.time()))
############################################################## 
def getValues():
	msg = "%d,%d,%d,%d,%d,%d,%d" % (lastRed,lastGreen,lastBlue,lastWhite,lastHUE,lastSAT,lastINT)
	# print "msg: %s" % (msg)
	clientsock.send(msg)
##############################################################
def decodeCommandblock(data):
	global transitionActive
	transitionActive = True
	#parse command
	msgBlock=data.split( ',' )
	msgCMD=msgBlock.pop(0)
	#open socket to LED controller
	dreamyLightController = setupSocket(addrLD382A,portLD372A)

	# check for single value set
	if msgCMD == "s" or msgCMD == "S":
		# HSI direct set requested, just call HSI conversion
		# command block: "[s|S],hue,sat,intensity"
		hsi2rgbw(int(msgBlock.pop(0)),int(msgBlock.pop(0)),int(msgBlock.pop(0)),dreamyLightController)
	if msgCMD == "r" or msgCMD == "R":
		# RGBW direct set requested, just call HSI conversion
		# command block; "[r|R],red,green,blue,white"
		setRGBW(int(msgBlock.pop(0)),int(msgBlock.pop(0)),int(msgBlock.pop(0)),int(msgBlock.pop(0)),dreamyLightController)
	
	# check for transition sets
	if msgCMD == "t" or msgCMD == "T":
		# simple transition from HSI to H'S'I'
		# command block: "t,hue,sat,int,hue',sat',int',duration"
		performTransition(data,dreamyLightController)
	# check for effect sets
	if msgCMD == "e" or msgCMD == "E":
		# select effect to run
		# command block: "[e|E],effect,duration"
		msgEffect=msgBlock.pop(0)
		msgDuration=msgBlock.pop(0)
		# run fire effect proc
		if msgEffect == "fire" or msgEffect == "Fire":
		 print "Effect 'Fire' selected"
		 effectFire(msgDuration, dreamyLightController)			

	transitionActive = False
	# close socket to LED controller
	dreamyLightController.close()
##############################################################
### MAIN starts here ###
# parse command line arguments
# these arguments are needed
# hue, stat(uration), int(ensity), contr(oller)
parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('-H','--HUE', help='Value for HUE')
parser.add_argument('-S','--SAT', help='Value for saturation')
parser.add_argument('-I','--INT', help='Value for intensity')
parser.add_argument('-C','--CTRL', help='Value for controller IP',required = True)
args = vars(parser.parse_args())

addrLD382A = args['CTRL']
if args['HUE']: HUE = int(args['HUE'])
if args['SAT']: SAT = int(args['SAT'])
if args['INT']: INT = int(args['INT'])


# if parameters have been provided, run in one-shot mode as
# client and terminate
if HUE and SAT and INT and addrLD382A:
	#open socket to LED controller
	dreamyLightController = setupSocket(addrLD382A,portLD372A)
	hsi2rgbw(HUE,SAT,INT,dreamyLightController)
	# close socket to LED controller
	dreamyLightDachboden.close()

else:
	# open socket for incoming connections and run in server mode
	serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversock.bind(ADDR)
	serversock.listen(2)
	read_list = [serversock]
	
	#open socket to LED controller
	#dreamyLightDachboden = setupSocket(addrLD382A,portLD372A)

	# enter loop
	while True:
		readable, writable, errored = select.select(read_list, [], [],.5)
		# print "main while... Slots left: %d Next slot: %d" % (transitionSlotsLeft,transitionNextSlot)
		for s in readable:
			if s is serversock:
				clientsock, addr = serversock.accept()
				read_list.append(clientsock)
				print "Connection from", addr
			else:
				data = s.recv(BUFSIZ).rstrip()
				print "received: %s -> Slot %d" % (data,transitionNextSlot)
				transitionRingbuffer.insert(transitionNextSlot,data)
				transitionNextSlot = (transitionNextSlot + 1) % transitionMaxSlots
				transitionSlotsLeft = transitionSlotsLeft + 1
				# clamp transitionSlotsLeft to 0 <> transitionMaxSlots - 1
				transitionSlotsLeft = max(min(transitionSlotsLeft,(transitionMaxSlots-1)),0)
				if data:
					#parse command early to catch 'g' request, before the socket closes
					msgBlock=data.split( ',' )
					msgCMD=msgBlock.pop(0)
					if msgCMD == "g" or msgCMD == "G":
						# return current saved values for RGBW and HSI
		 				getValues()
					s.close()
					read_list.remove(s)
		if transitionSlotsLeft > 0 and not transitionActive:
			thread.start_new_thread(decodeCommandblock, (transitionRingbuffer[transitionCurrentSlot],))
			transitionSlotsLeft = transitionSlotsLeft - 1
			print "played: %s Slot: %d, remaining: %d" % (transitionRingbuffer[transitionCurrentSlot],transitionCurrentSlot,transitionSlotsLeft)
			transitionCurrentSlot = (transitionCurrentSlot + 1) % transitionMaxSlots
			# clamp transitionSlotsLeft to 0 <> transitionMaxSlots - 1
			transitionSlotsLeft = max(min(transitionSlotsLeft, (transitionMaxSlots-1)),0)

# close socket to LED controller
dreamyLightDachboden.close()



