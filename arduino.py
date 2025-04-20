import tkinter as tk
from database import *
import threading
import serial
import time
import json
import datetime

# Global Variables
color_blue = '#559bfb'
color_charcoal = '#3E505B'
color_red = '#F2426E'
color_warning = '#FD9722'
# Predefined Variables
AVAILABLE = 1
OCCUPIED = 2
MAINTENANCE = 3
CMD_ENTRANCE = 'entrance'
CMD_EXIT = 'exit'
CMD_PARKING = 'parking'
CMD_DEPARTED = 'departed'
CMD_CLEAR_TOLL = 'clear_toll'

class SmartParkingApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Smart Parking System")
		self.root.state("zoomed")
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		# Grid UI config
		self.column_length = 4
		self.row_length = 2 # TODO: set to 2 if the 2nd floor is ready
		self.total_row = 2
		# Store frames and labels
		self.sections = []
		# Initialize the interface
		self.init_interface()
		# Configure grid layout
		self.root.grid_columnconfigure(0, weight=1)
		for i in range(1, 5):
			self.root.grid_columnconfigure(i, weight=2)
		for i in range(self.total_row):
			self.root.grid_rowconfigure(i, weight=1)

		# Initialize the database tables and default slots
		# TODO: comment this out when the database is ready
		init_tables()
		default_slots()
		# TODO: comment this out when the database is ready
		self.slots = get_slots()

		# Start the serial data reading in a separate thread
		self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
		self.serial_thread.start()

	def init_interface(self):
		for row in range(self.row_length):
			# Create a label for the floor
			floor_label_text = 'Ground Floor' if row == 0 else '2nd Floor'
			floor_label = tk.Label(self.root, text=floor_label_text, font=('Arial', 16, 'bold'), bg=color_charcoal, fg='white')
			floor_label.grid(row=row, column=0, sticky='nsew', padx=2, pady=2)

			# Sections loop
			for col in range(self.column_length):
				index = row * self.column_length + col
				# Create a frame for each section
				frame = tk.Frame(self.root, bg=color_blue)
				frame.grid(row=row, column=col+1, sticky='nsew', padx=2, pady=2)
				# Create a label for each section
				section_label = tk.Label(frame,text=f"Slot {index+1}", bg=color_blue, fg='white', font=('Arial', 14))
				section_label.pack(expand=True)
				# Store section data for modifying slots status
				self.sections.append((frame, section_label))
		
		# Create a label for the toll booth
		toll_label = tk.Label(self.root, text="Toll: "+chr(0x20B1)+"0.00", bg=color_charcoal, fg='white', font=('Arial', 16, 'bold'), height=2)
		toll_label.grid(row=self.total_row, column=0, columnspan=self.column_length+1, sticky='nsew', padx=2, pady=2)
		toll_label.grid_propagate(False)
		# Store toll label for updating toll amount
		self.sections.append((self.root, toll_label))
	
	# Update UI
	def update_interface(self):
		for slot in self.slots:
			frame, label = self.sections[int(slot[0])-1]
			color = (
					color_blue if slot[1] == AVAILABLE else 
					color_red if slot[1] == OCCUPIED else
					color_warning
				)
			text = (
					f'Slot {slot[0]}' if slot[1] == AVAILABLE else 
					'Taken' if slot[1] == OCCUPIED else
					'Warning'
				)
			frame.config(bg=color)
			label.config(text=text, bg=color)

	# Read serial data from Arduino
	def read_serial_data(self):
		try:
			with serial.Serial("COM4", 9600, timeout=1) as ser:
				time.sleep(2)
				self.root.after(0, self.update_interface)
				status_string = ", ".join(
					"Y" if slot[1] == AVAILABLE else "N" if slot[1] == OCCUPIED else "M"
					for slot in self.slots
				)
				command = {"cmd": "slots", "context": status_string}
				self.send_command(ser, command)
				while True:
					line = ser.readline().decode('utf-8').strip()
					if not line:
						continue
					try:
						data = json.loads(line)
						if 'cmd' in data:
							if data['cmd'] == CMD_ENTRANCE:
								# Get the available slots
								available = get_available_slots()
								if available > 0:
									# Open the entrance gate
									command = {"cmd": "open_entrance"}
									self.send_command(ser, command)
								else:
									# No available slots, do not open the gate
									command = {"cmd": "full_slot"}
									self.send_command(ser, command)
							if data['cmd'] == CMD_EXIT:
								# Open the exit gate and display the toll fee
								id = get_log_history_that_are_away()
								if id is not None:
									_, label = self.sections[len(self.sections)-1]
									fee, slot = calculate_toll(id)
									label.config(text=f"Toll: {chr(0x20B1)}{fee:.2f}")
									command = {"cmd": "open_exit", "context": fee, "slot": slot}
									self.send_command(ser, command)
									self.slots = get_slots()
									self.root.after(0, self.update_interface)
							if data['cmd'] == CMD_PARKING:
								# Update the slot status in the database
								slot = data['context']
								for row in self.slots:
									if row[0] == slot and row[1] == AVAILABLE:
										update_slot(slot, OCCUPIED)
										log_slot_history(slot)
										# Update the UI for the slot
										self.slots = get_slots()
										self.root.after(0, self.update_interface)
										command = {"cmd": "parked", "context": slot}
										self.send_command(ser, command)
										break
							if data['cmd'] == CMD_DEPARTED:
								# Update the slot status in the database
								slot = data['context']
								for row in self.slots:
									if row[0] == slot and row[1] == OCCUPIED:
										id = get_log_history_id(slot)
										if id is not None:
											update_log_history_to_away(id)
										break
							if data['cmd'] == CMD_CLEAR_TOLL:
								_, label = self.sections[len(self.sections)-1]
								label.config(text="Toll: "+chr(0x20B1)+"0.00")
					except json.JSONDecodeError as e:
						print(f"JSON error: {e} | line was: {line}")

		except serial.SerialException as e:
			print(f"Serial error: {e}")

	def send_command(self, ser, cmd):
		ser.write((json.dumps(cmd) + '\n').encode())
	
	# Handle closing the window application
	def on_closing(self):
		self.root.quit()
		self.root.destroy()

if __name__ == "__main__":
	root = tk.Tk()
	app = SmartParkingApp(root)
	root.mainloop()