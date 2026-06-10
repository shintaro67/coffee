#include <Arduino.h>
#include <ESPmDNS.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <WebServer.h>
#include <HX711.h>

#if ENABLE_THERMOCOUPLES
#include <max6675.h>
#endif

#include "config.h"

enum BrewState : uint8_t {
  STATE_IDLE = 0,
  STATE_WAITING = 1,
  STATE_BREWING = 2,
  STATE_FINISHED = 3
};

struct SharedData {
  float weight = 0.0f;
  float tempKettle = 0.0f;
  float tempDripper = 0.0f;
  float baselineWeight = 0.0f;
  uint32_t elapsedMs = 0;
  uint32_t brewStartMillis = 0;
  bool timerStarted = false;
  BrewState state = STATE_IDLE;
};

SharedData gData;
SemaphoreHandle_t gDataMutex;

HX711 gScale;
#if ENABLE_THERMOCOUPLES
MAX6675 gKettleThermocouple(MAX6675_KETTLE_SCK_PIN, MAX6675_KETTLE_CS_PIN, MAX6675_KETTLE_SO_PIN);
MAX6675 gDripperThermocouple(MAX6675_DRIPPER_SCK_PIN, MAX6675_DRIPPER_CS_PIN, MAX6675_DRIPPER_SO_PIN);
#endif

WiFiUDP gUdp;
WebServer gHttp(HTTP_CONTROL_PORT);
enum PendingAction : uint8_t {
  PENDING_NONE = 0,
  PENDING_TARE_IDLE = 1,
  PENDING_START_WAITING = 2,
};

volatile PendingAction gPendingAction = PENDING_NONE;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(MDNS_HOSTNAME);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected: ");
  Serial.println(WiFi.localIP());
  WiFi.setSleep(false);
}

void sendStartupAnnouncement() {
  const String ip = WiFi.localIP().toString();
  const String payload = String("announce,") + ip + "," + MDNS_HOSTNAME;
  gUdp.beginPacket(UDP_TARGET_IP, UDP_TARGET_PORT);
  gUdp.print(payload);
  gUdp.endPacket();
}

void tareScaleAndResetState(BrewState nextState) {
  xSemaphoreTake(gDataMutex, portMAX_DELAY);
  gData.baselineWeight = 0.0f;
  gData.elapsedMs = 0;
  gData.brewStartMillis = 0;
  gData.timerStarted = false;
  gData.state = nextState;
  xSemaphoreGive(gDataMutex);
}

const char* stateToString(BrewState state) {
  switch (state) {
    case STATE_IDLE:
      return "idle";
    case STATE_WAITING:
      return "waiting";
    case STATE_BREWING:
      return "brewing";
    case STATE_FINISHED:
      return "finished";
    default:
      return "unknown";
  }
}

void handleRoot() {
  Serial.println("HTTP: handleRoot() entry");
  Serial.printf("HTTP: freeHeap=%u\n", ESP.getFreeHeap());
  gHttp.send(200, "application/json", "{\"message\":\"esp32-coffee-control\"}");
  Serial.println("HTTP: handleRoot() exit");
}

void handleTare() {
  Serial.println("HTTP: handleTare() entry");
  Serial.printf("HTTP: freeHeap(before)=%u\n", ESP.getFreeHeap());
  gPendingAction = PENDING_TARE_IDLE;
  Serial.println("HTTP: tare scheduled");
  gHttp.send(200, "application/json", "{\"ok\":true,\"state\":\"idle\"}");
  Serial.printf("HTTP: freeHeap(after)=%u\n", ESP.getFreeHeap());
  Serial.println("HTTP: handleTare() exit");
}

void handleStart() {
  Serial.println("HTTP: handleStart() entry");
  Serial.printf("HTTP: freeHeap(before)=%u\n", ESP.getFreeHeap());
  gPendingAction = PENDING_START_WAITING;
  Serial.println("HTTP: start scheduled");
  gHttp.send(200, "application/json", "{\"ok\":true,\"state\":\"waiting\"}");
  Serial.printf("HTTP: freeHeap(after)=%u\n", ESP.getFreeHeap());
  Serial.println("HTTP: handleStart() exit");
}

void handleStatus() {
  SharedData snapshot;
  xSemaphoreTake(gDataMutex, portMAX_DELAY);
  snapshot = gData;
  xSemaphoreGive(gDataMutex);

  String payload = "{";
  payload += "\"ok\":true,";
  payload += "\"state\":\"" + String(stateToString(snapshot.state)) + "\",";
  payload += "\"elapsed_ms\":" + String(snapshot.elapsedMs) + ",";
  payload += "\"weight\":" + String(snapshot.weight, 2) + ",";
#if ENABLE_THERMOCOUPLES
  payload += "\"temp_kettle\":" + String(snapshot.tempKettle, 2) + ",";
  payload += "\"temp_dripper\":" + String(snapshot.tempDripper, 2);
#else
  payload += "\"temp_kettle\":0.0,";
  payload += "\"temp_dripper\":0.0"; // ← セミコロンをダブルクォーテーションに修正
#endif
  payload += "}";

  gHttp.send(200, "application/json", payload);
}

void setupHttpServer() {
  gHttp.on("/", HTTP_GET, handleRoot);
  gHttp.on("/tare", HTTP_POST, handleTare);
  gHttp.on("/start", HTTP_POST, handleStart);
  gHttp.on("/status", HTTP_GET, handleStatus);
  gHttp.begin();
  Serial.println("HTTP server started");
}

