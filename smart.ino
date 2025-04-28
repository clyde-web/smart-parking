#include <ArduinoJson.h>
#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

JsonDocument read, write;
LiquidCrystal_I2C lcd(0x27, 16, 2);
// LiquidCrystal_I2C lcd2(adrss, 16, 2); // Uncomment if toll lcd change address done and replce {adrss} with the address
Servo front_gate;
Servo exit_gate;

String slots[8];
int front_ir = 53;
int exit_ir = 52;

struct ParkingSlot {
	int pinStart;
	int pinEnd;
	bool parked;
	int index;
}

ParkingSlot slots_info[] = {
	{22, 23, false, 1},
	{24, 25, false, 2},
	{26, 27, false, 3},
	{28, 29, false, 4}
}; // Add more pins for the 2nd floor

bool exit_parked = false;
bool entrance_parked = false;
bool refresh_lcd = false;


void setup()
{
  Serial.begin(9600);
  pinMode(front_ir, INPUT);
  pinMode(exit_ir, INPUT);

  lcd.init();
  lcd.backlight();
  init_lcd();
  // lcd2.init();
  // lcd2.backlight();
  // init_lcd2();

  front_gate.attach(9);
  exit_gate.attach(10);
  close_entrance_gate();
  close_exit_gate();
  
  for (int x = 0; x < 4; x++) {
	  pinMode(slots_info[x].pinStart, INPUT);
	  // pinMode(slots_info[x].pinEnd, INPUT); // Uncomment if ready for double detection
  }
}

void loop()
{
  read_from_python();
  handle_sensor_reading();
  if (refresh_lcd) {
    slot_display_lcd();
    refresh_lcd = false;
  }
  delay(500);
}

void init_lcd() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(" Parking System ");
  lcd.setCursor(0, 1);
  lcd.print("    Waiting...  ");
}

void init_lcd2() {
  lcd2.clear();
  lcd2.setCursor(0, 0);
  lcd2.print("    Waiting...  ");
}

void lcd_full() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   Parking Full  ");
}

void write_toll(String amount) {
  int textLength = amount.length();
  int startPosition = (16 - textLength) / 2;
  lcd2.clear();
  lcd2.setCursor(0, 0);
  lcd2.print("   Please Pay    ");
  lcd2.setCursor(startPosition, 1);
  lcd2.print(amount);
}

void slot_display_lcd() {
  lcd.clear();
  lcd.setCursor(0, 0);
  // Ground Floor
  lcd.print("S1:");
  lcd.print(slots[0]);
  for (int i=0; i<3; i++) {
    int index = (i*2)+3;
    lcd.print("S" + String(index) + ":");
    lcd.print(slots[index]);
  }
  // 2nd Floor
  lcd.setCursor(0, 1);
  lcd.print("S2:");
  lcd.print(slots[1]);
  for (int i=4; i<7; i++) {
    int index = (i-2)*2;
    lcd.print("S" + String(index) + ":");
    lcd.print(slots[index]);
  }
}

void open_entrance_gate() {
  front_gate.write(110);
}

void close_entrance_gate() {
  front_gate.write(0);
}

void open_exit_gate() {
  exit_gate.write(180);
}

void close_exit_gate() {
  exit_gate.write(80);
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
    init_lcd2();
    delay(300);
    close_exit_gate();
	}
}

void handle_entrance_sensor() {
  if (digitalRead(front_ir) == 0 && !entrance_parked) {
    entrance_parked = true;
    write.clear();
    write["cmd"] = "entrance";
    serializeJson(write, Serial);
    Serial.println();
  } else if (digitalRead(front_ir) == 1 && entrance_parked) {
    entrance_parked = false;
    delay(300);
    close_entrance_gate();
  }
}

void handle_sensor_reading() {

  handle_entrance_sensor();
	handle_exit_sensor();

	for (int s = 0; s < 4; s++) {
		ParkingSlot &slot = slots_info[s];
		int startSensor = digitalRead(slot.pinStart);
    // int endSensor = digitalRead(slot.pinEnd); // Uncomment if ready for double detection
    bool isDetected = startSensor == 0; // && endSensor == 0; // Uncomment if ready for double detection
    bool isDeparted = startSensor == 1;// && endSensor == 1; // Uncomment if ready for double detection

		if (isDetected && slots[s] == "Y" && !slot.parked) {
			slot.parked = true;
			write.clear();
			write["cmd"] = "parking";
			write["context"] = slot.index;
			serializeJson(write, Serial);
			Serial.println();
		} else if (isDeparted && slots[s] == "N" && slot.parked) {
			slot.parked = false;
			write.clear();
			write["cmd"] = "departed";
			write["context"] = slot.index;
			serializeJson(write, Serial);
			Serial.println();
		}

	}

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
        refresh_lcd = true;
      } else if (command == "open_entrance") {
        open_entrance_gate();
      } else if (command == "full_slot") {
        lcd_full();
      } else if (command == "parked") {
        int context = read["context"];
        slots[context-1] = "N";
        refresh_lcd = true;
      } else if (command == "open_exit") {
        String context = read["context"];
        int slot = read["slot"];
        slots[slot-1] = "Y";
        // write_toll(context); // Uncomment if ready for toll
        open_exit_gate();
        refresh_lcd = true;
      }

    }
  }
}
