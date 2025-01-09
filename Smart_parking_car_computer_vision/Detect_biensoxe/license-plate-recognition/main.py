import sys
import os
from multiprocessing import Queue, Process
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QGridLayout, QHBoxLayout, QTabWidget
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QScreen
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
import cv2
import random
from rfid_management import RFIDManagementWindow
from webcam import DetectLicensePlate
from mqtt_handler import MQTTHandler
import json
import time
import threading
from doanh_thu import DoanhThu  # Import RevenueManagementTab

class MQTTThread(threading.Thread):
    def __init__(self, mqtt_handler):
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.daemon = True

    def run(self):
        self.mqtt_handler.start()

mqtt_sub_topic = "esp32/slots"
# mqtt_rfid_topic = "esp32/rfid"

class ParkingApp(QMainWindow):
    # Tín hiệu để thông báo reset
    reset_rfid_in_signal = pyqtSignal()
    reset_rfid_out_signal = pyqtSignal()
    def __init__(self, image):
        super().__init__()
        print("Khoi tao APP Parking")

        # Danh sách các ô đỗ xe
        self.parking_spots = []
        self.webcam = image
        self.detector = image

        self.setWindowTitle("Parking Management System")
        # self.setGeometry(100, 100, 1920, 1080)

        # Lấy kích thước màn hình
        screen = QApplication.primaryScreen()  # Lấy màn hình chính
        screen_geometry = screen.geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())

        self.central_widget = QTabWidget()  # Đổi từ QWidget sang QTabWidget
        self.setCentralWidget(self.central_widget)

        # self.layout = QVBoxLayout(self.central_widget)

        # Create camera and parking layout tab
        self.parking_tab = QWidget()
        self.init_parking_tab()
        self.central_widget.addTab(self.parking_tab, "Parking Management")

        # Add RevenueManagementTab
        self.revenue_tab = DoanhThu()
        self.central_widget.addTab(self.revenue_tab, "Doanh thu")

                # Khởi tạo MQTTHandler
        self.mqtt_handler = MQTTHandler()
        self.mqtt_handler.client.on_message = self.on_mqtt_message

        # Chạy MQTTHandler trong một luồng riêng
        self.mqtt_thread = MQTTThread(self.mqtt_handler)
        self.mqtt_thread.start()

        print(f"Subscribed to topic: {self.mqtt_handler.sub_topic}")

        # Tạo QTimer cho reset
        self.clear_timer_in = QTimer(self)
        self.clear_timer_in.setSingleShot(True)
        self.clear_timer_in.timeout.connect(self.clear_rfid_in)

        self.clear_timer_out = QTimer(self)
        self.clear_timer_out.setSingleShot(True)
        self.clear_timer_out.timeout.connect(self.clear_rfid_out)

        # Kết nối tín hiệu với timer start
        self.reset_rfid_in_signal.connect(lambda: self.clear_timer_in.start(3000))
        self.reset_rfid_out_signal.connect(lambda: self.clear_timer_out.start(3000))

    def init_parking_tab(self):
        # self.parking_tab_layout = QVBoxLayout(self.parking_tab)

        # # Camera Display
        # self.camera_label = QLabel("Camera Feed")
        # self.camera_label.setFixedSize(640, 480)
        # self.parking_tab_layout.addWidget(self.camera_label)
        # # Đảm bảo căn giữa layout trong tab
        # # self.parking_tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # # Create horizontal layout for buttons and camera
        # self.controls_layout = QHBoxLayout()
        
        # # Open door in button
        # self.open_door_in_button = QPushButton("Open Door In")
        # self.open_door_in_button.clicked.connect(self.open_door_in)
        # self.controls_layout.addWidget(self.open_door_in_button)

        # # Open door out button
        # self.open_door_out_button = QPushButton("Open Door Out")
        # self.open_door_out_button.clicked.connect(self.open_door_out)
        # self.controls_layout.addWidget(self.open_door_out_button)

        # # Add the camera and control buttons to the main layout
        # self.parking_tab_layout.addLayout(self.controls_layout)
        self.parking_tab_layout = QVBoxLayout(self.parking_tab)

        # Create horizontal layout for camera and control buttons
        self.main_layout = QHBoxLayout()

        # Camera Display (increase size)
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setFixedSize(800, 600)  # Increase the size of the camera display
        self.main_layout.addWidget(self.camera_label)

        # Create another layout for control buttons (Open Door In and Open Door Out)
        self.controls_layout = QVBoxLayout()

        # Open door in button (resize it)
        self.open_door_in_button = QPushButton("Open Door In")
        self.open_door_in_button.setFixedSize(150, 40)  # Set smaller size for the button
        self.open_door_in_button.clicked.connect(self.open_door_in)
        self.controls_layout.addWidget(self.open_door_in_button)

        # Open door out button (resize it)
        self.open_door_out_button = QPushButton("Open Door Out")
        self.open_door_out_button.setFixedSize(150, 40)  # Set smaller size for the button
        self.open_door_out_button.clicked.connect(self.open_door_out)
        self.controls_layout.addWidget(self.open_door_out_button)

        # Add the control buttons layout to the main layout
        self.main_layout.addLayout(self.controls_layout)

        # Add the main layout (camera + buttons) to the parking tab layout
        self.parking_tab_layout.addLayout(self.main_layout)

        # Timer for updating camera feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        self.cap = cv2.VideoCapture(0)  # Access default camera
        self.timer.start(30)

        # License Plate Display (Thêm QLabel để hiển thị biển số)
        self.plate_label = QLabel("Detected License Plate: None")
        self.plate_label.setStyleSheet("font-size: 16px; color: white;")
        self.parking_tab_layout.addWidget(self.plate_label)

        # Save Image Button
        self.save_image_button = QPushButton("Save Detected Plate Image")
        self.save_image_button.clicked.connect(self.save_plate_image)
        self.parking_tab_layout.addWidget(self.save_image_button)

        # Parking Status Grid
        self.grid_layout = QGridLayout()
        self.parking_tab_layout.addLayout(self.grid_layout)
        
        #Khoi tao bien nhan gia tri rfid tu esp32
        self.rfid_esp32_in = None
        self.rfid_esp32_out = None

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
        self.parking_tab_layout.addWidget(self.rfid_button)
        

    def update_camera(self):
        """Cập nhật frame từ DetectLicensePlate."""
        ret, frame = self.detector.cap.read()
        if not ret:
            return
        
        # Lưu trữ frame mới nhất
        self.latest_frame = frame

        # Phát hiện biển số trên frame
        frame, lp = self.detector.detect_plate(frame)

        # Hiển thị frame
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QPixmap.fromImage(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
        self.camera_label.setPixmap(qt_image)

        # Hiển thị biển số (nếu có)
        if lp and lp != "unknown":
            self.plate_label.setText(f"Detected License Plate: {lp}")
            # Kiểm tra nếu RFID đã gửi và nếu chưa đủ 3 giây
            current_time = time.time()  # Lấy thời gian hiện tại (giây)
             # Nếu RFID đã được gửi và chưa đủ 3 giây
            if self.last_sent_rfid == lp and (current_time - self.last_sent_time < 3):
                return  # Không gửi lại, chờ đủ 3 giây
            
            rfid_month = self.rfid_window.get_rfid_month_from_plate(lp)
            rfid_day = self.rfid_window.get_rfid_day_from_plate(lp)
            if(rfid_month):
                print(f"RFID for {lp}: {rfid_month}")
                self.mqtt_handler.client.publish("esp32/rfid_month", rfid_month)
                
                # Cập nhật lại RFID đã gửi và thời gian gửi
                self.last_sent_rfid = lp
                self.last_sent_time = current_time  # Lưu thời gian gửi

            if(rfid_day):
                print(f"RFID for {lp}: {rfid_day}")
                self.mqtt_handler.client.publish("esp32/rfid_day", rfid_day)
                
                # Cập nhật lại RFID đã gửi và thời gian gửi
                self.last_sent_rfid = lp
                self.last_sent_time = current_time  # Lưu thời gian gửi
            # else:
                if self.rfid_esp32_out != None:
                    self.rfid_window.daily_ticket_manager.update_time_out(self.rfid_esp32_out, lp)
            else:
                if self.rfid_esp32_in != None:
                    self.rfid_window.daily_ticket_manager.handle_rfid_message(self.rfid_esp32_in, lp)
            
        else:
            self.plate_label.setText("Detected License Plate: None")
    def save_plate_image(self):
        # Đường dẫn tới thư mục lưu ảnh
        directory = "images"
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Tạo tên file và đường dẫn đầy đủ
        filename = os.path.join(directory, f"plate_{random.randint(1000, 9999)}.jpg")
        # Lưu ảnh vào thư mục
        if hasattr(self, 'latest_frame') and self.latest_frame is not None:
            cv2.imwrite(filename, self.latest_frame)
            print(f"Saved image: {filename}")
        else:
            print("Error: No frame available to save.")

    def update_parking_spot(self, spot_label, status):
        """Cập nhật trạng thái ô đỗ xe dựa trên dữ liệu."""
        
        # # Xóa dấu X nếu có (để vẽ lại nếu cần)
        # spot_label.clear()

        # Kiểm tra tình trạng cháy
        if status == 0:  # Có xe
            spot_label.setStyleSheet("background-color: green; border: 1px solid black;")
        else:  # Không có cháy
            spot_label.setStyleSheet("background-color: grey; border: 1px solid black;")


    def open_rfid_window(self):
        self.rfid_window.show()

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()

    def on_mqtt_message(self, client, userdata, msg):
        """Callback khi nhận được dữ liệu từ MQTT topic."""
        try:
            print(f"Received raw payload: {msg.payload}")
            print(f"Received data from topic '{msg.topic}': {msg.payload.decode()}")
            if msg.topic == "esp32/rfid_send_in":
                # Xử lý chuỗi từ topic esp32/send_rfid
                self.rfid_esp32_in = msg.payload.decode().strip()  # Loại bỏ khoảng trắng
                print(f"RFID received: {self.rfid_esp32_in}")
                # Phát tín hiệu để khởi động timer
                self.reset_rfid_in_signal.emit()

            elif msg.topic == "esp32/rfid_send_out":
                # Xử lý chuỗi từ topic esp32/send_rfid
                self.rfid_esp32_out = msg.payload.decode().strip()  # Loại bỏ khoảng trắng
                print(f"RFID received: {self.rfid_esp32_out}")
                # Phát tín hiệu để khởi động timer
                self.reset_rfid_out_signal.emit()

            elif msg.topic == "esp32/slots":
                # Giải mã dữ liệu JSON từ payload
                data = json.loads(msg.payload.decode())
                # print(f"Received data from topic '{msg.topic}': {data}")

                # Kiểm tra và xử lý dữ liệu nhận được
                spot_id = int(data.get("spot_id"))
                status = int(data.get("status"))

                # Kiểm tra xem spot_id có hợp lệ không
                if 0 <= spot_id < len(self.parking_spots):  # Đảm bảo spot_id hợp lệ
                    self.update_parking_spot(self.parking_spots[spot_id], status)
                else:
                    print(f"Invalid spot_id: {spot_id}. Valid range is 0 to {len(self.parking_spots)-1}.")
        except json.JSONDecodeError:
            print("Received invalid JSON payload.")

    def clear_rfid_in(self):
        self.rfid_esp32_in = None
        print("Cleared self.rfid_esp32_in")

    def clear_rfid_out(self):
        self.rfid_esp32_out = None
        print("Cleared self.rfid_esp32_out")

    def open_door_in(self):
        """Publish a value of 1 to the 'esp32/open_door_in' topic."""
        print("Opening door in...")
        self.mqtt_handler.client.publish("esp32/open_door_in", 1)

    def open_door_out(self):
        """Publish a value of 1 to the 'esp32/open_door_out' topic."""
        print("Opening door out...")
        self.mqtt_handler.client.publish("esp32/open_door_out", 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # vid = cv2.VideoCapture(0)
    detector = DetectLicensePlate()
    main_window = ParkingApp(detector)
    main_window.show()

    # vid.release()
    cv2.destroyAllWindows()
    sys.exit(app.exec())
