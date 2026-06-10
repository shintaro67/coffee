#pragma once

// 0: weight-only mode (temperature is planned; currently disabled)
// 1: use dual MAX6675 thermocouples
#define ENABLE_THERMOCOUPLES 0

// Wi-Fi settings
static const char* WIFI_SSID = "Buffalo-2G-8570";
static const char* WIFI_PASSWORD = "4favfe5es4x3c";
static const char* MDNS_HOSTNAME = "coffee-esp32";

// UDP telemetry target (PC)
static const char* UDP_TARGET_IP = "192.168.11.7";
static const uint16_t UDP_TARGET_PORT = 5005;

// HTTP control server port on ESP32
static const uint16_t HTTP_CONTROL_PORT = 8080;

// HX711 pins
static const int HX711_DOUT_PIN = 25;
static const int HX711_SCK_PIN = 26;
static const float HX711_CALIBRATION_FACTOR = -1087.33f;

// MAX6675 pins (example GPIO assignment; adjust to your wiring)
// Sensor 1 (kettle): SCK, CS, SO
static const int MAX6675_KETTLE_SCK_PIN = 18;
static const int MAX6675_KETTLE_CS_PIN = 5;
static const int MAX6675_KETTLE_SO_PIN = 19;

// Sensor 2 (dripper): SCK, CS, SO
static const int MAX6675_DRIPPER_SCK_PIN = 18;
static const int MAX6675_DRIPPER_CS_PIN = 17;
static const int MAX6675_DRIPPER_SO_PIN = 19;

// Sampling intervals
static const uint32_t WEIGHT_SAMPLE_INTERVAL_MS = 20;   // prioritize weight updates
static const uint32_t TEMP_SAMPLE_INTERVAL_MS = 220;    // MAX6675 conversion window
static const uint32_t TELEMETRY_INTERVAL_MS = 100;      // UDP send cadence

// Brew trigger threshold after start command
static const float START_TRIGGER_GRAMS = 5.0f;
