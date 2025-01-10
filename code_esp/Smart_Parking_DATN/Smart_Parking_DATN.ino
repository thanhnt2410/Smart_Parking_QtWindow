#include<ESP32Servo.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <WiFi.h>
#include <SPI.h>
#include <MFRC522.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>

#define RST_PINin         17          // Configurable, see typical pin layout above
#define SS_PINin          5         // Configurable, see typical pin layout above

#define RST_PINout         16
#define SS_PINout          4

MFRC522 mfrc522_in(SS_PINin, RST_PINin);  // Khởi tạo đối tượng MFRC522
MFRC522 mfrc522_out(SS_PINout, RST_PINout);  // Khởi tạo đối tượng MFRC522

#define BARIEL_IN 33
#define BARIEL_OUT 12

#define A1 2
#define B1 15
#define C1 13

#define A2 14
#define B2 27
#define C2 26

// Chân đầu ra của 2 IC
#define Y1 39  // Đầu ra của IC1
#define Y2 36  // Đầu ra của IC2

// Thông tin mạng WiFi
const char* ssid = "EcoTel Tang 2";           // Thay đổi thành tên WiFi của bạn
const char* password = "ecotel@123";   // Thay đổi thành mật khẩu WiFi của bạn

// Thông tin MQTT
const char* mqtt_server = "052e06039773482e81b963e2a3b42fba.s1.eu.hivemq.cloud"; // Thay đổi thành IP hoặc tên miền broker MQTT của bạn
const int mqtt_port = 8883;                 // Port mặc định của MQTT là 1883
const char* mqtt_user = "smartpark";  // Thay đổi tên tài khoản nếu có
const char* mqtt_pass = "Smartpark123";     // Thay đổi mật khẩu nếu có
const char* mqtt_publish_topic  = "esp32/slots";      // Chọn tên topic phù hợp
const char* mqtt_subscribe_topic = "esp32/detect"; // Topic nhận thông điệp
const char* mqtt_rfid_month_topic = "esp32/rfid_month";         //Topic nhận giá trị rfid
const char* mqtt_rfid_day_topic = "esp32/rfid_day";         //Topic nhận giá trị rfid
const char* mqtt_rfid_send_in = "esp32/rfid_send_in";
const char* mqtt_rfid_send_out = "esp32/rfid_send_out";
const char* mqtt_open_door_in = "esp32/open_door_in";
const char* mqtt_open_door_out = "esp32/open_door_out";

String rfid_month, rfid_day;
long long int last_time_receive_rfid_month =0, last_time_receive_rfid_day = 0, last_time_receive_status_out = 0, last_time_receive_status_in =0;
bool status_out = 0, status_in =0;

// Mảng status và fire_status cho các slot (6 slot)
int status[6] = {0, 0, 0, 0, 0, 0}; // Trạng thái của 6 slot
int fire_status[6] = {0, 0, 0, 0, 0, 0}; // Trạng thái lửa của 6 slot

Servo BarielIn, BarielOut;
LiquidCrystal_I2C lcd(0x27,20,4);

WiFiClientSecure espClient;
PubSubClient client(espClient);

