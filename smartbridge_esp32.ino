#include <HX711.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>

// ===== WiFi =====
#define WIFI_SSID "CirkitWifi"
#define WIFI_PASS ""

// ===== ThingSpeak =====
#define API_KEY "23QZO8VUXRXAB3D9"
const char* serverName = "http://api.thingspeak.com/update";

// ===== PIN CONFIG =====
#define SDA_S3 8
#define SCL_S3 9
#define DHTPIN 18
#define HX711_DT 4
#define HX711_SCK 5

// ===== OBJECTS =====
DHT dht(DHTPIN, DHT22);
HX711 scale;
Adafruit_BMP085 bmp;

// ===== VARIABLES =====
float calibration_factor = 1677721;   // ✅ CALIBRATED VALUE
float last_temp = 0.0;
unsigned long last_upload = 0;

void setup() {
  Serial.begin(115200);

  // I2C
  Wire.begin(SDA_S3, SCL_S3);

  // Sensors
  dht.begin();
  bmp.begin();

  // HX711
  scale.begin(HX711_DT, HX711_SCK);

  Serial.println("Remove all weight...");
  delay(3000);

  scale.set_scale();   // Reset scale
  scale.tare();        // Zero calibration
  delay(2000);

  Serial.println("Tare done!");

  // Apply calibration factor
  scale.set_scale(calibration_factor);

  Serial.println("System Ready!");

  // ===== WiFi Connect =====
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
}

void loop() {
  // ===== READ SENSORS =====
  float t = dht.readTemperature();
  if (!isnan(t)) last_temp = t;

  float p = bmp.readPressure();

  // Load cell (averaged)
  float weight = scale.get_units(15);

  // ===== SERIAL OUTPUT =====
  Serial.print("Temeperature: ");
  Serial.print(last_temp);
  Serial.print(" C | Pressure: ");
  Serial.print(p);
  Serial.print(" Pa | Load: ");
  Serial.print(weight, 2);
  Serial.println(" kg");

  // ===== THINGSPEAK UPLOAD =====
  if (millis() - last_upload >= 16000) {
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;

      String url = String(serverName) + "?api_key=" + API_KEY +
                   "&field1=" + String(last_temp) +
                   "&field2=" + String(p) +
                   "&field3=" + String(weight);

      http.begin(url);
      int code = http.GET();

      if (code == 200)
        Serial.println("ThingSpeak Updated!");
      else
        Serial.println("Upload Failed");

      http.end();
    }
    last_upload = millis();
  }

  delay(2000);
}

