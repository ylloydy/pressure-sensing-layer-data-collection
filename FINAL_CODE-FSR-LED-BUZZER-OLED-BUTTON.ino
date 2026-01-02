// --- FSR406 + LED + Buzzer + OLED (SH1106) + Button ---
// Hardware: Arduino Nano ESP32

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- Pin Definitions ---
const int fsrPin = A0;
const int ledPin = 11;
const int buzzerPin = 12;
const int buttonPin = 10;

// --- Constants ---
const float Rfixed = 10000.0;
const float Vin = 3.3;
const int ADCmax = 4095;

// --- FSR406 Calibration ---
const float C = 6.0;
const float S = 1.5;

// --- Threshold ---
const float forceThreshold = 15.0;

// --- State Variables ---
bool systemOn = false;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 300;

bool plotMode = true;   // IMPORTANT: must be true for Python

void setup() {
  pinMode(fsrPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);

  Serial.begin(115200);
  delay(400);

  // Flush old serial buffer (fixes 2-second delay)
  while (Serial.available()) Serial.read();

  // --- OLED Init ---
  if (!display.begin(0x3C, true)) {
    Serial.println(F("OLED failed"));
    for (;;);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.println("FSR406 Sensor");
  display.println("Press Button");
  display.display();
  delay(1500);
}

void loop() {
  handleButton();

  if (!systemOn) {
    display.clearDisplay();
    display.setTextSize(2);
    display.setCursor(20, 25);
    display.println("OFF");
    display.display();

    digitalWrite(ledPin, LOW);
    digitalWrite(buzzerPin, LOW);
    noTone(buzzerPin);

    delay(100);
    return;
  }

  // --- ACTIVE MODE ---
  int adc = analogRead(fsrPin);
  if (adc <= 1) adc = 1;

  float Rfsr = Rfixed * ((float)ADCmax / (float)adc - 1.0);
  float logR = log10(Rfsr);
  float forceN = pow(10, (C - logR) / S);

  // ---- SERIAL OUTPUT (only clean numeric output) ----
  if (plotMode) {
    Serial.println(forceN);     // Python expects ONLY this!
  }

  // ---- OLED Output ----
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("FSR406 Force Sensor");
  display.println("-------------------");
  display.setTextSize(2);
  display.setCursor(0, 25);

  if (forceN >= forceThreshold) {
    display.println("Flip Now!");
    digitalWrite(ledPin, HIGH);
    digitalWrite(buzzerPin, HIGH);
  } else {
    display.print(forceN, 2);
    display.println(" N");
    digitalWrite(ledPin, LOW);
    digitalWrite(buzzerPin, LOW);
  }

  display.display();

  delay(100);  // EXACT MATCH to Python interval (100 ms)
}

// --- Button Debounce ---
void handleButton() {
  static bool lastButtonState = HIGH;
  bool currentState = digitalRead(buttonPin);

  if (currentState != lastButtonState && (millis() - lastDebounceTime) > debounceDelay) {
    lastDebounceTime = millis();
    if (currentState == LOW) {
      systemOn = !systemOn;
    }
  }
  lastButtonState = currentState;
}