long long int lastTime_SendData, lastTime;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(A1, OUTPUT);  // IC1 S0
  pinMode(B1, OUTPUT);  // IC1 S1
  pinMode(C1, OUTPUT);  // IC1 S2

  pinMode(A2, OUTPUT);  // IC2 S0
  pinMode(B2, OUTPUT);  // IC2 S1
  pinMode(C2, OUTPUT);  // IC2 S2

  pinMode(Y1, INPUT);  // Đọc tín hiệu từ IC1
  pinMode(Y2, INPUT);  // Đọc tín hiệu từ IC2
  BarielIn.attach(BARIEL_IN);
  BarielOut.attach(BARIEL_OUT);
  lcd.init();               
  lcd.backlight();
  lcd.setCursor(3,0);
  lcd.print("Test Servo");
  test_servo();
  lcd.clear();
  lcd.print("Intilialize RFID");

  SPI.begin();            // Khởi động giao tiếp SPI
  mfrc522_in.PCD_Init();     // Khởi tạo module RC522
  mfrc522_out.PCD_Init();
  Serial.println("Đặt thẻ RFID lên đầu đọc...");

  // Kết nối WiFi
  setup_wifi();
  espClient.setInsecure();

  // Kết nối với broker MQTT
  client.setServer(mqtt_server, mqtt_port);
  // Đăng ký callback function để xử lý dữ liệu nhận được
  client.setCallback(mqtt_callback);

  // Đăng ký vào topic để nhận dữ liệu
  reconnect();
  lcd.clear();
}

void loop() {
  // Kiểm tra xem có thông điệp mới không
  client.loop();
  if (!client.connected()) {
    reconnect();
  }
  if(millis()-lastTime_SendData>1000)
  {
    send_data_to_mqtt();
    lastTime_SendData =millis();
  }
  
  RFID_in();
  RFID_out();
  read_sensor();

  if (rfid_month != "") {
    if (millis() - last_time_receive_rfid_month > 5000) {
      rfid_month = "";
    }
  }
  if (rfid_day != "") {
    if (millis() - last_time_receive_rfid_day > 5000) {
      rfid_day = "";
    }
  }
  if (status_in != 0) {
    if (millis() - last_time_receive_status_in > 2000) {
      status_in = 0;
    }
  }
  if (status_out != 0) {
    if (millis() - last_time_receive_status_out > 2000) {
      status_out = 0;
    }
  }
  display_LCD();
  control_door();
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi...");
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
  Serial.println("IP address: ");
  Serial.print(WiFi.localIP());
}

void test_servo()
{
    Bariel_In_Open();
    delay(500);
    Bariel_In_Close();
    delay(500);
    Bariel_Out_Open();
    delay(500);
    Bariel_Out_Close();
    delay(500);
}

void Bariel_In_Open()
{
  Serial.println("In Close");
  for(int pos = 2; pos < 110; pos += 10){ 
        BarielIn.write(pos);
        delay(15);
    }
}
void Bariel_In_Close()
{
  Serial.println("In Open");
  for(int pos = 110; pos>=0; pos-=10) {                           
        BarielIn.write(pos);
        delay(15);
    } 
}

void Bariel_Out_Close()
{
  Serial.println("Out Open");
  for(int pos = -10; pos < 115; pos += 10){ 
        BarielOut.write(pos);
        delay(15);
    }
}
void Bariel_Out_Open()
{
  Serial.println("Out Close");
  for(int pos = 115; pos>=-10; pos-=10) {                           
        BarielOut.write(pos);
        delay(15);
    } 
}
void RFID_in()
{
    if (mfrc522_in.PICC_IsNewCardPresent()) {
    if (mfrc522_in.PICC_ReadCardSerial()) {
      Serial.println("Thẻ RFID in đã được phát hiện!");
      
      // In ra mã UID của thẻ
      Serial.print("UID của thẻ: ");
      String uid = "";
      for (byte i = 0; i < mfrc522_in.uid.size; i++) {
        uid += String(mfrc522_in.uid.uidByte[i], DEC);
      }
      Serial.print(uid);
      send_rfid_in(uid);
      if(uid==rfid_month)
      {
        Serial.println("Bariel In Open for card month");
        lcd.clear();
        lcd.print("Xe vao");
        Bariel_In_Open();
        delay(3000);
        lcd.clear();
        Bariel_In_Close();
      }
      else if(uid==rfid_day)
      {
        Serial.println("Bariel In Open for card day");
        lcd.clear();
        lcd.print("Xe vao");
        Bariel_In_Open();
        delay(3000);
        lcd.clear();
        Bariel_In_Close();
      }
      Serial.println();
      
      mfrc522_in.PICC_HaltA();  // Dừng đọc thẻ
      mfrc522_in.PCD_StopCrypto1();  // Dừng mã hóa
    }
  }
}

