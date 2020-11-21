#!/usr/bin/python3
#encoding:utf-8
#

# Author Dan Pancamo
# Description: Get the distance to the fish
# HARDWARE
	# Rasapberry pi0w https://amzn.to/32Le5c6
	# adafruit ultrasonic 4884

# Updates
# 11/19/2020  New FishpI




from gpiozero import CPUTemperature



import psutil
import graphyte

import time
import os
import serial

import statistics


#GLOBALS
disthigh = 0
distlow = 1000
distavg = 0
count = 0 
medianDistance = 0
CpuUtil = 0







GRAPHITE="localhost"
HOT="hot.pancamo.com"
myws="KTXOLIVI"
mywslocation="PancamoPointPier"

graphyte.init(GRAPHITE, prefix='wu.KTXOLIVI.PI2')

sender1 = graphyte.Sender(GRAPHITE, prefix='wu.KTXOLIVI.PI2')
#sender2 = graphyte.Sender(HOT, prefix='wu.KTXOLIVI.PI2')


SERIAL_PORT = "/dev/serial0"   # or "COM4" or whatever
serialport = serial.Serial(SERIAL_PORT, 9600)



# This function measures a distance


def read_me007ys(ser, timeout = 1.0):
    ts = time.time()
    buf = bytearray(3)
    idx = 0

    while True:
        # Option 1, we time out while waiting to get valid data
        if time.time() - ts > timeout:
            raise RuntimeError("Timed out waiting for data")

        c = ser.read(1)[0]
        #print(c)
        if idx == 0 and c == 0xFF:
            buf[0] = c
            idx = idx + 1
        elif 0 < idx < 3:
            buf[idx] = c
            idx = idx + 1
        else:
            chksum = sum(buf) & 0xFF
            if chksum == c:
                return (buf[1] << 8) + buf[2]
            idx = 0
    return None


def toGraphite(Distance,CpuUtil):


		cpu = CPUTemperature()


		FishDist = ((Distance*0.0393701)/12)

		CpuTemp = (cpu.temperature * (9/5)) + 32

		#print("FishDist=",FishDist)

		#print("----------sender 1---------------------")


		sender1.send('FishDist', FishDist)


		sender1.send('CpuTemp',CpuTemp)
		sender1.send('CpuUtil',CpuUtil)

		#print("----------sender 2---------------------")
		#sender2.send('WaterLevelHigh', WaterLevelHigh)
		#sender2.send('WaterLevelLow', WaterLevelLow)
		#sender2.send('WaterLevelAvg', WaterLevelAvg)
		#sender2.send('WaterLevelMedian', WaterLevelMedian)
		#sender2.send('WaveHeight', WaveHeight)
		#sender2.send('CpuTemp',CpuTemp)
		#sender2.send('CpuUtil',CpuUtil)


		return



if __name__ == '__main__':
	try:


		while True:
			distance = read_me007ys(serialport)
			#print("CURRENT = %.1f in" % (distance*0.0393701))

			if distance > 0:
				Cpu =  psutil.cpu_percent(percpu=True)
				CpuUtil = Cpu[0]
				toGraphite(distance,CpuUtil)

			#time.sleep(.3)
				


        # Reset by pressing CTRL + C
	except KeyboardInterrupt:
		print("Measurement stopped by User")
        

