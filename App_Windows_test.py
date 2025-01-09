import sys
import cv2
import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                           QLineEdit, QPushButton, QGridLayout, QVBoxLayout, 
                           QHBoxLayout, QFrame, QComboBox, QMessageBox,
                           QTabWidget, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo

class SmartCarPark(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize variables
        self.data_buffer = ""
        self.id_ls_vao = ""
        self.id_ls_ra = ""
        self.bienso_ls_vao = ""
        self.bienso_ls_ra = ""
        self.time_ls_vao = ""
        self.time_ls_ra = ""
        self.is_open_in = False
        self.is_open_out = False
        self.slot = 0
        self.capture = None
        self.processing_frame = False
        
        # Setup UI
        self.setWindowTitle("Smart Car Park System")
        self.setGeometry(100, 100, 1200, 700)
        
        # Create main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_management_tab(), "Quản lý hệ thống")
        self.main_layout.addWidget(self.tab_widget)
        
        # Setup timer for clock
        self.setup_timer()
        
        # Setup serial ports
        self.setup_serial_ports()
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        
    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S %p")
        self.label_clock.setText(current_time)
        
    def create_management_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()
        
        # Left section (Camera views and controls)
        left_section = QVBoxLayout()
        
        # Camera preview
        camera_group = QGroupBox("Camera Preview")
        camera_layout = QVBoxLayout()
        
        self.camera_view = QLabel()
        self.camera_view.setMinimumSize(640, 480)
        self.camera_view.setStyleSheet("background-color: #f0f0f0;")
        camera_layout.addWidget(self.camera_view)
        
        # Camera controls
        camera_controls = QHBoxLayout()
        self.camera_combo = QComboBox()
        self.populate_cameras()
        camera_controls.addWidget(QLabel("Camera:"))
        camera_controls.addWidget(self.camera_combo)
        
        self.btn_connect_camera = QPushButton("Connect")
        self.btn_connect_camera.clicked.connect(self.connect_camera)
        camera_controls.addWidget(self.btn_connect_camera)
        
        self.btn_capture = QPushButton("Capture")
        self.btn_capture.clicked.connect(self.capture_image)
        camera_controls.addWidget(self.btn_capture)
        
        camera_layout.addLayout(camera_controls)
        camera_group.setLayout(camera_layout)
        left_section.addWidget(camera_group)
        
        # Middle section (Entry/Exit info)
        middle_section = QVBoxLayout()
        
        # Serial port controls
        serial_group = QGroupBox("Serial Ports")
        serial_layout = QFormLayout()
        
        # Create port combo boxes
        self.port_combo_in = QComboBox()
        self.port_combo_out = QComboBox()
        
        serial_layout.addRow("Entrance Port:", self.port_combo_in)
        serial_layout.addRow("Exit Port:", self.port_combo_out)
        
        # Add connect buttons
        self.btn_connect_in = QPushButton("Connect")
        self.btn_connect_out = QPushButton("Connect")
        
        serial_layout.addRow("", self.btn_connect_in)
        serial_layout.addRow("", self.btn_connect_out)
        
        serial_group.setLayout(serial_layout)
        middle_section.addWidget(serial_group)
        
        # Entry section
        entry_group = QGroupBox("Entrance Gate")
        entry_layout = QFormLayout()
        
        self.entry_fields = {
            'id': QLineEdit(),
            'plate': QLineEdit(),
            'time': QLineEdit(),
            'status': QLineEdit()
        }
        
        for label, field in self.entry_fields.items():
            field.setReadOnly(True)
            entry_layout.addRow(f"{label.title()}:", field)
            
        entry_group.setLayout(entry_layout)
        middle_section.addWidget(entry_group)
        
        # Exit section
        exit_group = QGroupBox("Exit Gate")
        exit_layout = QFormLayout()
        
        self.exit_fields = {
            'id': QLineEdit(),
            'plate': QLineEdit(),
            'time': QLineEdit(),
            'status': QLineEdit()
        }
        
        for label, field in self.exit_fields.items():
            field.setReadOnly(True)
            exit_layout.addRow(f"{label.title()}:", field)
            
        exit_group.setLayout(exit_layout)
        middle_section.addWidget(exit_group)
        
        # Right section (Status and info)
        right_section = QVBoxLayout()
        
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        
        self.label_clock = QLabel()
        status_layout.addWidget(self.label_clock)
        
        self.label_slots = QLabel("Số vị trí trống: 0")
        status_layout.addWidget(self.label_slots)
        
        status_group.setLayout(status_layout)
        right_section.addWidget(status_group)
        
        # Add all sections to main layout
        layout.addLayout(left_section, stretch=2)
        layout.addLayout(middle_section, stretch=1)
        layout.addLayout(right_section, stretch=1)
        
        tab.setLayout(layout)
        return tab
        
    def setup_serial_ports(self):
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.handle_serial_data)
        
        # Clear existing items
        self.port_combo_in.clear()
        self.port_combo_out.clear()
        
        # Add available ports
        available_ports = QSerialPortInfo().availablePorts()
        for port in available_ports:
            self.port_combo_in.addItem(port.portName())
            self.port_combo_out.addItem(port.portName())
            
    def populate_cameras(self):
        self.camera_combo.clear()
        
        # Only check first 2 cameras to avoid excessive error messages
        for i in range(2):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Use DirectShow backend
                if cap.isOpened():
                    self.camera_combo.addItem(f"Camera {i}")
                    cap.release()
            except Exception as e:
                print(f"Error checking camera {i}: {str(e)}")
                
    def connect_camera(self):
        if self.capture is not None:
            self.capture.release()
            self.timer_camera.stop()
            
        try:
            camera_index = self.camera_combo.currentIndex()
            if camera_index >= 0:
                self.capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                if self.capture.isOpened():
                    self.timer_camera = QTimer()
                    self.timer_camera.timeout.connect(self.update_frame)
                    self.timer_camera.start(30)
                    QMessageBox.information(self, "Success", "Camera connected successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to connect to camera")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Camera error: {str(e)}")
                
    def update_frame(self):
        if not self.processing_frame and self.capture is not None:
            try:
                self.processing_frame = True
                ret, frame = self.capture.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    self.camera_view.setPixmap(QPixmap.fromImage(qt_image))
            except Exception as e:
                print(f"Error updating frame: {str(e)}")
            finally:
                self.processing_frame = False
            
    def capture_image(self):
        if self.capture is not None:
            try:
                ret, frame = self.capture.read()
                if ret:
                    cv2.imwrite("captured.jpg", frame)
                    self.process_license_plate("captured.jpg")
                    QMessageBox.information(self, "Success", "Image captured successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to capture image: {str(e)}")
                
    def process_license_plate(self, image_path):
        # Add your license plate recognition code here
        pass
        
    def handle_serial_data(self):
        # Add your serial data handling code here
        pass
        
    def closeEvent(self, event):
        if self.capture is not None:
            self.capture.release()
        self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SmartCarPark()
    window.show()
    sys.exit(app.exec())