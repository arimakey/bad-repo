#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>

// ==========================================
// CONFIGURACIÓN USUARIO
// ==========================================
const char* ssid = "Kale";
const char* password = "varkosjs5";

// Servidor Render
const char* server_url = "https://bad-repo.onrender.com/api/upload_frame";

// ==========================================
// CONFIGURACIÓN CÁMARA
// ==========================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  config.frame_size   = FRAMESIZE_QVGA; 
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Error init cámara");
    while(true) delay(100);
  }
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Conectado!");
}

void syncTime() {
  // SSL necesita hora correcta
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Sync Hora");
  time_t now = time(nullptr);
  while (now < 1600000000) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println(" OK");
}

void setup() {
  Serial.begin(115200);
  initCamera();
  connectWiFi();
  syncTime(); 
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    return;
  }

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) return;

  HTTPClient http;
  
  // Conexión segura (Render fuerza HTTPS)
  http.begin(server_url);
  
  // Headers importantes para enviar raw binary
  http.addHeader("Content-Type", "image/jpeg");
  
  Serial.printf("Enviando %u bytes a %s\n", fb->len, server_url);

  // Enviar POST con el buffer de la imagen
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  if (httpResponseCode > 0) {
    Serial.printf("POST OK, codigo: %d\n", httpResponseCode);
    String payload = http.getString();
    Serial.println(payload);
  } else {
    Serial.printf("Error POST: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();
  esp_camera_fb_return(fb);

  // Pequeño delay para no saturar y mantener ~2 FPS
  // 500ms = 2 frames por segundo
  delay(500); 
}
