#!/usr/bin/python

import RPi.GPIO as GPIO
from RPLCD import CharLCD
import smbus
import math
import time

# Power management registers
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

gyro_scale = 131.0
accel_scale = 16384.0

address = 0x68  # This is the address value read via the i2cdetect command

def read_all():
    raw_gyro_data = bus.read_i2c_block_data(address, 0x43, 6)
    raw_accel_data = bus.read_i2c_block_data(address, 0x3b, 6)

    gyro_scaled_x = twos_compliment((raw_gyro_data[0] << 8) + raw_gyro_data[1]) / gyro_scale
    gyro_scaled_y = twos_compliment((raw_gyro_data[2] << 8) + raw_gyro_data[3]) / gyro_scale
    gyro_scaled_z = twos_compliment((raw_gyro_data[4] << 8) + raw_gyro_data[5]) / gyro_scale

    accel_scaled_x = twos_compliment((raw_accel_data[0] << 8) + raw_accel_data[1]) / accel_scale
    accel_scaled_y = twos_compliment((raw_accel_data[2] << 8) + raw_accel_data[3]) / accel_scale
    accel_scaled_z = twos_compliment((raw_accel_data[4] << 8) + raw_accel_data[5]) / accel_scale

    return (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z)
    
def twos_compliment(val):
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a, b):
    return math.sqrt((a * a) + (b * b))

def get_z_rotation(x,y,z):
    radians = math.atan2(z, dist(x,z))
    return -math.degrees(radians)

def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

bus = smbus.SMBus(1)  # or bus = smbus.SMBus(1) for Revision 2 boards

# Now wake the 6050 up as it starts in sleep mode
bus.write_byte_data(address, power_mgmt_1, 0)

#print "STABILIZOWANIE TEMP 30s"
#time.sleep(30)

now = time.time()

K = 0.2
K1 = 0.8

time_diff = 0.01

(gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()

last_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
last_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
last_z = get_z_rotation(accel_scaled_z, accel_scaled_y, accel_scaled_z)

gyro_offset_x = gyro_scaled_x 
gyro_offset_y = gyro_scaled_y
gyro_offset_z = gyro_scaled_z

gyro_total_x = (last_x) - gyro_offset_x
gyro_total_y = (last_y) - gyro_offset_y
gyro_total_z = (last_z) - gyro_offset_z

lcd = CharLCD(cols=16, rows=2, pin_rs=25, pin_e=24, pins_data=[23, 17, 18, 22],numbering_mode=GPIO.BCM)
GPIO.setwarnings(False)

lcd.write_string(u'PODAJ AZYMUT:')

azymut = input("Podaj azymut z RTK:  ")

gyro_x_cal = []
gyro_y_cal = []
gyro_z_cal = []
tim = 0.0


lcd.clear()
lcd.write_string(u'TRWA KALIBRACJA')

loop = 0.0

for i in range(0, 2999):
    time.sleep(time_diff - 0.005)

    (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()

    gyro_scaled_x -= gyro_offset_x
    gyro_scaled_y -= gyro_offset_y
    gyro_scaled_z -= gyro_offset_z
   
    gyro_x_delta = (gyro_scaled_x * time_diff)
    gyro_y_delta = (gyro_scaled_y * time_diff)
    gyro_z_delta = (gyro_scaled_z * time_diff)

    gyro_total_x += gyro_x_delta
    gyro_total_y += gyro_y_delta
    gyro_total_z += gyro_z_delta
 
    rotation_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    rotation_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    rotation_z = get_z_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)

    last_x = K * (last_x + gyro_total_x) + (K1 * rotation_x)
    last_y = K * (last_y + gyro_total_y) + (K1 * rotation_y)
    last_z = K * (last_z + gyro_total_z) + (K1 * rotation_z)
    
    gyro_x_cal.append(gyro_total_x)
    gyro_y_cal.append(gyro_total_y)
    gyro_z_cal.append(gyro_total_z)

    tim += 0.01

for i in range(0, int(1200.0 / time_diff)):
     
     if (loop == 10.0):
     	lcd.write_string(u"Hello"))
   	 else
   	 	loop +=1.0
   	 	break

    time.sleep(time_diff - 0.005) 
    
    (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()
    
    offset_x = (gyro_x_cal[0] - gyro_x_cal[2998]) / 2999
    offset_y = (gyro_y_cal[0] - gyro_y_cal[2998]) / 2999
    offset_z = (gyro_z_cal[0] - gyro_z_cal[2998]) / 2999
       
    gyro_scaled_x -= gyro_offset_x
    gyro_scaled_y -= gyro_offset_y
    gyro_scaled_z -= gyro_offset_z
    
    gyro_x_delta = (gyro_scaled_x * time_diff)
    gyro_y_delta = (gyro_scaled_y * time_diff)
    gyro_z_delta = (gyro_scaled_z * time_diff)

    gyro_total_x += gyro_x_delta + offset_x
    gyro_total_y += gyro_y_delta + offset_y
    gyro_total_z += gyro_z_delta + offset_z

    rotation_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    rotation_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    rotation_z = get_z_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)

    last_x = K * (last_x + gyro_total_x) + (K1 * rotation_x)
    last_y = K * (last_y + gyro_total_y) + (K1 * rotation_y)
    last_z = K * (last_z + gyro_total_z) + (K1 * rotation_z)

    kat_x = rotation_x
    kat_y = rotation_y
    kat_z = ((gyro_total_z)*0.857142857) - (gyro_z_cal[2998]*0.857142857) - azymut

    timee = (time.time() - now) - tim


    print "TIME: ", "{0:.2f}".format(timee), "DRIFT Z: ", "{0:.5f}".format (offset_z), "X: ", "{0:.2f}".format (kat_x), "Y: ", "{0:.2f}".format (kat_y), " Z: ", ('\x1b[6;30;42m' + "{0:.2f}".format (kat_z) + '\x1b[0m'), " !" 


   	

