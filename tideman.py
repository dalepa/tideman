#!/usr/bin/python
#encoding:utf-8


# Author Dan Pancamo
# Description Get the distance to the water and calculate a bunch of stats
	# Push to Grafana
	# Watch the tide come in
	
# HARDWARE
	# Rasapberry pi0w https://amzn.to/32Le5c6
	# JSN-SR04T https://amzn.to/2FDJjcK 



from gpiozero import CPUTemperature



import RPi.GPIO as GPIO
import os
import time
import graphyte
import statistics

# Define GPIO to use on Pi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO_TRIGGER = 15
GPIO_ECHO = 14

TRIGGER_TIME = 0.00001
MAX_TIME = 0.014  # max time waiting for response in case something is missed
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Echo

GPIO.output(GPIO_TRIGGER, False)

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


GRAPHITE="192.168.1.144"
GRAPHITE="hot.pancamo.com"
myws="KTXOLIVI"
mywslocation="PancamoPointPier"
graphyte.init(GRAPHITE, prefix='wu.KTXOLIVI.PI')



# This function measures a distance


def measure():
    # Pulse the trigger/echo line to initiate a measurement
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(TRIGGER_TIME)
    GPIO.output(GPIO_TRIGGER, False)

    # ensure start time is set in case of very quick return
    start = time.time()
    timeout = start + MAX_TIME

    # set line to input to check for start of echo response
    while GPIO.input(GPIO_ECHO) == 0 and start <= timeout:
        start = time.time()

    if(start > timeout):
        return -1

    stop = time.time()
    timeout = stop + MAX_TIME
    # Wait for end of echo response
    while GPIO.input(GPIO_ECHO) == 1 and stop <= timeout:
        stop = time.time()

    if(stop <= timeout):
        elapsed = stop-start
        distance = float(elapsed * 34300)/2.0
    else:
        return -1
    return distance


if __name__ == '__main__':
    try:

	flowstarttime = time.time()
	flowsstartdepth = 0

        while True:
            distance = measure()

            if(distance > -1):

		#print("CURRENT = %.1f in" % (distance*0.393701))
		mDistance[count] = distance

		if count == 99:

			
			cpu = CPUTemperature()

			mDistance.sort()

			#print mDistance

			distlow = mDistance[20]
			disthigh = mDistance[80]
			distavg = statistics.mean(mDistance[20:80])


			waveheight = disthigh - distlow
			medianDistance = statistics.median(mDistance[20:80])

			print "---------------------  time left ----------------", MAXFLOWTIME -(time.time() - flowstarttime)


			WaterLevelHigh=SENSORHEIGHTINFEET-((distlow*0.393701)/12)
			WaterLevelLow=SENSORHEIGHTINFEET-((disthigh*0.393701)/12)
			WaterLevelAvg=SENSORHEIGHTINFEET-((distavg*0.393701)/12)
			WaterLevelMedian=SENSORHEIGHTINFEET-((medianDistance*0.393701)/12)
			WaveHeight=(waveheight*0.393701)
	
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
			print "---------------------  average ----------------"



			count = 0
			distavg = 0
			disthigh = 0
			distlow = 400

			if flowsstartdepth == 0:
				flowsstartdepth = WaterLevelLow
		else:
			count = count + 1
			distavg = distavg + distance

		if ((time.time() - flowstarttime) > MAXFLOWTIME):
			flowtime = time.time() - flowstarttime

			flowstopdepth = WaterLevelLow
			flowrateinperhour = (((flowstopdepth - flowsstartdepth) * 3600 ) / flowtime)*12


			print "flowsstartdepth = ", flowsstartdepth
			print "flowstopdepth = ", flowstopdepth
			print "flowtime = ", flowtime
			print "flowrateinperhour = ", flowrateinperhour
			graphyte.send('WaterFlowRatePerHour',flowrateinperhour)  #in inches

			flowsstartdepth = 0 
			flowstarttime = time.time()
			
            else:
                print("bad distance")

            time.sleep(0.1)
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