void RFID_out()
{
    if (mfrc522_out.PICC_IsNewCardPresent()) {
    if (mfrc522_out.PICC_ReadCardSerial()) {
      Serial.println("Thẻ RFID out đã được phát hiện!");
      
      // In ra mã UID của thẻ
      Serial.print("UID của thẻ: ");
      String uid = "";
      for (byte i = 0; i < mfrc522_out.uid.size; i++) {
        uid += String(mfrc522_out.uid.uidByte[i], DEC);
        // Serial.print(mfrc522_in.uid.uidByte[i], DEC);
        // Serial.print(" ");
      }
      Serial.print(uid);
      send_rfid_out(uid);
      if(uid==rfid_month)
      {
        Serial.println("Bariel out open for card month");
        lcd.clear();
        lcd.print("Xe ra");
        Bariel_Out_Open();
        delay(3000);
        Bariel_Out_Close();
      }
      else if(uid==rfid_day)
      {
        Serial.println("Bariel out close for card month");
        lcd.clear();
        lcd.print("Xe ra");
        Bariel_Out_Open();
        delay(3000);
        Bariel_Out_Close();
      }
      Serial.println();
      
      mfrc522_out.PICC_HaltA();  // Dừng đọc thẻ
      mfrc522_out.PCD_StopCrypto1();  // Dừng mã hóa
    }
  }
}

