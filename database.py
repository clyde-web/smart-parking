import sqlite3
import datetime

def db_connect():
	return sqlite3.connect('database.db')

def init_tables():
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("DROP TABLE IF EXISTS slots;")
	cursor.execute("DROP TABLE IF EXISTS slots_history;")
	cursor.execute("CREATE TABLE slots (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, status INTEGER DEFAULT 1);")
	cursor.execute("CREATE TABLE slots_history (id INTEGER PRIMARY KEY AUTOINCREMENT, slot_id INTEGER, time_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP, time_out TIMESTAMP, status INTEGER DEFAULT 1);")
	connection.commit()
	connection.close()

def default_slots():
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 1');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 2');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 3');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 4');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 5');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 6');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 7');")
	cursor.execute("INSERT INTO slots (name) VALUES ('Slot 8');")
	connection.commit()
	connection.close()

def get_available_slots():
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("SELECT COUNT(id) as total_available FROM slots WHERE status = 1;")
	slots = cursor.fetchone()
	connection.close()
	return slots[0] if slots is not None else 0

def get_slots():
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("SELECT id, status FROM slots ORDER BY id ASC;")
	slots = cursor.fetchall()
	connection.close()
	return slots

def update_slot(id,status):
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("UPDATE slots SET status = ? WHERE id = ?;", (status,id,))
	connection.commit()
	connection.close()

def log_slot_history(slot_id):
	connection = db_connect()
	cursor = connection.cursor()
	now = datetime.datetime.now()
	cursor.execute("INSERT INTO slots_history (slot_id, time_in) VALUES (?, ?);", (slot_id,now,))
	connection.commit()
	connection.close()

def get_log_history_id(slot_id):
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("SELECT id FROM slots_history WHERE slot_id = ? AND status = 1;", (slot_id,))
	id = cursor.fetchone()
	connection.close()
	return id[0] if id is not None else None

def update_log_history_to_away(id):
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("UPDATE slots_history SET status = 2 WHERE id = ?", (id,))
	connection.commit()
	connection.close()

def get_log_history_that_are_away():
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("SELECT id FROM slots_history WHERE status = 2 ORDER BY id ASC;")
	id = cursor.fetchone()
	connection.close()
	return id[0] if id is not None else None

def calculate_toll(id):
	connection = db_connect()
	cursor = connection.cursor()
	cursor.execute("SELECT time_in, slot_id FROM slots_history WHERE id = ?;", (id,))
	result = cursor.fetchone()
	entry_time = result[0]
	slot_id = result[1]

	if entry_time:
		now = datetime.datetime.now()
		parse_time = datetime.datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')
		duration = (now - parse_time).total_seconds() / 60 
		fee = round(duration * 5, 2) # Assuming Php5.00 per minute
		cursor.execute("UPDATE slots SET status = 1 WHERE id = ?;", (slot_id,))
		cursor.execute("UPDATE slots_history SET time_out = ?, status = 3 WHERE id = ? AND status = 2;", (now,id,))
		connection.commit()
	else:
		fee = 0

	connection.close()
	return fee, slot_id
