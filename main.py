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
		self.row_length = 1 # set to 2 if the 2nd floor is ready
		self.total_row = 2
		# Store frames and labels
		self.sections = []
		# callback response variables
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
		label = tk.Label(self.root, text='Toll Both: -', bg=color_charcoal, fg='white', font=('Arial', 16, 'bold'), height=2)
		label.grid(row=self.total_row, column=0, columnspan=5, sticky="nsew", padx=2, pady=2)
		label.grid_propagate(False)

		self.sections.append((self.root, label))

	# Handle the callback for the entrance gate
	def entrance_callback(self, value):
		if value is not None and value is False:
			# Our predefined ir sensors
			irs = [
				{'slot': 0, 'start': 12, 'end': 13},
				{'slot': 1, 'start': 11, 'end': 10},
				{'slot': 2, 'start': 9, 'end': 8},
				{'slot': 3, 'start': 7, 'end': 6}
			]
			for ir in irs:
				start_slot = board.get_pin(f'd:{ir['start']}:i')
				end_slot = board.get_pin(f'd:{ir['end']}:i')
				start_slot.register_callback(lambda value: self.slots_callback(value, {'name': ir['slot'], 'status': 'start'}))
				end_slot.register_callback(lambda value: self.slots_callback(value, {'name': ir['slot'], 'status': 'end'}))

	# Handle the callback for the exit gate
	# This is where you can add the logic to calculate the toll fee
	def exit_callback(self, value):
		self.exit_response = value
	
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
			self.slots_response[args['name']]['parking_flg'] = True
			frame.config(bg=color_red)
			label.config(text="Taken", bg=color_red)
		# this condition check for the maintenance status
		# if only 1 of the ir sensors detected a car
		elif slot['start'] is False and slot['end'] is True and slot['start'] is True and slot['end'] is False:
			# code here to save to database to set the status as maintenance
			frame.config(bg=color_warning)
			label.config(text="Maintenance", bg=color_warning)
		# this condition check if the parked car is leaving the parking lot
		# then add it to the queue
		elif slot['start'] is True and slot['end'] is True and 'parking_flg' in self.slots_response[args['name']] and self.slots_response[args['name']]['parking_flg'] is True:
			# code here to save to database to set the status as available
			self.queue.append(int(args['name']))

	# Listen to the IR sensors for entrance and exit
	def listener(self):
		sensor_entrance = board.get_pin(f'd:{IR_ENTRANCE}:i')
		sensor_entrance.register_callback(self.entrance_callback)
		sensor_exit = board.get_pin(f'd:{IR_EXIT}:i')
		sensor_exit.register_callback(self.exit_callback)
		#if self.exit_response is not None and self.exit_response == False:
			# asyncio.create_task(self.open_servo(SERVO_EXIT, 65))
			# code here to calculate the toll fee according to the timestamp saved in the database
		
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