void reconnect() {
  // Kết nối lại đến broker MQTT nếu bị mất kết nối
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Thử kết nối với MQTT broker
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      Serial.println("Connected to MQTT");
      delay(2000);  // Thêm thời gian trễ
      if (client.subscribe(mqtt_subscribe_topic)) {
        Serial.println("Successfully subscribed to esp32/detect");
      } else {
        Serial.println("Failed to subscribe to esp32/detect");
      }
      if (client.subscribe(mqtt_rfid_month_topic)) {
        Serial.println("Successfully subscribed to " + String(mqtt_rfid_month_topic));
      } else{
        Serial.println("Failed to subscribe to " + String(mqtt_rfid_month_topic));
      }
      if (client.subscribe(mqtt_rfid_day_topic))
      {
        Serial.println("Successfully subscribed to " + String(mqtt_rfid_day_topic));
      }else{
        Serial.println("Failed to subscribe to " + String(mqtt_rfid_day_topic));
      }
      if (client.subscribe(mqtt_open_door_in)) {
        Serial.println("Successfully subscribed to " + String(mqtt_open_door_in));
      } else{
        Serial.println("Failed to subscribe to " + String(mqtt_open_door_in));
      }
      if (client.subscribe(mqtt_open_door_out)) {
        Serial.println("Successfully subscribed to " + String(mqtt_open_door_out));
      } else{
        Serial.println("Failed to subscribe to " + String(mqtt_open_door_out));
      }
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void send_rfid_in(String bien_so)
{
  if (client.publish(mqtt_rfid_send_in, bien_so.c_str())) {
      Serial.println("Message sent successfully: " + bien_so);
    } else {
      Serial.println("Message failed to send: " + bien_so);
    }
    delay(10);
}

void send_rfid_out(String bien_so)
{
  if (client.publish(mqtt_rfid_send_out, bien_so.c_str())) {
      Serial.println("Message sent successfully: " + bien_so);
    } else {
      Serial.println("Message failed to send: " + bien_so);
    }
    delay(10);
}
void send_data_to_mqtt() {

  // Vòng lặp gửi dữ liệu cho từng slot (6 slot)
  for (int i = 0; i < 6; i++) {  // Vòng lặp từ 0 đến 5 (6 phần tử)
    // Chuỗi JSON cho mỗi slot với dấu nháy kép
    String json_message = "{\"spot_id\": \"" + String(i) + "\", ";  // spot_id từ 1 đến 6
    json_message += "\"status\": \"" + String(status[i]) + "\"}";  // status từ mảng status
    // json_message += "\"fire_status\": \"" + String(fire_status[i]) ;  // fire_status từ mảng fire_status
    
    // Gửi thông điệp tới MQTT
    if (client.publish(mqtt_publish_topic, json_message.c_str())) {
      Serial.println("Message sent successfully: " + json_message);
    } else {
      Serial.println("Message failed to send: " + json_message);
    }
    delay(10);
  }
}


// Callback function để xử lý thông điệp nhận được từ topic esp32/detect
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);

  // Chuyển đổi payload thành chuỗi
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // In ra thông điệp nhận được
  Serial.print("Message: ");
  Serial.println(message);

  if (String(topic) == mqtt_subscribe_topic) {
    // Xử lý thông điệp từ topic "esp32/detect"
    Serial.println("Processing data from esp32/detect topic...");
    // Thêm mã xử lý cho topic "esp32/detect"
  }
  else if (String(topic) == mqtt_rfid_month_topic) {
    // Xử lý thông điệp từ topic "esp32/rfid"
    Serial.println("Processing data from esp32/rfid_month_topic...");
    rfid_month = message;
    last_time_receive_rfid_month = millis();
    // Thêm mã xử lý cho topic "esp32/rfid"
  }
  else if (String(topic) == mqtt_rfid_day_topic) {
    // Xử lý thông điệp từ topic "esp32/rfid"
    Serial.println("Processing data from esp32/rfid_day_topic...");
    rfid_day = message;
    last_time_receive_rfid_day = millis();
    // Thêm mã xử lý cho topic "esp32/rfid"
  }
    else if (String(topic) == mqtt_open_door_in) {
    // Xử lý thông điệp từ topic "esp32/rfid"
    Serial.println("Processing data from open_door_in...");
    status_in = 1;
    last_time_receive_status_in = millis();
    // Thêm mã xử lý cho topic "esp32/rfid"
  }
    else if (String(topic) == mqtt_open_door_out) {
    // Xử lý thông điệp từ topic "esp32/rfid"
    Serial.println("Processing data from open_door_out...");
    status_out = 1;
    last_time_receive_status_out = millis();
    // Thêm mã xử lý cho topic "esp32/rfid"
  }
}

void read_sensor() {
  for (int i = 0; i < 6; i++) {
    // Thiết lập các giá trị của S0, S1, S2 để chọn kênh i cho IC2
    digitalWrite(A2, (i & 1));       // S0 = bit 0 của i
    digitalWrite(B2, (i >> 1) & 1);  // S1 = bit 1 của i
    digitalWrite(C2, (i >> 2) & 1);  // S2 = bit 2 của i
    // Đọc tín hiệu từ IC1 (Y1) và IC2 (Y2)
    status[i] = digitalRead(Y2);  // Đọc đầu ra từ IC2
  }
  for (int i = 0; i < 6; i++) {
    Serial.print(status[i]);
    Serial.print(" ");
  }
  Serial.println("");
  delay(1000);
}
void display_LCD()
{
  lcd.setCursor(0,0);
  lcd.print("1:"+String(status[0])+" 2:"+String(status[1])+" 3:"+String(status[2]));
  lcd.setCursor(0,1);
  lcd.print("4:"+String(status[3])+" 5:"+String(status[4])+" 6:"+String(status[5]));
}

void control_door()
{
  Serial.println("Status_in: "+String(status_in)+" status_out: "+String(status_out));
  if(status_in ==1)
  {
    Bariel_In_Open();
    delay(2000);
    Bariel_In_Close();
  }
  else if(status_out==1)
  {
    Bariel_Out_Open();
    delay(2000);
    Bariel_Out_Close();
  }
}