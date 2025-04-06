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
IR_ENTRANCE = 8
IR_EXIT = 3
SERVO_ENTRANCE = 9
SERVO_EXIT = 10

# GUI Class
class SmartParkingApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Smart Parking System")
		self.root.state('zoomed')  # Maximize the window

		# Initialize columns and rows length
		self.column_length = 4
		self.row_length = 1 # set to 2 if the 2nd floor is ready
		self.total_row = 2
		# Store frames and labels
		self.sections = []
		# callback response variables
		self.entrance_response = None
		self.exit_response = None
		self.slots_response = None
		# Initialize UI
		self.init_ui()
		self.init_toll_ui()
		# Configure grid weights
		self.root.grid_columnconfigure(0, weight=1)
		for i in range(1, 5):
			self.root.grid_columnconfigure(i, weight=2)
		for i in range(self.total_row):
			self.root.grid_rowconfigure(i, weight=1)

		self.root.after(1000, self.listener)

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

	def init_toll_ui(self):
		label = tk.Label(self.root, text='Toll Both: -', bg=color_charcoal, fg='white', font=('Arial', 16, 'bold'), height=2)
		label.grid(row=self.total_row, column=0, columnspan=5, sticky="nsew", padx=2, pady=2)
		label.grid_propagate(False)

		self.sections.append((self.root, label))

	def entrance_callback(self, value):
		self.entrance_response = value
	
	def exit_callback(self, value):
		self.exit_response = value
	
	def slots_callback(self, value, args):
		print(f"Slot {args['slot']} status: {value}")

	def listener(self):
		# sensor_entrance = board.get_pin(f'd:{IR_ENTRANCE}:i')
		# sensor_entrance.register_callback(self.entrance_callback)
		# sensor_exit = board.get_pin(f'd:{IR_EXIT}:i')
		# sensor_exit.register_callback(self.exit_callback)
		sensor = board.get_pin(f'd:{IR_ENTRANCE}:i')
		sensor.register_callback(lambda value: self.slots_callback(value, {"slot": 1}))

		
		
	async def open_servo(self, pin, angle):
		servo = board.get_pin(f'd:{pin}:p')
		servo.write(angle)
		await asyncio.sleep(2)
		servo.write(0)


if __name__ == '__main__':
	root = tk.Tk()
	app = SmartParkingApp(root)
	root.mainloop()