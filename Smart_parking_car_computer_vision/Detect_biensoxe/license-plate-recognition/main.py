import sys
import os
from multiprocessing import Queue, Process
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QGridLayout, QHBoxLayout
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt6.QtCore import QTimer, Qt
import cv2
import random
from rfid_management import RFIDManagementWindow
from webcam import DetectLicensePlate
from mqtt_handler import MQTTHandler
import json
import time

mqtt_sub_topic = "esp32/slots"
mqtt_rfid_topic = "esp32/rfid"
mqtt_host = "192.168.1.14"  # Thay "localhost" bằng địa chỉ IP của server, ví dụ: "192.168.1.100"
mqtt_port = 1883  # Cổng mặc định của MQTT
class ParkingApp(QMainWindow):
    def __init__(self, image):
        super().__init__()
        self.mqtt_handler = MQTTHandler(broke = mqtt_host, port=mqtt_port, topic=mqtt_sub_topic)
        self.mqtt_handler.client.on_message = self.on_mqtt_message
        self.mqtt_handler.client.loop_start()
        self.mqtt_handler.client.subscribe(mqtt_sub_topic)
        print(f"Subscribed to topic: {mqtt_sub_topic}")

        # Danh sách các ô đỗ xe
        self.parking_spots = []
        self.webcam = image
        self.detector = image

        self.setWindowTitle("Parking Management System")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Camera Display
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setFixedSize(640, 480)
        self.layout.addWidget(self.camera_label)

        # Timer for updating camera feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        self.cap = cv2.VideoCapture(0)  # Access default camera
        self.timer.start(30)

        # License Plate Display (Thêm QLabel để hiển thị biển số)
        self.plate_label = QLabel("Detected License Plate: None")
        self.plate_label.setStyleSheet("font-size: 16px; color: white;")
        self.layout.addWidget(self.plate_label)

        # Save Image Button
        self.save_image_button = QPushButton("Save Detected Plate Image")
        self.save_image_button.clicked.connect(self.save_plate_image)
        self.layout.addWidget(self.save_image_button)

        # Parking Status Grid
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)

        # Khởi tạo biến để lưu RFID đã gửi
        self.last_sent_rfid = None
        self.last_sent_time = None

        for i in range(2):  # Hai hàng
            for j in range(3):  # Ba cột
                spot_index = i * 3 + j + 1  # Tính chỉ số slot (1 đến 6)

                # Tạo QLabel để hiển thị tên slot
                slot_name_label = QLabel(f"Slot {spot_index}")
                slot_name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                slot_name_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-right: 5px;")

                # Tạo QLabel để hiển thị trạng thái slot
                spot_label = QLabel()
                spot_label.setFixedSize(100, 100)
                spot_label.setStyleSheet("border: 1px solid black; background-color: lightgray;")

                # Tạo một widget container
                container_widget = QWidget()
                container_layout = QHBoxLayout(container_widget)
                container_layout.addWidget(slot_name_label)
                container_layout.addWidget(spot_label)

                # Thêm widget container vào lưới
                self.grid_layout.addWidget(container_widget, i, j)

                # Lưu trạng thái của slot vào danh sách
                self.parking_spots.append(spot_label)

        # RFID Management Window Button
        self.rfid_window = RFIDManagementWindow()
        self.rfid_button = QPushButton("Manage Monthly Parking Cards")
        self.rfid_button.clicked.connect(self.open_rfid_window)
        self.layout.addWidget(self.rfid_button)

    def update_camera(self):
        """Cập nhật frame từ DetectLicensePlate."""
        ret, frame = self.detector.cap.read()
        if not ret:
            return

        # Phát hiện biển số trên frame
        frame, lp = self.detector.detect_plate(frame)

        # Hiển thị frame
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QPixmap.fromImage(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
        self.camera_label.setPixmap(qt_image)

        # Hiển thị biển số (nếu có)
        if lp:
            self.plate_label.setText(f"Detected License Plate: {lp}")
            # Kiểm tra nếu RFID đã gửi và nếu chưa đủ 3 giây
            current_time = time.time()  # Lấy thời gian hiện tại (giây)
             # Nếu RFID đã được gửi và chưa đủ 3 giây
            if self.last_sent_rfid == lp and (current_time - self.last_sent_time < 3):
                return  # Không gửi lại, chờ đủ 3 giây
            
            rfid = self.rfid_window.get_rfid_from_plate(lp)
            if(rfid):
                print(f"RFID for {lp}: {rfid}")
                self.mqtt_handler.client.publish("esp32/rfid", rfid)
                # Cập nhật lại RFID đã gửi và thời gian gửi
                self.last_sent_rfid = lp
                self.last_sent_time = current_time  # Lưu thời gian gửi
        else:
            self.plate_label.setText("Detected License Plate: None")
    def save_plate_image(self):
        ret, frame = self.cap.read()
        if ret:
            filename = f"plate_{random.randint(1000, 9999)}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved image: {filename}")

    def update_parking_spot(self, spot_label, status, fire_status):
        """Cập nhật trạng thái ô đỗ xe dựa trên dữ liệu."""
        
        # # Xóa dấu X nếu có (để vẽ lại nếu cần)
        # spot_label.clear()

        # Kiểm tra tình trạng cháy
        if fire_status == 1:  # Có cháy
            spot_label.setStyleSheet("background-color: red; border: 1px solid black;")
        else:  # Không có cháy
            spot_label.setStyleSheet("background-color: green; border: 1px solid black;")

        # Kiểm tra có xe hay không
        if status == 1:  # Có xe
            spot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spot_label.setText("VEHICLE")
        else:
            spot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spot_label.setText("NO VEHICLE")
        # Nếu không có xe, không làm gì thêm (X đã bị xóa ở đầu hàm)

    def open_rfid_window(self):
        self.rfid_window.show()

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()

    def on_mqtt_message(self, client, userdata, msg):
        """Callback khi nhận được dữ liệu từ MQTT topic."""
        try:
            print(f"Received raw payload: {msg.payload}")
            # Giải mã dữ liệu JSON từ payload
            data = json.loads(msg.payload.decode())
            print(f"Received data from topic '{msg.topic}': {data}")

            # Kiểm tra và xử lý dữ liệu nhận được
            spot_id = int(data.get("spot_id"))
            status = int(data.get("status"))
            fire_status = int(data.get("fire_status"))

            # Kiểm tra xem spot_id có hợp lệ không
            if 0 <= spot_id < len(self.parking_spots):  # Đảm bảo spot_id hợp lệ
                self.update_parking_spot(self.parking_spots[spot_id], status, fire_status)
            else:
                print(f"Invalid spot_id: {spot_id}. Valid range is 0 to {len(self.parking_spots)-1}.")
        except json.JSONDecodeError:
            print("Received invalid JSON payload.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # mqtt_handler = MQTTHandler( topic=mqtt_topic)
    detector = DetectLicensePlate()
    # vid = cv2.VideoCapture(0)
    main_window = ParkingApp(detector)
    main_window.show()

    # vid.release()
    cv2.destroyAllWindows()
    sys.exit(app.exec())
