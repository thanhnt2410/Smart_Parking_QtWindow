import cv2
import numpy as np
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
from simple_CNN_util import get_parking_spots_bboxes, empty_or_not

def calc_diff(im1, im2):
    return np.abs(np.mean(im1) - np.mean(im2))

mask_path = 'C:/Users/DUYEN/OneDrive/Documents/GitHub/Smart_parking_car_computer_vision/Detect_vitri/parking-space-counter/Mask_final.jpg'
# video_path = 'C:/Users/DUYEN/OneDrive/Documents/GitHub/Smart_parking_car_computer_vision/Detect_vitri/parking-space-counter/WIN_20240726_15_48_06_Pro.mp4'

mask = cv2.imread(mask_path, 0)
mask_height, mask_width = mask.shape[:2]

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")

connected_components = cv2.connectedComponentsWithStats(mask, 4, cv2.CV_32S)

# Define minimum width and height for parking spots
min_width = 20
min_height = 20

def get_parking_spots_bboxes(connected_components, min_width=20, min_height=20):
    (numLabels, labels, stats, centroids) = connected_components
    spots = []

    for i in range(1, numLabels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        # Filter out small rectangles
        if w >= min_width and h >= min_height:
            spots.append((x, y, w, h))

    return spots

spots = get_parking_spots_bboxes(connected_components, min_width, min_height)

spots_status = [None for _ in spots]
diffs = [None for _ in spots]

previous_frame = None

frame_nmr = 0
step = 10
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        break

    # Resize frame to match the mask size
    frame = cv2.resize(frame, (mask_width, mask_height))

    if frame_nmr % step == 0 and previous_frame is not None:
        for spot_indx, spot in enumerate(spots):
            x1, y1, w, h = spot
            spot_crop = frame[y1:y1 + h, x1:x1 + w, :]
            diffs[spot_indx] = calc_diff(spot_crop, previous_frame[y1:y1 + h, x1:x1 + w, :])
        print([diffs[j] for j in np.argsort(diffs)][::-1])

    if frame_nmr % step == 0:
        if previous_frame is None:
            arr_ = range(len(spots))
        else:
            arr_ = [j for j in np.argsort(diffs) if diffs[j] / np.amax(diffs) > 0.4]
        for spot_indx in arr_:
            spot = spots[spot_indx]
            x1, y1, w, h = spot
            spot_crop = frame[y1:y1 + h, x1:x1 + w, :]
            spot_status = empty_or_not(spot_crop)
            spots_status[spot_indx] = spot_status

    if frame_nmr % step == 0:
        previous_frame = frame.copy()

    for spot_indx, spot in enumerate(spots):
        spot_status = spots_status[spot_indx]
        x1, y1, w, h = spots[spot_indx]

        if spot_status:
            frame = cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), (0, 255, 0), 2)
        else:
            frame = cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), (0, 0, 255), 2)

    cv2.rectangle(frame, (80, 20), (550, 80), (0, 0, 0), -1)
    cv2.putText(frame, 'Available spots: {} / {}'.format(str(sum(spots_status)), str(len(spots_status))), (100, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.imshow('frame', frame)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

    frame_nmr += 1

cap.release()
cv2.destroyAllWindows()
