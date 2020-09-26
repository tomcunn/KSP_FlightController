####################################
#  KSP Control using Joystick      #
#  pi_ksp_Controller.py            #
#  Cunningham Jan 2018             #
####################################

import smbus
import time
import socket
import sys

from neopixel import *
import argparse

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331,sh1106

#Create the i2c bus
bus = smbus.SMBus(1)

#I/O Extender Chip
IO_DEVICE_ADDRESS = 0x20

#MAX1039 this chip, 8 bit ADC 12 channel
ADC_DEVICE_ADDRESS = 0x65

#OLED Display
DISPLAY_ADDRESS = 0x3C

#Create the display driver

serial = i2c(port=1,address=DISPLAY_ADDRESS)
device = ssd1306(serial)

#LED strip configuration
LED_COUNT = 7
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN,LED_FREQ_HZ,LED_DMA, LED_INVERT, LED_BRIGHTNESS,LED_CHANNEL)
strip.begin()

#Bottom Light (1)
strip.setPixelColor(0,Color(20,0,0))
strip.setPixelColor(1,Color(20,0,0))

#Light (2)
strip.setPixelColor(2,Color(20,0,0))
strip.setPixelColor(3,Color(20,0,0))

#Light (3)
strip.setPixelColor(4,Color(20,0,0))
strip.setPixelColor(5,Color(20,0,0))

#Light (4)
strip.setPixelColor(6,Color(0,0,30))
strip.show()

strip.show()

#Create the socket 
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_address = ('192.168.0.173',10010)
print('Connecting to Server location')
sock.connect(server_address)

joystick_pitch = 0
joystick_yaw = 0
joystick_roll = 0

joystick_x =0
joystick_y =0
joystick_z =0

throttle_value = 0
switch_data = 0
packet_count = 0

with canvas(device) as draw:
	draw.rectangle(device.bounding_box, outline = "white", fill="black")
	draw.text((5,10), "ALL SYSTEMS GO", fill="white")
	draw.text((5,20), "CHECK COMPLETE", fill="white")
####################################################################
# GetJoyStick()
#
# A function call to get the channel from the Joystick
#####################################################################
def GetJoyStick():
    global joystick_pitch
    global joystick_yaw
    global joystick_roll

    global joystick_x
    global joystick_y
    global joystick_z

    global throttle_value

    #channel 0  b'001 0000 1'
    data_0 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x21)
    #channel 1  b'001 0001 1'
    data_1 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x23)
    #channel 2  b'001 0010 1;
    data_2 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x25)

    #channel 3  b'001 0011 1;
    data_3 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x27)
    #channel 4  b'001 0100 1;
    data_4 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x29)
    #channel 5  b'001 0101 1;
    data_5 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x2B)

    #channel 6 is a button that does not have a pull down
    #b'001 0110 1;    

    #channel 7  b'001 0111 1;
    data_6 = bus.read_byte_data(ADC_DEVICE_ADDRESS,0x2F)

    #For debugging  
    #print "%d , %d , %d" %(data_0, data_1, data_2)
    #Need to convert to floats on the other end (data -128)/128.0
    joystick_pitch = data_0
    joystick_yaw   = data_1
    joystick_roll  = data_2

    joystick_x = data_3 
    joystick_y = data_4
    joystick_z = data_5

    throttle_value = data_6

######################################################################
# DataLengthPacket()
#
# Create a packet that always sends 4 Characters with the length 
# of the string up to 999 characters. Always start with "L" so that
# the string can be verified
#####################################################################
def DataLengthPacket(length):
   if length < 10:
	DataLengthString = 'L00' + str(length)
   elif length > 100:
	DataLengthString = 'L' + str(length)
   elif length > 10:
        DataLengthString = 'L0' + str(length)
   return DataLengthString

#####################################################################
# ProcessSwitchInputs()
# 
# Read in all of the switch data and send out store as one big byte
# might as well break it apart on the other end to save space
#
####################################################################
def ProcessSwitchInputs():
   global switch_data
   switch_data = bus.read_byte_data(IO_DEVICE_ADDRESS,0)
   switch_data2 = bus.read_byte_data(IO_DEVICE_ADDRESS,1)
   switch_data = switch_data + switch_data2*256
   print(switch_data)

####################################################################
# DisplayDraw()
#
# Write something to the display
#
#
##################################################################   
def DisplayDraw(value,x,y,z,a,b,c,throttle):
   with canvas(device) as draw:
      draw.rectangle(device.bounding_box, outline= "white", fill="black")
      draw.text((5,10), "Switch Value:",fill="white")
      draw.text((5,20),str(value), fill="white")   
      draw.text((5,30),str(x)+","+str(y)+","+str(z), fill="white")
      draw.text((5,40),str(a)+","+str(b)+","+str(c), fill="white")
      draw.text((5,50),str(throttle), fill="white")
#####################################################################
# MainLoop
#
# This is the main loop of the program 
#
#####################################################################
while(True):
    #Get the Joystick values
    GetJoyStick()
    #Get the Switch values, realize this is polling
    ProcessSwitchInputs()
    #Put Together the data stream
    data_Stream = 'S,'+ str(joystick_pitch) + ',' +str( joystick_yaw) + ',' + str(joystick_roll) + ',' + str(switch_data) + ',' + str(throttle_value) + ',' + str(joystick_x) + ',' + str(joystick_y) + ',' + str(joystick_z) +  ',\n'
    #Compute the length of the stream 
    data_Stream_length = len(data_Stream)
    #Send a packet that contains the length starting the CHAR "L"
    packet_Length_data = str(DataLengthPacket(data_Stream_length))
    sock.sendall(packet_Length_data)   
   # print(packet_Length_data)
    sock.sendall(data_Stream)
    
    if(int(switch_data) & 512):
	strip.setPixelColor(6,Color(0,0,30))
    else:
	strip.setPixelColor(6,Color(0,0,0))

    if(int(switch_data) & 2):
        strip.setPixelColor(4,Color(30,0,0))
        strip.setPixelColor(5,Color(30,0,0))

    else:
        strip.setPixelColor(4,Color(0,30,0))
        strip.setPixelColor(5,Color(0,30,0))


   
    strip.show()     
    # print "%f , %f , %f" %(joystick_pitch, joystick_yaw, joystick_roll) 
   # print DataLengthPacket(data_Stream_length)
    packet_count = packet_count + 1
  
    #DisplayDraw(switch_data,joystick_pitch,joystick_yaw,joystick_roll,joystick_x,joystick_y,joystick_z,throttle_value)
    #print (packet_count)
    time.sleep(0.05) 
print 'connection closed'
sock.close()
