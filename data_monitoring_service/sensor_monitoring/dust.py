#!/usr/bin/python
# -*- coding: utf-8 -*-

import wiringpi as wp

Clock = 27
Address = 28
DataOut = 29

COV_RATIO = 0.2  # ug/mmm /mv
NO_DUST_VOLTAGE = 400  # mv
SYS_VOLTAGE = 3300
D0 = 0
S0 = 1

flag_first  = 0
sum = 0
_buff = []
def filter(m):
    global flag_first, sum, _buff
    if flag_first == 0:
        flag_first = 1

        for i in range(0, 10):
            _buff.append(m)
            sum += m
        return m
    else:
        sum -= _buff[0]
        for i in range(0, 9):
            _buff[i] = _buff[i+1]
        _buff[9] = m
        sum += m
        return sum / 10.0

def adc_read(channel):
    LSB, MSB = 0,0
    channel = channel << 4

    for i in range(0, 4):
        if channel & 0x80:
            wp.digitalWrite(Address, 1)
        else:
            wp.digitalWrite(Address, 0)
        wp.digitalWrite(Clock, 1)
        wp.digitalWrite(Clock, 0)
        channel = channel << 1

    for i in range(0, 6):
        wp.digitalWrite(Clock, 1)
        wp.digitalWrite(Clock, 0)

    wp.delayMicroseconds(15)
    for i in range(0, 2):
        wp.digitalWrite(Clock, 1)
        MSB <<= 1
        if wp.digitalRead(DataOut):
            MSB |= 0x1
        wp.digitalWrite(Clock, 0)

    for i in range(0, 8):
        wp.digitalWrite(Clock, 1)
        LSB <<= 1
        if wp.digitalRead(DataOut):
            LSB |= 0x1
        wp.digitalWrite(Clock, 0)

    value = MSB
    value <<= 8
    value |= LSB
    return value

def read():
    wp.digitalWrite(S0, wp.GPIO.HIGH)   #  lay tin hieu dien ap
    wp.delayMicroseconds(280)           # chờ 280us
    adcvalue = adc_read(6)
    wp.digitalWrite(S0, wp.GPIO.LOW)    # ket thuc lay tin hieu

    # loc tin hieu
    # print("adcvalue before: {}".format(adcvalue))
    adcvalue = filter(adcvalue)   # loc tin hieu
    # print("adcvalue after filter: {}".format(adcvalue))
    voltage = (SYS_VOLTAGE / 1024.0) * adcvalue * 11
    # print('Voltage After: {}'.format(voltage))
    if voltage >= NO_DUST_VOLTAGE:
        voltage -= NO_DUST_VOLTAGE
        density = voltage * COV_RATIO
    else:
        density = 0
    return  density

def set_up_GPIO():
    wp.wiringPiSetup()
    wp.pinMode(DataOut, wp.GPIO.INPUT)
    wp.pullUpDnControl(DataOut, wp.GPIO.PUD_UP)
    wp.pinMode(Clock, wp.GPIO.OUTPUT)
    wp.pinMode(Address, wp.GPIO.OUTPUT)
    wp.pinMode(D0, wp.GPIO.INPUT)
    wp.digitalWrite(D0, wp.GPIO.LOW)
    wp.pinMode(S0, wp.GPIO.OUTPUT)


if __name__ == '__main__':
    set_up_GPIO()

    while True:
        density = read()
        print("Do bui: " + str(density)+ "\n")
        wp.delay(1000)