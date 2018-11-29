import krpc
import time
import socket
import sys
from Flight_Controller_Buttons import buttons

#Create the connection with the game
print('Starting Server')
conn = krpc.connect(name='FlightControllerConnection',address='127.0.0.1', rpc_port=10000, stream_port=10001)
print(conn.krpc.get_status().version)
vessel = conn.space_center.active_vessel
print('server complete')

#Create the connection to the controller
print('starting socket connection to controller')
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('192.168.0.173', 10015))
sock.listen(1)
connection,address = sock.accept()
print('Connection complete')
stage_pushbutton_previous = 0
#########################################################
# ProcessDataStream()
#
# Take the packet of data and break into the individual
# components
#
#########################################################
def ProcessDataStream(data_packet):
	global stage_pushbutton_previous
	split_data = data_packet.split(',')
	pitch_raw = split_data[1]
	roll_raw = split_data[2]
	yaw_raw = split_data[3]
	button_raw = split_data[4]
	throttle_raw = split_data[5]
	x_raw = split_data[6]
	y_raw = split_data[7]
	z_raw = split_data[8]
	#print(str(pitch_raw) + ':' + str(roll_raw) + ':' + str(yaw_raw) + ':' + str(button_raw))
	#print(pitch_raw)
	#convert int to floats between 1 and -1
	roll_float  = (float(roll_raw) - 128)/128.0
	pitch_float = (float(pitch_raw) - 128)/128.0
	yaw_float   = (float(yaw_raw) - 128)/128.0
	throttle_float = (float(throttle_raw)/190)-(40/190)
	
	x_float = (float(x_raw) - 128)/128.0
	y_float = (float(y_raw) - 128)/128.0
	z_float = (float(z_raw) - 128)/128.0
	#print(str(roll_float) + ':' + str(pitch_float) + ':' + str( yaw_float) + ':' + str(throttle_float))
	
	#process the Button presses
	#STAGING
	if(int(button_raw) & buttons.STAGE_TOGGLE):
		stage_toggle = 1
	else:
		stage_toggle = 0
		
	if(int(button_raw) & buttons.STAGE_PUSHBUTTON):
		stage_pushbutton = 1
	else:
		stage_pushbutton = 0
	#SAS TOGGLE
	if(int(button_raw) & buttons.SAS_TOGGLE):
		vessel.control.sas = True
	else:
		vessel.control.sas = False
	#RCS_TOGGLE 
	if(int(button_raw) & buttons.RCS_TOGGLE):
		vessel.control.rcs = True
		#only update x,y,z if RCS is active
		vessel.control.right = x_float
		vessel.control.up = y_float
		vessel.control.forward = z_float
	else:
		vessel.control.rcs = False
	#GEAR_TOGGLE
	if(int(button_raw) & buttons.GEAR_TOGGLE):
		vessel.control.gear = True
	else:
		vessel.control.gear = False
	
	#PARACHUTE
	if((int(button_raw) & buttons.PARA_A_TOGGLE) and vessel.control.parachutes == False):
		vessel.control.parachutes = True
	
	#Logic for staging
	GoForStage = 0
	if(stage_toggle):
		if(stage_pushbutton and not stage_pushbutton_previous):
			GoForStage = 1
	
	stage_pushbutton_previous = stage_pushbutton
	
	if(GoForStage):
		vessel.control.activate_next_stage()
		GoForStage = 0
	#Send data to the game
	vessel.control.roll  =  yaw_float
	vessel.control.pitch =  pitch_float
	vessel.control.yaw   =  roll_float
	
	vessel.control.throttle = throttle_float
	
#############################################################
#
#    Main Loop
#
############################################################	
	#Start processing the incoming data
while True:
	#Read in the length of the string
	buf = connection.recv(1)
	#print(buf)
	#The start Char should be an "L" = 'd'76
	start_char = str(buf[0])
	#print(start_char)
	if start_char == '76':
		#print('found start character')
		#Read in the 3 digit length, start at digit one read until digit 4
		buf = connection.recv(3)
		data_length_RX = int(buf[0:3])
		#Receive the data stream
		data_RX = connection.recv(data_length_RX)
		#print(data_RX)
		#Process the data stream
		ProcessDataStream(str(data_RX))
connection.close()


#altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
#g_force = conn.add_stream(getattr,vessel.flight(), 'g_force')