void taskWeightAndTelemetry(void* parameter) {
  // ループ前の初期化
  Serial.println("[Task] Weight & Telemetry stream optimized for 80Hz.");

  for (;;) {
    // 1. 非同期リクエストの処理（HTTP側からの割り込み）
    if (gPendingAction != PENDING_NONE) {
      const PendingAction pendingAction = gPendingAction;
      gPendingAction = PENDING_NONE;

      if (pendingAction == PENDING_TARE_IDLE) {
        Serial.printf("HTTP: applying pending action -> %s\n", stateToString(STATE_IDLE));
        gScale.tare(1); // 最少サンプリングでブロッキングを最小化
        tareScaleAndResetState(STATE_IDLE);
      } else if (pendingAction == PENDING_START_WAITING) {
        Serial.printf("HTTP: applying pending action -> %s\n", stateToString(STATE_WAITING));
        xSemaphoreTake(gDataMutex, portMAX_DELAY);
        gData.elapsedMs = 0;
        gData.brewStartMillis = 0;
        gData.timerStarted = false;
        gData.state = STATE_WAITING;
        xSemaphoreGive(gDataMutex);
      }
    }

    // 2. 重量サンプリング
    // ★重要: HX711が80Hzモードの場合、この get_units(1) が「12.5msに1回」のペースで
    // データの準備が整った瞬間に正確にブロックを解除してくれます。
    const float currentWeight = gScale.get_units(1);

    const uint32_t now = millis();

    // データが取れた瞬間にミューテックスを最小限の時間だけロック
    xSemaphoreTake(gDataMutex, portMAX_DELAY);
    gData.weight = currentWeight;

    if (gData.state == STATE_WAITING) {
      const float gain = gData.weight - gData.baselineWeight;
      if (gain >= START_TRIGGER_GRAMS) {
        gData.timerStarted = true;
        gData.brewStartMillis = now;
        gData.elapsedMs = 0;
        gData.state = STATE_BREWING;
      }
    }

    if (gData.timerStarted) {
      gData.elapsedMs = now - gData.brewStartMillis;
    }

    // UDP送信用のスナップショットをコピーして、ミューテックスは即座に解放！
    SharedData snapshot = gData;
    xSemaphoreGive(gDataMutex);

    // 3. UDPストリーミング送信（インターバル制限なし、PCのノンブロッキング受信へ直撃）
    String line = String(snapshot.elapsedMs / 1000.0f, 3) + ",";
    line += String(snapshot.weight, 2);

#if ENABLE_THERMOCOUPLES
    line += ",";
    line += String(snapshot.tempKettle, 2) + ",";
    line += String(snapshot.tempDripper, 2) + ",";
    line += String(stateToString(snapshot.state));
#endif

    gUdp.beginPacket(UDP_TARGET_IP, UDP_TARGET_PORT);
    gUdp.print(line);
    gUdp.endPacket();

    // 4. 他の低優先度タスク（HTTPサーバー等）にCPUを譲る
    // vTaskDelay(2) や delay(2) のような固定の「眠り」を排除し、
    // 最少の1ミリ秒だけCPUを解放して、すぐに次の get_units(1) の待ち状態に移行します。
    vTaskDelay(pdMS_TO_TICKS(1));
  }
}

#if ENABLE_THERMOCOUPLES
void taskTemperatureRead(void* parameter) {
  uint32_t lastTempRead = 0;

  for (;;) {
    const uint32_t now = millis();

    if (now - lastTempRead >= TEMP_SAMPLE_INTERVAL_MS) {
      const float kettle = gKettleThermocouple.readCelsius();
      const float dripper = gDripperThermocouple.readCelsius();

      xSemaphoreTake(gDataMutex, portMAX_DELAY);
      gData.tempKettle = kettle;
      gData.tempDripper = dripper;
      lastTempRead = now;
      xSemaphoreGive(gDataMutex);
    }

    vTaskDelay(pdMS_TO_TICKS(10));
  }
}
#endif

void setup() {
  Serial.begin(115200);
  delay(200);

  gDataMutex = xSemaphoreCreateMutex();

  gScale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  gScale.set_scale(HX711_CALIBRATION_FACTOR);
  gScale.tare();

  connectWiFi();
  if (MDNS.begin(MDNS_HOSTNAME)) {
    MDNS.addService("http", "tcp", HTTP_CONTROL_PORT);
    Serial.print("mDNS hostname: http://");
    Serial.print(MDNS_HOSTNAME);
    Serial.print(".local:");
    Serial.println(HTTP_CONTROL_PORT);
  } else {
    Serial.println("mDNS startup failed");
  }
  gUdp.begin(UDP_TARGET_PORT);
  sendStartupAnnouncement();
  setupHttpServer();

  xTaskCreatePinnedToCore(
      taskWeightAndTelemetry,
      "TaskWeightTelemetry",
      4096,
      nullptr,
      2,
      nullptr,
      1);

#if ENABLE_THERMOCOUPLES
  xTaskCreatePinnedToCore(
      taskTemperatureRead,
      "TaskTemperature",
      4096,
      nullptr,
      1,
      nullptr,
      0);
#else
  // Temperature acquisition is planned for a later phase.
  // MAX6675 task is intentionally disabled in weight-only mode.
#endif
}

void loop() {
  gHttp.handleClient();
  delay(2);
}