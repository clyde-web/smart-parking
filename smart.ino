#include <ArduinoJson.h>

JsonDocument read, write;
String slots[8];
int front_ir = 0;
int exit_ir = 52;

struct ParkingSlot {
	int pinStart;
	int pinEnd;
	bool parked;
	int index;
}

ParkingSlot slots_info[] = {
	{22, 0, false, 1}
	{24, 0, false, 2}
	{26, 0, false, 3}
	{28, 0, false, 4}
};

bool exit_parked = false;


void setup()
{
  Serial.begin(9600);
  pinMode(exit_ir, INPUT);
  
  for (int x = 0; x < 4; x++) {
	pinMode(slots_info[x].pinStart, INPUT);
  }
}

void loop()
{
  read_from_python();
  handle_sensor_reading();
  delay(500);
}

void handle_exit_sensor() {
	if (digitalRead(exit_ir) == 0 && !exit_parked) {
		exit_parked = true;
		write.clear();
		write["cmd"] = "exit";
		serializeJson(write, Serial);
		Serial.println();
	} else if (digitalRead(exit_ir) == 1 && exit_parked) {
		exit_parked = false;
		write.clear();
		write["cmd"] = "clear_toll";
		serializeJson(write, Serial);
		Serial.println();
	}
}

void handle_sensor_reading() {
	for (int s = 0; s < 4; s++) {
		ParkingSlot &slot = slots_info[s];
		int startSensor = digitalRead(slot.pinStart);

		if (startSensor == 0 && slots[s] == "Y" && !slot.parked) {
			slot.parked = true;
			write.clear();
			write["cmd"] = "parking";
			write["context"] = 1;
			serializeJson(write, Serial);
			Serial.println();
		} else if (startSensor == 1 && slots[s] == "N" && slot.parked) {
			slot.parked = false;
			write.clear();
			write["cmd"] = "departed";
			write["context"] = 1;
			serializeJson(write, Serial);
			Serial.println();
		}
	}
	handle_exit_sensor();
}

void read_from_python() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    if (input) {
      read.clear();
      deserializeJson(read, input);
      String command = read["cmd"];

      if (command  == "slots") {
        String context = read["context"];
        int count = 0;
        context.trim();
        while(context.length() > 0) {
          int comma = context.indexOf(",");
          if (comma == -1) {
            slots[count++] = context;
            break;
          } else {
            slots[count++] = context.substring(0, comma);
            context = context.substring(comma+1);
            context.trim();
          }
        }
      } else if (command == "open_entrance") {
        // open servo
      } else if (command == "full_slot") {
        // write to lcd full notification
      } else if (command == "parked") {
        int context = read["context"];
        slots[context-1] = "N";
      } else if (command == "open_exit") {
        int context = read["context"];
        int slot = read["slot"];
        // write the context to lcd2
        // open servo
        slots[slot-1] = "Y";
      }

    }
  }
}
