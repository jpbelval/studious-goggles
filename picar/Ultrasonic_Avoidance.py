#!/usr/bin/env python
'''
**********************************************************************
* Filename    : Ultrasonic_Avoidance.py
* Description : A module for SunFounder Ultrasonic Avoidance
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-26    New release
**********************************************************************
'''
import time
import RPi.GPIO as GPIO

class Ultrasonic_Avoidance(object):

    def __init__(self, channel):
        self.channel = channel
        GPIO.setmode(GPIO.BCM)
        self.TRIG = 19
        self.ECHO = 26
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        self.timeout = 0.1

    def distance(self):
        GPIO.output(self.TRIG, 0)
        time.sleep(0.01)
        GPIO.output(self.TRIG, 1)
        time.sleep(0.000015)
        pulse_end = 0
        pulse_start = 0
        GPIO.output(self.TRIG, 0)
        timeout_start = time.time()
        while GPIO.input(self.ECHO) == 0:
            pulse_start = time.time()
            if pulse_start - timeout_start > self.timeout:
                return -1
        while GPIO.input(self.ECHO) == 1:
            pulse_end = time.time()
            if pulse_end - timeout_start > self.timeout:
                return -2
        during = pulse_end - pulse_start
        cm = round(during * 340 / 2 * 100, 2)  
        return cm
    
    def get_distance(self, mount = 5):
        sum = 0
        for i in range(mount):
            a = self.distance()
            sum += a
        return int(sum/mount)

    def less_than(self, alarm_gate):
        dis = self.get_distance()
        status = 0
        if dis >= 0 and dis <= alarm_gate:
            status = 1
        elif dis > alarm_gate:
            status = 0
        else:
            status = -1
        return status

def test():
    UA = Ultrasonic_Avoidance(17)
    threshold = 30

    distances = []
    distancesPow = []
    while True:
        distance = UA.get_distance()
        status = UA.less_than(threshold)
        if distance != -1:
            distances.append(distance)
            distancesPow.append(distance**2)
            if len(distances) == 50:
                print(distances)
                avg = float(sum(distances))/float(len(distances))
                print("Avg: " + str(avg))
                print("Variance: " + str((float(sum(distancesPow))-len(distances)*avg**2)/(len(distances)-1)))
            else:
                print(len(distances))
            time.sleep(0.2)
        else:
            print(False)
        if status == 1:
            print("")
        elif status == 0:
            print("Over %d" % threshold)
        else:
            print("Read distance error.")

if __name__ == '__main__':
    test()
