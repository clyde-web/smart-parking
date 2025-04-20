#include <ArduinoJson.h>

JsonDocument read, write;
String slots[8];
int front_ir = 0;
int exit_ir = 52;
int slot1[1] = {22};
int slot2[1] = {53};
int slot3[1] = {50};
// int slot4[1] = {28};

bool slot1_parked = false;
bool slot2_parked = false;
bool exit_parked = false;

// unsigned long frontGateOpenTime = 0;
// unsigned long exitGateOpenTime = 0;

// bool frontGateOpen = false;
// bool exitGateOpen = false;

// bool frontTriggered = false;
// bool exitTriggered = false;

void setup()
{
	Serial.begin(9600);
  pinMode(exit_ir, INPUT);
  pinMode(slot1[0], INPUT);
  pinMode(slot2[0], INPUT);
  pinMode(slot3[0], INPUT);
  // pinMode(slot4[0], INPUT);
}

void loop()
{
  read_from_python();
 if (digitalRead(slot1[0]) == 0 && slots[0] == "Y" && !slot1_parked) {
    slot1_parked = true;
    write.clear();
    write["cmd"] = "parking";
    write["context"] = 1;
    serializeJson(write, Serial);
    Serial.println();
 } else if (digitalRead(slot1[0]) == 1 && slots[0] == "N" && slot1_parked) {
    slot1_parked = false;
    write.clear();
    write["cmd"] = "departed";
    write["context"] = 1;
    serializeJson(write, Serial);
    Serial.println();
 }
 if (digitalRead(slot2[0]) == 0 && slots[1] == "Y" && !slot2_parked) {
    slot2_parked = true;
    write.clear();
    write["cmd"] = "parking";
    write["context"] = 2;
    serializeJson(write, Serial);
    Serial.println();
 } else if (digitalRead(slot2[0]) == 1 && slots[1] == "N" && slot2_parked) {
    slot2_parked = false;
    write.clear();
    write["cmd"] = "departed";
    write["context"] = 2;
    serializeJson(write, Serial);
    Serial.println();
 }
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
 delay(1500);
}

void read_from_python() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    if (input) {
      // read.clear();
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
