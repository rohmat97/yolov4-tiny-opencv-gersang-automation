#!/usr/bin/env python
# coding: utf-8

# # **Instructions**:
# 
# ### 1 - Open your game that you want to perform detections
# ### 2 - In the game window, get the name of it's title bar 
# ### 3 - Update the variable "window_name" with the game title bar name
# ### 4 - Run all cells to start detecting objects using your trained model

# In[1]:


import numpy as np
import win32gui, win32ui, win32con
from PIL import Image
from time import sleep
import cv2 as cv
import os
import random

# Ensure the working directory is set to the directory of this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# The batch file execution is handled externally via run_detect_and_click.bat to run as Administrator.


# In[2]:


class WindowCapture:
    w = 0
    h = 0
    hwnd = None

    def __init__(self, window_name):
        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise Exception('Window not found: {}'.format(window_name))

        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        border_pixels = 8
        titlebar_pixels = 30
        self.w = self.w - (border_pixels * 2)
        self.h = self.h - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

    def get_screenshot(self):
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        img = img[...,:3]
        img = np.ascontiguousarray(img) 
            
        return img

    def generate_image_dataset(self):
        if not os.path.exists("images"):
            os.mkdir("images")
        while(True):
            img = self.get_screenshot()
            im = Image.fromarray(img[..., [2, 1, 0]])
            im.save(f"./images/img_{len(os.listdir('images'))}.jpeg")
            sleep(1)
    
    def get_window_size(self):
        return (self.w, self.h)


# In[3]:


class ImageProcessor:
    W = 0
    H = 0
    net = None
    ln = None
    classes = {}
    colors = []

    def __init__(self, img_size, cfg_file, weights_file):
        np.random.seed(42)
        self.net = cv.dnn.readNetFromDarknet(cfg_file, weights_file)
        self.net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i-1] for i in self.net.getUnconnectedOutLayers()]
        self.W = img_size[0]
        self.H = img_size[1]
        
        with open('yolov4-tiny/obj.names', 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            self.classes[i] = line.strip()
        
        # If you plan to utilize more than six classes, please include additional colors in this list.
        self.colors = [
            (0, 0, 255), 
            (0, 255, 0), 
            (255, 0, 0), 
            (255, 255, 0), 
            (255, 0, 255), 
            (0, 255, 255)
        ]
        

    def proccess_image(self, img):

        blob = cv.dnn.blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.ln)
        outputs = np.vstack(outputs)
        
        coordinates = self.get_coordinates(outputs, 0.5)

        self.draw_identified_objects(img, coordinates)

        return coordinates

    def get_coordinates(self, outputs, conf):

        boxes = []
        confidences = []
        classIDs = []

        for output in outputs:
            scores = output[5:]
            
            classID = np.argmax(scores)
            confidence = scores[classID]
            if confidence > conf:
                x, y, w, h = output[:4] * np.array([self.W, self.H, self.W, self.H])
                p0 = int(x - w//2), int(y - h//2)
                boxes.append([*p0, int(w), int(h)])
                confidences.append(float(confidence))
                classIDs.append(classID)

        indices = cv.dnn.NMSBoxes(boxes, confidences, conf, conf-0.1)

        if len(indices) == 0:
            return []

        coordinates = []
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            coordinates.append({'x': x, 'y': y, 'w': w, 'h': h, 'class': classIDs[i], 'class_name': self.classes[classIDs[i]]})
        return coordinates

    def draw_identified_objects(self, img, coordinates):
        for coordinate in coordinates:
            x = coordinate['x']
            y = coordinate['y']
            w = coordinate['w']
            h = coordinate['h']
            classID = coordinate['class']
            
            color = self.colors[classID]
            
            cv.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv.putText(img, self.classes[classID], (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv.imshow('window',  img)


# In[4]:


# Run this cell to initiate detections using the trained model.

from pynput.mouse import Button, Controller
from pynput.keyboard import Controller as KeyboardController, Key
mouse = Controller()
keyboard = KeyboardController()

window_name = "Gersang"
cfg_file_name = "./yolov4-tiny/yolov4-tiny-custom.cfg"
weights_file_name = "yolov4-tiny-custom_last.weights"

# Check if configuration file exists
if not os.path.exists(cfg_file_name):
    print(f"Error: YOLO configuration file not found at: {os.path.abspath(cfg_file_name).replace('\\', '/')}")
    input("\nPress Enter to exit...")
    exit(1)

# Check if weights file exists
if not os.path.exists(weights_file_name):
    print(f"Error: Trained model weights file '{weights_file_name}' not found!")
    print(f"Expected path: {os.path.abspath(weights_file_name).replace('\\', '/')}")
    print("\nTo resolve this:")
    print("1. If you haven't trained the model yet, follow the Colab training steps in 'project_execution_guide.md'.")
    print("2. If you already trained it, download the '.weights' file from your Google Drive and put it in this folder.")
    input("\nPress Enter to exit...")
    exit(1)

try:
    print(f"Searching for game window: '{window_name}'...")
    wincap = WindowCapture(window_name)
    print("Game window found!")
except Exception as e:
    print(f"\nError: Could not capture game window.")
    print(f"Details: {e}")
    print(f"Please ensure that the game '{window_name}' is open, running in windowed mode, and visible on your screen.")
    input("\nPress Enter to exit...")
    exit(1)

try:
    print("Loading YOLOv4-tiny model into OpenCV DNN...")
    improc = ImageProcessor(wincap.get_window_size(), cfg_file_name, weights_file_name)
    print("Model loaded successfully! Starting detection loop...")
except Exception as e:
    print(f"\nError: Could not initialize ImageProcessor (OpenCV DNN network).")
    print(f"Details: {e}")
    input("\nPress Enter to exit...")
    exit(1)


while(True):
    
    ss = wincap.get_screenshot()
    
    if cv.waitKey(1) == ord('q'):
        cv.destroyAllWindows()
        break

    coordinates = improc.proccess_image(ss)
    keyboard.press(Key.space)

    coordinates = [c for c in coordinates if c["class_name"] == "bow_skeleton"]

    if len(coordinates) == 0:
        continue
        
    sk_to_hit = coordinates[0]

    mouse.position = (sk_to_hit['x'], sk_to_hit['y'])

    # Start pressing 'G' and space keys
    keyboard.press('1')
    keyboard.press('g')
    

    # Keep pressing 'G' and space with a short delay
    for _ in range(10):
        keyboard.press('g')
        sleep(0.1)  # Adjust the sleep duration as needed
        keyboard.release('g')
        sleep(0.1)  # Adjust the sleep duration as needed

    # Stop pressing the keys
    keyboard.release('g')
    keyboard.release(Key.space)

print('Finished.')



# # 
