import tkinter as tk
import asyncio
from pyfirmata2 import Arduino

board = Arduino(Arduino.AUTODETECT)
board.samplingOn()

# Global Variables
color_blue = '#559bfb'
color_charcoal = '#3E505B'
color_red = '#F2426E'
color_warning = '#FD9722'
# GPIO Pins
IR_ENTRANCE = 4
IR_EXIT = 2
SERVO_ENTRANCE = 5
SERVO_EXIT = 3

# GUI Class
class SmartParkingApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Smart Parking System")
		self.root.state('zoomed')  # Maximize the window
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close event

		# Initialize columns and rows length
		self.column_length = 4
		self.row_length = 1 # TODO: set to 2 if the 2nd floor is ready
		self.total_row = 2
		# Store frames and labels
		self.sections = []
		# Board variables
		self.slot1_start = board.get_pin('d:13:i')
		self.slot1_end = board.get_pin('d:12:i')
		self.slot2_start = board.get_pin('d:11:i')
		self.slot2_end = board.get_pin('d:10:i')
		self.slot3_start = board.get_pin('d:9:i')
		self.slot3_end = board.get_pin('d:8:i')
		self.slot4_start = board.get_pin('d:7:i')
		self.slot4_end = board.get_pin('d:6:i')
		# callback response variables
		self.db_requires_update = False
		self.slots_response = {}
		self.queue = []
		# Initialize UI
		self.init_ui()
		self.init_toll_ui()
		# Configure grid weights
		self.root.grid_columnconfigure(0, weight=1)
		for i in range(1, 5):
			self.root.grid_columnconfigure(i, weight=2)
		for i in range(self.total_row):
			self.root.grid_rowconfigure(i, weight=1)
		
		self.listener()

	# Grid UI
	# Initialize the UI with labels and frames
	def init_ui(self):
		for row in range(self.row_length):
			floor_label_text = 'Ground Floor' if row == 0 else '2nd Floor'
			floor_label = tk.Label(self.root, text=floor_label_text, bg=color_charcoal, fg='white', font=('Arial', 16, 'bold'))
			floor_label.grid(row=row, column=0, sticky="nsew", padx=2, pady=2)

			for col in range(4):
				color_index = row * 4 + col
				color = color_blue

				# Create a frame for each section
				frame = tk.Frame(self.root, bg=color)
				frame.grid(row=row, column=col+1, sticky="nsew", padx=2, pady=2)

				# Create a label inside each section
				section_label = tk.Label(frame, text=f"Slot {color_index+1}", bg=color, fg='white', font=('Arial', 14))
				section_label.pack(expand=True)

				# Store section data for future changes
				self.sections.append((frame, section_label))

	# Toll UI
	def init_toll_ui(self):
		label = tk.Label(self.root, text='Toll Booth: -', bg=color_charcoal, fg='white', font=('Arial', 16, 'bold'), height=2)
		label.grid(row=self.total_row, column=0, columnspan=5, sticky="nsew", padx=2, pady=2)
		label.grid_propagate(False)

		self.sections.append((self.root, label))

	# Handle the callback for the entrance gate
	def entrance_callback(self, value):
		# TODO: add servo motor when done configuring
		if value is not None and value is False:
			self.slot1_start.register_callback(lambda value: self.slots_callback(value, {'name': 0, 'status': 'start'}))
			self.slot1_end.register_callback(lambda value: self.slots_callback(value, {'name': 0, 'status': 'end'}))
			self.slot2_start.register_callback(lambda value: self.slots_callback(value, {'name': 1, 'status': 'start'}))
			self.slot2_end.register_callback(lambda value: self.slots_callback(value, {'name': 1, 'status': 'end'}))
			self.slot3_start.register_callback(lambda value: self.slots_callback(value, {'name': 2, 'status': 'start'}))
			self.slot3_end.register_callback(lambda value: self.slots_callback(value, {'name': 2, 'status': 'end'}))
			self.slot4_start.register_callback(lambda value: self.slots_callback(value, {'name': 3, 'status': 'start'}))
			self.slot4_end.register_callback(lambda value: self.slots_callback(value, {'name': 3, 'status': 'end'}))

	# Handle the callback for the exit gate
	# This is where you can add the logic to calculate the toll fee
	def exit_callback(self, value):
		# TODO: add servo motor when done configuring
		if value is not None and value is False:
			toll_index = len(self.sections) - 1
			frame, label = self.sections[toll_index]  # get the frame and label for the toll booth
			label.config(text="Toll Booth: PHP 200.00", bg=color_charcoal)
	
	# Handle the callback for the slots
	def slots_callback(self, value, args):
		# if the args['name'] is not in the slots_response dictionary, create it
		if args['name'] not in self.slots_response:
			self.slots_response[args['name']] = {'status': {'start': None, 'end': None}}
		self.slots_response[args['name']]['status'][args['status']] = value # assign the detected value to the start or end key
		slot = self.slots_response[args['name']]['status']
		frame, label = self.sections[int(args['name'])] # get the frame and label for the slot

		# this condition check if the both ir sensors detected a car
		# if yes it will to the database to set the status as taken
		if slot['start'] is False and slot['end'] is False:
			# code here to save to database to set the status as taken
			self.db_requires_update = True
			self.slots_response[args['name']]['parking_flg'] = True
			frame.config(bg=color_red)
			label.config(text="Taken", bg=color_red)
		# this condition check for the maintenance status
		# if only 1 of the ir sensors detected a car
		elif slot['start'] is False and slot['end'] is True or slot['start'] is True and slot['end'] is False:
			# code here to save to database to set the status as maintenance
			self.db_requires_update = True
			frame.config(bg=color_warning)
			label.config(text="Maintenance", bg=color_warning)
		# this condition check if the parked car is leaving the parking lot
		# then add it to the queue
		elif slot['start'] is True and slot['end'] is True and 'parking_flg' in self.slots_response[args['name']] and self.slots_response[args['name']]['parking_flg'] is True:
			# code here to save to database to set the status as available
			self.db_requires_update = True
			self.queue.append(int(args['name']))
		# default
		else:
			frame.config(bg=color_blue)
			label.config(text=f"Slot {args['name']+1}", bg=color_blue)
		
		if self.db_requires_update is True:
			# code here to update the database with the new status
			self.db_requires_update = False

	# Listen to the IR sensors for entrance and exit
	def listener(self):
		sensor_entrance = board.get_pin(f'd:{IR_ENTRANCE}:i')
		sensor_entrance.register_callback(self.entrance_callback)
		sensor_exit = board.get_pin(f'd:{IR_EXIT}:i')
		sensor_exit.register_callback(self.exit_callback)
		
	# Handle the entry and exit gates servo motors
	async def open_servo(self, pin, angle):
		servo = board.get_pin(f'd:{pin}:s')
		servo.write(angle)
		await asyncio.sleep(2)
		servo.write(0)
	
	# Clean up and close the application
	def on_close(self):
		board.samplingOff()
		self.root.quit()
		self.root.destroy()

if __name__ == '__main__':
	root = tk.Tk()
	app = SmartParkingApp(root)
	root.mainloop()