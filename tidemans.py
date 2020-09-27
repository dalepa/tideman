#!/usr/bin/python3
#encoding:utf-8


# Author Dan Pancamo
# Description: Get the distance to the water and calculate a bunch of stats
# HARDWARE
	# Rasapberry pi0w https://amzn.to/32Le5c6
	# adafruit ultrasonic 4884



from gpiozero import CPUTemperature



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
mDistance = [0] * 100


#SENSORLOCATION 
PIERHEIGHTINFEET=82.5/12
SENSORHEIGHTINFEET=93.0/12
SENSORABOVEPIERINFEET=SENSORHEIGHTINFEET-PIERHEIGHTINFEET


MAXFLOWTIME=(60*60)



GRAPHITE="localhost"
myws="KTXOLIVI"
mywslocation="PancamoPointPier"
graphyte.init(GRAPHITE, prefix='wu.KTXOLIVI.PI2')



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


def toGraphite(mDistance):

		mDistance.sort()

		#print mDistance

		distlow = mDistance[10]
		disthigh = mDistance[90]
		distavg = statistics.mean(mDistance[10:90])


		waveheight = disthigh - distlow
		medianDistance = statistics.median(mDistance[10:90])



		WaterLevelHigh=SENSORHEIGHTINFEET-((distlow*0.0393701)/12)-SENSORABOVEPIERINFEET
		WaterLevelLow=SENSORHEIGHTINFEET-((disthigh*0.0393701)/12)-SENSORABOVEPIERINFEET
		WaterLevelAvg=SENSORHEIGHTINFEET-((distavg*0.0393701)/12)-SENSORABOVEPIERINFEET
		WaterLevelMedian=SENSORHEIGHTINFEET-((medianDistance*0.0393701)/12)-SENSORABOVEPIERINFEET
		WaveHeight=(waveheight*0.0393701)

		print("wu.{}.{}.WaterLevelHigh {:.0f} {}".format( myws, mywslocation, time.time(), WaterLevelHigh))
		print("wu.{}.{}.WaterLevelLow {:.0f} {}".format( myws, mywslocation, time.time(), WaterLevelLow))
		print("wu.{}.{}.WaterLevelAvg {:.0f} {}".format( myws, mywslocation, time.time(), WaterLevelAvg))
		print("wu.{}.{}.WaveHeight {:.0f} {}".format( myws, mywslocation, time.time(), WaveHeight))
		print("wu.{}.{}.WaterLevelMedian {:.0f} {}".format( myws, mywslocation, time.time(), WaterLevelMedian))
		print("wu.{}.{}.CpuTemp {:.0f} {}".format( myws, mywslocation, time.time(), ((cpu.temperature * (9/5)) + 32)))


		graphyte.send('WaterLevelHigh', WaterLevelHigh)
		graphyte.send('WaterLevelLow', WaterLevelLow)
		graphyte.send('WaterLevelAvg', WaterLevelAvg)
		graphyte.send('WaterLevelMedian', WaterLevelMedian)
		graphyte.send('WaveHeight', WaveHeight)
		graphyte.send('CpuTemp',((cpu.temperature * (9/5)) + 32))




		return
	

if __name__ == '__main__':
	try:

		count = 0

		while True:
			distance = read_me007ys(serialport)
			#print("CURRENT = %.1f in" % (distance*0.0393701))
			mDistance[count] = distance


		
			cpu = CPUTemperature()

			if count == 99:
				print (mDistance)
				toGraphite(mDistance)
				count = 0
			else:
				count = count + 1
				


        # Reset by pressing CTRL + C
	except KeyboardInterrupt:
		print("Measurement stopped by User")
        

