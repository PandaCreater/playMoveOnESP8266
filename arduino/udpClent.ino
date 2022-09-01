#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include "SSD1306Wire.h"

SSD1306Wire display(0x3c, SDA, SCL); 

// 网络用户名和密码 自行修改
const char* ssid = "wifi 账号";
const char* password = "wifi 密码";

WiFiUDP Udp;
unsigned int localUdpPort = 4210;  // udp的监听点
char incomingPacket[1024];  // 接收udp数据的数组

void setup()
{
  // 初始化显示
  display.init();
  display.setContrast(255);
  Serial.begin(115200);
  Serial.println();

  Serial.printf("Connecting to %s ", ssid);

  String ssidStr = ssid;
  String message = "Connecting to" + ssidStr;

  displayStr(message);

  // 连接wifi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
    message = message + ".";
    displayStr(message);
  }

  Serial.println(" connected");

  // 开启udp监听
  Udp.begin(localUdpPort);
  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.localIP().toString().c_str(), localUdpPort);
  displayStr("Now listening at IP " + WiFi.localIP().toString() + ", UDP port:  4210");
}

void loop()
{
  // 获取udp数据长度
  int packetSize = Udp.parsePacket();
  if (packetSize)
  {
    // 读取数据
    int len = Udp.read(incomingPacket, 1024);
    // 清空屏幕
    display.clear();
    int row = 0;
    int col = 0;
    // 根据数据byte，一个byte 8个像素点 转换成二进制，1为点亮 

    unsigned char byte;// Read from file
    unsigned char mask = 1; // Bit mask
    unsigned char bit;

    for (int i = 0; i< len; i++) {
      byte = incomingPacket[i];
      col += 8;
      if (col > 128) {
        col = 8;
        row += 1;
      }

      // byte转bit
      for (int j = 0; j < 8; j++) {
          bit = (byte & (mask << j)) != 0;
          if (bit) {
            display.setPixel(col - j, row);
          }
      }
    }
    // 显示
    display.display();
  }
}

// 显示文字
void displayStr(String text) {  
  display.clear();
  display.drawStringMaxWidth(0, 0, 128, text);
  display.display();
}
