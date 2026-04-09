#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>
#include "HX711.h"

// ===== WiFi & ThingSpeak =====
#define WIFI_SSID "CirkitWifi"
#define WIFI_PASS ""
#define API_KEY "23QZO8VUXRXAB3D9"
const char* serverName = "http://api.thingspeak.com/update";

// ===== Sensor Pins =====
#define DHTPIN 18      
#define DHTTYPE DHT22
#define HX711_DT 4
#define HX711_SCK 5
#define SDA_S3 1      
#define SCL_S3 2      

DHT dht(DHTPIN, DHTTYPE);
HX711 scale;
Adafruit_BMP085 bmp;

float last_temp = 0.0;
unsigned long last_upload = 0;
const unsigned long upload_interval = 15000; // ThingSpeak free limit is ~15s

void setup() {
  Serial.begin(115200);
  
  // Connect WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");

  Wire.begin(SDA_S3, SCL_S3); 
  dht.begin();
  scale.begin(HX711_DT, HX711_SCK);
  scale.set_scale(420.0); 
  scale.tare();

  if (!bmp.begin()) Serial.println("BMP180 Error!");
}

void loop() {
  // 1. Read Sensors
  float t = dht.readTemperature();
  if (!isnan(t)) last_temp = t;
  
  float p = bmp.readPressure();
  float f_kg = scale.get_units(5);

  // 2. Local Display (Serial Monitor)
  Serial.print("Temp: "); Serial.print(last_temp);
  Serial.print(" | Press: "); Serial.print(p);
  Serial.print(" | Load: "); Serial.println(f_kg);

  // 3. Cloud Upload (Every 15 seconds)
  if (millis() - last_upload >= upload_interval) {
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      
      // Construct URL for ThingSpeak
      // field1=Temp, field2=Pressure, field3=Load
      String url = String(serverName) + "?api_key=" + API_KEY + 
                   "&field1=" + String(last_temp) + 
                   "&field2=" + String(p) + 
                   "&field3=" + String(f_kg);
      
      http.begin(url);
      int httpResponseCode = http.GET();
      
      if (httpResponseCode > 0) {
        Serial.print("Cloud Upload Success: ");
        Serial.println(httpResponseCode);
      } else {
        Serial.print("Error on sending GET: ");
        Serial.println(httpResponseCode);
      }
      http.end();
    }
    last_upload = millis();
  }
  
  delay(1000); 
}
