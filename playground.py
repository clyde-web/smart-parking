import serial
import time
import json

with serial.Serial("COM4", 9600, timeout=1) as ser:
	time.sleep(2)
	command = {'cmd':'slots','context': "Y,Y,Y,Y"}
	ser.write((json.dumps(command) + '\n').encode());
	while True:
		line = ser.readline().decode().strip()
		if not line:
			continue
		print(f'Received: {line}')