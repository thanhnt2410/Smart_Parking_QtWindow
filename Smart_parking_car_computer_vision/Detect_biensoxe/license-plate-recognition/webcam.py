from PIL import Image
import cv2
import torch
import math 
import function.utils_rotate as utils_rotate
# from IPython.display import display
import os
import time
import argparse
import function.helper as helper
# from mqtt_handler import MQTTHandler

# # Khởi tạo MQTT Handler
# mqtt_handler = MQTTHandler(port=1883, topic="license_plate/detection")
# mqtt_broke = "192.168.1.14"
# mqtt_port=1883
# mqtt_topic="esp32/slots"

class DetectLicensePlate:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        # self.mqtt_handler = MQTTHandler()
        # self.mqtt_handler.start()

        # Load models
        self.yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', 
                                             force_reload=True, source='local')
        self.yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', 
                                                 force_reload=True, source='local')
        self.yolo_license_plate.conf = 0.60

        self.prev_frame_time = 0
        self.new_frame_time = 0
        # Khởi tạo camera
        self.cap = cv2.VideoCapture(self.camera_index)

    def detect_plate(self, frame):
        """Phát hiện biển số xe trên một frame"""
        plates = self.yolo_LP_detect(frame, size=640)
        list_plates = plates.pandas().xyxy[0].values.tolist()
        # list_read_plates = set()
        lp = ""
        for plate in list_plates:
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin
            crop_img = frame[y:y + h, x:x + w]

            # Vẽ hình chữ nhật bao quanh biển số
            cv2.rectangle(frame, (x, y), (x + w, y + h), color=(0, 0, 255), thickness=2)

            # Xử lý nhận diện biển số
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = helper.read_plate(self.yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        # list_read_plates.add(lp)
                        # Hiển thị biển số lên frame
                        cv2.putText(frame, lp, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                        # Gửi dữ liệu qua MQTT
                        # self.mqtt_handler.publish(lp)
                        return frame, lp

        return frame, lp

    def run(self):
        """Bắt đầu phát hiện biển số từ camera"""
        vid = cv2.VideoCapture(self.camera_index)
        while True:
            ret, frame = vid.read()
            if not ret:
                break

            # Phát hiện biển số trên frame
            frame, lp = self.detect_plate(frame)

            # Tính FPS
            self.new_frame_time = time.time()
            fps = 1 / (self.new_frame_time - self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time
            fps = int(fps)
            cv2.putText(frame, f"FPS: {fps}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Hiển thị frame
            cv2.imshow("License Plate Detection", frame)

            # Thoát nếu nhấn 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        vid.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":

    # Tạo đối tượng phát hiện biển số
    detector = DetectLicensePlate()

    # Chạy phát hiện
    detector.run()
