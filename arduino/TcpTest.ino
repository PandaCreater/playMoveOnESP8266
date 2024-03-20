#include <WiFi.h>
#include "ESP32-HUB75-MatrixPanel-I2S-DMA.h"

// Panel configuration
#define PANEL_RES_X 64  // Number of pixels wide of each INDIVIDUAL panel module.
#define PANEL_RES_Y 64  // Number of pixels tall of each INDIVIDUAL panel module.

#define NUM_ROWS 1  // Number of rows of chained INDIVIDUAL PANELS
#define NUM_COLS 1  // Number of INDIVIDUAL PANELS per ROW

#define SERPENT true
#define TOPDOWN false
#define PANEL_CHAIN 1

// placeholder for the matrix object
MatrixPanel_I2S_DMA* dma_display = nullptr;

const char* ssid = "shareVLAN";
const char* password = "123456789";
const char* host = "192.168.110.124";  // The IP of the computer running the Python server
constexpr int port = 13235;            // Port number must match the one in the Python script

char incomingPacket[1024];  // 接收udp数据的数组
uint16_t displayColor[512];
int part = 0;

WiFiClient client;

void setup() {
  Serial.begin(115200);
  delay(10);

  Serial.println("connecting WiFi");
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Connection successful, print IP address
  Serial.println("");
  Serial.println("WiFi connected");

  Serial.println("connecting TCP");
  // Attempt to connect to the server with the configured host and port
  while (!client.connect(host, port)) {
    delay(3000);
    Serial.print(".");
  }
  Serial.println("Connected to server");
  delay(500);

  HUB75_I2S_CFG::i2s_pins _pins = {
    25,  //R1_PIN,
    26,  //G1_PIN,
    27,  //B1_PIN,
    14,  //R2_PIN,
    12,  //G2_PIN,
    13,  //B2_PIN,
    23,  //A_PIN,
    19,  //B_PIN,
    5,   //C_PIN,
    17,  //D_PIN,
    18,  //E_PIN,
    4,   //LAT_PIN,
    15,  //OE_PIN,
    16,  //CLK_PIN
  };
  HUB75_I2S_CFG mxconfig(
    PANEL_RES_X,  // Module width
    PANEL_RES_Y,  // Module height
    PANEL_CHAIN,  // chain length
    _pins         // pin mapping -- uncomment if providing own custom pin mapping as per above.
  );

  // OK, now we can create our matrix object
  dma_display = new MatrixPanel_I2S_DMA(mxconfig);

  // let's adjust default brightness to about 75%
  dma_display->setBrightness8(96);  // range is 0-255, 0 - 0%, 255 - 100%

  // Allocate memory and start DMA display
  if (not dma_display->begin())
    Serial.println("****** !KABOOM! I2S memory allocation failed ***********");

  displayStr("now start");
  delay(1000);
}

void loop() {
  // Check the WiFi connection status
  if (client.connected()) {
      if (client.available()) {
        client.readBytes(incomingPacket, 1024);
        for (int j = 0; j < 512; j++) {
          displayColor[j] = incomingPacket[j * 2] << 8 | incomingPacket[j * 2 + 1];
        }
        dma_display->drawRGBBitmap(0, 8 * part, displayColor, 64, 8);
        part++;
        if (part >= 8) {
          part = 0;
        }
      }
    }
  else {
    Serial.println("disconnect TCP");
    // Attempt to connect to the server with the configured host and port
    Serial.println("connecting TCP");
    while (!client.connect(host, port)) {
      delay(3000);
      Serial.print(".");
    }
  }
}

// 显示文字
void displayStr(String text) {
  dma_display->clearScreen();
  dma_display->setTextColor(dma_display->color565(255, 255, 255));
  dma_display->setCursor(0, 0);
  dma_display->print(text);
  delay(1000);
}