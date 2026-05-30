# YOLOv4-tiny Object Detection, Auto Combat, and Auto Login System for Gersang

This repository implements a real-time object detection, automated combat, and zero-touch auto-login system for the PC game "Gersang" (巨商) using YOLOv4-tiny, OpenCV, and native Windows API keyboard/mouse event simulation.

---

## ⚠️ Disclaimer

This project is intended for **educational and learning purposes only**.  
All automation features are implemented solely to explore real-time object detection, model deployment, and system control integration in a safe, offline environment.

The game "Gersang" is used purely as a technical testbed for computer vision applications, without modifying game memory, reading active processes' memory, or interfering with network communications. All automation operates strictly through standard window capture and OS-level hardware input simulation.

Please do not use this project or its derived components for any unethical behavior, including but not limited to:
- Online cheating or botting in multiplayer environments
- Violations of the game's terms of service
- Unauthorized actions that disrupt the game experience for others

---

## 🎥 Auto Combat Demo Video

[![Watch the video](https://img.youtube.com/vi/k_GV45inPjE/0.jpg)](https://youtu.be/k_GV45inPjE)

---

## 🚀 Key Features

### 1. Zero-Touch Auto Login System
A standalone credential filler and launcher automation macro:
- **Clipboard Injection Bypass**: Avoids detectable raw key typing by directly injecting credentials via Windows clipboard pasting (`Ctrl + V`).
- **GPU-Bypassing Screen DC Scanner**: Uses a highly efficient screen GDI device context scanner that bypasses GPU-accelerated window blackouts to capture actual pixels.
- **Dynamic Bounding-Box Color Polling**: Scans the button region at a step of 5 pixels (<2ms execution) for the golden-beige active color to automatically submit as soon as the files update check completes.
- **DPI and Border Independent**: Utilizes absolute `ClientToScreen` coordinate translations, making the macro immune to custom themes, title bar sizes, and Windows DPI scaling (125%, 150%, etc.).
- **Credentials Security**: Automatically ignores and hides credentials behind a local, Git-ignored `credentials.txt` file.

### 2. YOLOv4-tiny Real-Time Auto Combat Bot
A deep learning-based automated combat macro:
- **High-Speed Window Capturing**: Grabs the game window frames using fast native Windows GDI `BitBlt` transfers.
- **Real-Time Bounding Box Inference**: Detects target monsters (e.g. skeleton bowmen) using custom-trained YOLOv4-tiny models executed inside OpenCV's DNN network.
- **Hardware-Level Simulators**: Automatically Z-orders target coordinates, translates positions, and injects combat keystrokes (`G`, `1`, `Space`) to defeat targets automatically.

---

## 🛠️ Technologies Used

| Component | Description |
|----------|-------------|
| YOLOv4-tiny (Darknet) | Lightweight, low-latency deep learning object detection model |
| OpenCV (cv2.dnn) | Fast model inference and image preprocessing |
| win32gui / win32ui | Captures game window client contents natively |
| pynput | Simulates native hardware keyboard and mouse inputs |
| PyInstaller | Standalone Windows `.exe` compiler |
| AlexeyAB/darknet | Model training environment (Google Colab T4 GPU) |
| makesense.ai | Bounding-box image annotation tool (YOLO format) |

---

## 📂 Project Directory Overview

```
yolov4-tiny-opencv-gersang-automation/
├── auto_login.py            # Zero-touch Auto Login macro script
├── run_auto_login.bat       # Helper script to launch Auto Login with Admin rights
├── run_calibration.bat      # Calibration utility to configure launcher clicks
├── dist/
│   └── GersangAutoLogin.exe # Standalone compiled Windows executable
├── 1_generate_dataset.ipynb # Phase 1: Screenshots generator for dataset
├── 2_label_dataset.ipynb    # Phase 2: Generates YOLO custom model config files
├── 3_yolo_model_training.ipynb # Phase 3: Colab training notebook wrapper
├── 4_yolo_opencv_detector.py # Phase 4: In-game auto combat main bot
├── yolov4-tiny/
│   ├── yolov4-tiny-custom.cfg       # YOLO network architecture file
│   └── obj.names / obj.data         # Class definitions and paths
├── requirements.txt         # Python package dependencies
```

---

## 🔑 How to Configure and Run

### Phase A: Zero-Touch Auto Login

#### 1. Setup Your Credentials
On the first run of the script or executable, a local, Git-ignored `credentials.txt` file is automatically created in the same folder.
Open the [credentials.txt](credentials.txt) file and replace the placeholder text with your real Gersang account credentials:
```ini
username=your_gersang_id
password=your_gersang_password
```

#### 2. Running the Auto Login
You can run the auto login in three ways:

* **Method 1: Standalone Executable (Recommended)**
  Navigate into the `dist/` directory, ensure `credentials.txt` is placed next to `GersangAutoLogin.exe`, and double-click:
  ```
  GersangAutoLogin.exe
  ```
* **Method 2: Elevated Batch Script**
  Double-click `run_auto_login.bat`. It will prompt for Windows Administrator rights and launch the Python script:
  ```powershell
  run_auto_login.bat
  ```
* **Method 3: Raw Python Script**
  Open an Administrator terminal and execute:
  ```bash
  python auto_login.py
  ```

#### 3. Coordinate Calibration (Optional)
If your launcher skin has custom dimensions or buttons, double-click `run_calibration.bat` to run the calibration tool. The terminal will guide you to click on your Account field, Password field, and Enter Game button, generating perfect relative coordinates to copy and paste into the script configuration section.

---

### Phase B: YOLOv4-tiny Auto Combat

#### 1. Image Collection (Dataset Generation)
1. Open Gersang in **Windowed Mode**. Ensure the window title bar is named exactly `Gersang`.
2. Open a terminal in the project directory and run:
   ```bash
   jupyter notebook
   ```
3. Open `1_generate_dataset.ipynb` and run the cells. The script will capture screenshots of the game window client area every `0.3` seconds and save them inside `images/`.

#### 2. Labeling & Annotation
1. Open [makesense.ai](https://www.makesense.ai/) in your browser.
2. Drag all screenshots from your `images/` directory into the workspace.
3. Select **Object Detection** and draw bounding boxes around target enemies, labeling them (e.g., `bow_skeleton`).
4. Go to **Actions** > **Export Annotations** and download the annotations as a **Single .zip package in YOLO format**.
5. Extract the `.zip` file and place all `.txt` label files together with their corresponding `.jpg` images inside the `shuffled_images/` directory.

#### 3. Config Generation
1. In `2_label_dataset.ipynb`, declare your target class list (e.g. `classes = ["bow_skeleton"]`).
2. Run the cells to automatically package `yolov4-tiny/obj.zip` and generate updated `obj.names`, `obj.data`, and `yolov4-tiny-custom.cfg` configuration files.

#### 4. Model Training (Google Colab)
1. Upload the entire `yolov4-tiny` folder to the root of your Google Drive.
2. Open Google Colab and upload the training notebook `3_yolo_model_training.ipynb`.
3. Set your runtime type to **GPU** (T4 GPU).
4. Run the training cells. Training checkpoints will automatically sync back to your Google Drive `/yolov4-tiny/training/` directory.

#### 5. Deploying the Bot
1. Download the finished weight file `yolov4-tiny-custom_last.weights` from your Google Drive.
2. Place the weights file in the root of your project directory (alongside `4_yolo_opencv_detector.py`).
3. Right-click `run_detect_and_click.bat` and select **Run as Administrator** to launch the combat bot.
4. Press `q` while focusing the OpenCV display window to stop the bot.

---

## 📝 Technical Notes

- The YOLO model input resolution is configured at `416x416`.
- Bounding-box detection positions are automatically re-scaled back to native window sizes to guarantee mouse aiming accuracy.
- The game window must run in windowed mode and remain in the foreground for hardware controls to function.

## 🤝 Credits

- YOLOv4 training: [AlexeyAB/darknet](https://github.com/AlexeyAB/darknet)
- Annotation tool: [makesense.ai](https://www.makesense.ai/)
