import os
import sys
import time
import ctypes
import win32gui
import win32con
import subprocess
import win32process
import psutil
import win32api
import win32clipboard
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button, Listener

# Force the process to be DPI-Aware.
# This prevents Windows from scaling coordinate lookups, ensuring GetWindowRect
# coordinates exactly match physical mouse positions on displays with scaling (125%, 150%, etc.)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- CONFIGURATION ---

# Path to the game launcher executable
LAUNCHER_PATH = r"C:\MangoT5\PSTW\52GSlogin.exe"

# Default relative click coordinates (as percentage of launcher window width/height)
# You can use the Calibration Mode to find the exact percentages for your launcher!
ID_FIELD_PCT = {"x": 0.60, "y": 0.53}        # Click point for Account ID field (using client percentages)
PWD_FIELD_PCT = {"x": 0.60, "y": 0.70}       # Click point for Password field (using client percentages)
LOGIN_BTN_PCT = {"x": 0.88, "y": 0.65}       # Click point for "Enter Game" button

# Target launcher window search keywords (case-insensitive)
WINDOW_KEYWORDS = ["Gersang", "巨商", "掌門人", "天下第一商", "52GSLogin"]

# --- CONTROLLERS ---
mouse = MouseController()
keyboard = KeyboardController()


def list_active_windows():
    """Finds and lists all visible windows matching by process name or keywords."""
    matching_windows = []
    
    def win_enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            # Check window size (ignore tiny background or invisible helper windows)
            try:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if w < 300 or h < 200:
                    return
            except Exception:
                return

            # 1. Try matching by process name (extremely robust for custom skin windows with blank titles)
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                proc_name = proc.name().lower()
                if "52gslogin" in proc_name:
                    title = win32gui.GetWindowText(hwnd) or f"52GSLogin (PID: {pid})"
                    matching_windows.append((hwnd, title))
                    return
            except Exception:
                pass
            
            # 2. Fallback to matching by visible window title keywords
            title = win32gui.GetWindowText(hwnd)
            if title:
                # Ignore typical IDE, editor, python, or terminal windows to avoid matching this workspace folder name in VS Code or Terminal
                lower_title = title.lower()
                if any(ignored in lower_title for ignored in ["visual studio", "code", "editor", "python", "terminal", "cmd.exe", "powershell"]):
                    return
                for keyword in WINDOW_KEYWORDS:
                    if keyword.lower() in lower_title:
                        matching_windows.append((hwnd, title))
                        break
                        
    win32gui.EnumWindows(win_enum_handler, None)
    return matching_windows


def get_window_rect(hwnd):
    """Returns (left, top, width, height) of the window client area or window itself."""
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    return left, top, right - left, bottom - top


def get_client_coord(hwnd, pct_x, pct_y):
    """Converts relative client coordinates to absolute screen coordinates."""
    _, _, w, h = win32gui.GetClientRect(hwnd)
    cx = int(w * pct_x)
    cy = int(h * pct_y)
    return win32gui.ClientToScreen(hwnd, (cx, cy))


def focus_window(hwnd):
    """Brings the launcher window to the front, Z-orders it to top-most, and focuses it."""
    # Restore window if minimized
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)
    
    # Force window to top of the Z-stack to bypass Windows foreground restrictions
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
    
    # Focus window
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.5)  # Wait for focus transition


def calibrate_coordinates(hwnd):
    """Interactive mode to find the exact relative coordinate percentages of your launcher."""
    print("\n" + "="*50)
    print("                 CALIBRATION MODE")
    print("="*50)
    print("Instructions:")
    print("1. Bring the Launcher window to the screen.")
    print("2. Left-click on the ACCOUNT ID input box.")
    print("3. Left-click on the PASSWORD input box.")
    print("4. Left-click on the ENTER GAME (進入遊戲) button.")
    print("5. Press the 'Esc' key to finish calibration.")
    print("="*50)
    
    focus_window(hwnd)
    left, top, w, h = get_window_rect(hwnd)
    print(f"Launcher Window Position: Left={left}, Top={top}, Width={w}, Height={h}")
    
    clicks = []
    
    def on_click(x, y, button, pressed):
        if pressed and button == Button.left:
            # Check if the click is inside the launcher window
            left, top, w, h = get_window_rect(hwnd)
            if left <= x <= left + w and top <= y <= top + h:
                rel_x = (x - left) / w
                rel_y = (y - top) / h
                clicks.append({"abs_x": x, "abs_y": y, "rel_x": rel_x, "rel_y": rel_y})
                step_names = ["ACCOUNT ID field", "PASSWORD field", "ENTER GAME button"]
                step_idx = len(clicks) - 1
                
                name = step_names[step_idx] if step_idx < len(step_names) else f"Extra Click {step_idx - 2}"
                print(f"Captured: {name}")
                print(f"  -> Absolute: X={x}, Y={y}")
                print(f"  -> Relative: X_pct={rel_x:.3f}, Y_pct={rel_y:.3f}")
                print("-" * 30)

    def on_release(key):
        if key == Key.esc:
            return False  # Stop listener
            
    # Start mouse listener in background
    listener = Listener(on_click=on_click)
    listener.start()
    
    # Start keyboard listener to detect escape key
    with KeyboardController() as _:
        from pynput.keyboard import Listener as KListener
        with KListener(on_release=on_release) as k_listener:
            k_listener.join()
            
    listener.stop()
    
    print("\nCalibration finished!")
    if len(clicks) >= 3:
        print("\n=== Recommended Code Configurations ===")
        print(f"ID_FIELD_PCT = {{\"x\": {clicks[0]['rel_x']:.3f}, \"y\": {clicks[0]['rel_y']:.3f}}}")
        print(f"PWD_FIELD_PCT = {{\"x\": {clicks[1]['rel_x']:.3f}, \"y\": {clicks[1]['rel_y']:.3f}}}")
        print(f"LOGIN_BTN_PCT = {{\"x\": {clicks[2]['rel_x']:.3f}, \"y\": {clicks[2]['rel_y']:.3f}}}")
        print("=======================================")
        return clicks[0], clicks[1], clicks[2]
    else:
        print("Warning: Did not capture all 3 required clicks. Using default configurations.")
        return None


def set_clipboard_text(text):
    """Copies text to the Windows clipboard safely."""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
    except Exception as e:
        print(f"Clipboard copy error: {e}")


def win32_click(x, y):
    """Performs a native hardware-level left click using win32api."""
    print(f"Simulating hardware click at ({x}, {y})...")
    win32api.SetCursorPos((x, y))
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.15)


def wait_for_launcher_update_check():
    """Waits for the launcher update check to complete and button to activate."""
    print("\nWaiting for launcher update check to complete...")
    time.sleep(5.0)
    

def wait_for_game_launched(timeout=30):
    """Waits until the game window ('Gersang') is open and active on screen."""
    print("\nWaiting for game client ('Gersang') to launch...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Search natively for the newly created game client window
        hwnd = win32gui.FindWindow(None, "Gersang")
        if hwnd and win32gui.IsWindowVisible(hwnd):
            print("\nGame client ('Gersang') has successfully launched!")
            return True
        print(f"Checking for game client... Time elapsed: {int(time.time() - start_time)}s", end="\r")
        time.sleep(1.0)
        
    print(f"\nWarning: Timeout reached. Game client not detected yet.")
    return False


def perform_auto_fill(hwnd, username, password):
    """Clicks on the fields and automatically injects credentials using clipboard pasting."""
    print(f"\nStarting Hardware Auto-Fill sequence...")
    focus_window(hwnd)
    time.sleep(0.6)  # Give Windows extra time to complete focus and Z-order transitions
    
    # 1. Paste username directly (since the launcher automatically focuses the Account ID field on startup)
    print("Pasting Username...")
    set_clipboard_text(username)
    time.sleep(0.1)
    with keyboard.pressed(Key.ctrl):
        keyboard.press('v')
        keyboard.release('v')
    time.sleep(0.3)
    
    # 2. Press Tab to move to Password field
    print("Pressing Tab key to focus Password field...")
    keyboard.press(Key.tab)
    time.sleep(0.05)
    keyboard.release(Key.tab)
    time.sleep(0.3)
    
    # 3. Paste Password
    print("Pasting Password...")
    set_clipboard_text(password)
    time.sleep(0.1)
    with keyboard.pressed(Key.ctrl):
        keyboard.press('v')
        keyboard.release('v')
    time.sleep(0.3)
    
    # 3. Wait for the 'Enter Game' button to become active (matching the golden diamond color of the picture)
    print("\nWaiting for the 'Enter Game' button to become active...")
    
    # Poll color every 1 second until the button matches the golden-beige active state
    # We scan the entire button region on screen to be 100% robust against title bar offsets, borders, and DPI scaling!
    while True:
        # Re-fetch the current window location in case it was dragged or moved
        left, top, w, h = get_window_rect(hwnd)
        
        # Define search region coordinates using ClientToScreen (independent of window borders/title bar)
        min_x, min_y = get_client_coord(hwnd, 0.75, 0.40)
        max_x, max_y = get_client_coord(hwnd, 0.98, 0.80)
        
        hdc = win32gui.GetDC(0)
        gold_pixel_count = 0
        center_rgb = (0, 0, 0)
        
        try:
            # Sample the exact assumed relative center for diagnostic console output
            btn_x, btn_y = get_client_coord(hwnd, LOGIN_BTN_PCT["x"], LOGIN_BTN_PCT["y"])
            center_val = win32gui.GetPixel(hdc, btn_x, btn_y)
            center_rgb = (center_val & 0xff, (center_val >> 8) & 0xff, (center_val >> 16) & 0xff)
            
            # Scan the region with a step of 3 pixels (extremely fast, completes in < 2ms)
            for y in range(min_y, max_y, 5):
                for x in range(min_x, max_x, 5):
                    color_val = win32gui.GetPixel(hdc, x, y)
                    r = color_val & 0xff
                    g = (color_val >> 8) & 0xff
                    b = (color_val >> 16) & 0xff
                    
                    # Golden/beige active button color criteria:
                    if (170 <= r <= 255) and (140 <= g <= 245) and (100 <= b <= 210) and (r > g) and (g > b):
                        gold_pixel_count += 1
                        if gold_pixel_count >= 1: # We found at least 1 active golden pixels
                            break
                if gold_pixel_count >= 1:
                    break
        finally:
            win32gui.ReleaseDC(0, hdc)
            
        if gold_pixel_count >= 1:
            print(f"Detected active button! Golden pixel count in region: {gold_pixel_count}")
            break
            
        print(f"Checking... Button is not active yet (waiting for update check). Center pixel color: RGB={center_rgb}")
        time.sleep(1.0)
    # 4. replace gts languange to english
    import urllib.request
    
    file_name = "ChineseT.gts"
    dest_folder = r"C:\MangoT5\PSTW"
    file_url = "https://drive.google.com/uc?export=download&id=1lGhdhtvUwZ9nef3it_ndYQeauNHbbpVQ"
    dest_path = os.path.join(dest_folder, file_name)
    
    try:
        print(f"\nDownloading {file_name} from Google Drive...")
        os.makedirs(dest_folder, exist_ok=True)
        
        # Add User-Agent headers to ensure reliable Google Drive file fetching
        req = urllib.request.Request(
            file_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            out_file.write(response.read())
            
        if os.path.exists(dest_path):
            print(f"Download complete: {file_name} successfully saved to {dest_folder}")
        else:
            print("Download failed: File not found after download attempt.")
    except Exception as e:
        print(f"Download failed! Error: {e}")
    
    # 5. Submit form by pressing the Enter key (No useless focus_window call here)
    print("Submitting login form by pressing Enter...")
    keyboard.press(Key.enter)
    time.sleep(0.05)
    keyboard.release(Key.enter)
    
    print("Auto-Fill complete!")


def load_credentials():
    """Loads the username and password from a local credentials.txt file, auto-creating a template and exiting if missing."""
    # Determine the directory containing the running script or compiled .exe
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
    credentials_path = os.path.join(script_dir, "credentials.txt")
    
    # If the credentials file does not exist, create a blank template and exit
    if not os.path.exists(credentials_path):
        try:
            with open(credentials_path, "w", encoding="utf-8") as f:
                f.write("# Gersang Auto Login Credentials\n")
                f.write("# Enter your real username and password below, then save this file.\n")
                f.write("# Format: key-value (e.g. username=your_id) or simple line-by-line.\n\n")
                f.write("username=ENTER_YOUR_USERNAME_HERE\n")
                f.write("password=ENTER_YOUR_PASSWORD_HERE\n")
            print(f"\n[Error] Created credentials template at: {credentials_path}")
            print("Please open credentials.txt, configure your real username and password, and run the script again.")
        except Exception as e:
            print(f"Error creating credentials.txt template: {e}")
        sys.exit(1)

    username = ""
    password = ""
    
    try:
        with open(credentials_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            
        parsed_values = []
        for line in lines:
            if "=" in line:
                key, val = line.split("=", 1)
                parsed_values.append(val.strip())
            elif ":" in line:
                key, val = line.split(":", 1)
                parsed_values.append(val.strip())
            else:
                parsed_values.append(line)
                
        if len(parsed_values) >= 1:
            username = parsed_values[0]
        if len(parsed_values) >= 2:
            password = parsed_values[1]
            
    except Exception as e:
        print(f"Error reading credentials.txt: {e}")
        sys.exit(1)
        
    # Validate that real credentials have been configured
    if not username or not password or "ENTER_YOUR_" in username or "ENTER_YOUR_" in password:
        print(f"\n[Error] Invalid or placeholder credentials detected in credentials.txt!")
        print(f"File path: {credentials_path}")
        print("Please edit the file, enter your real credentials, and try again.")
        sys.exit(1)
        
    print(f"\nLoaded login credentials successfully (Username: {username})")
    return username, password


def main():
    # 1. Check if calibration is requested via command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--calibrate":
        print("Searching for launcher window for calibration...")
        windows = list_active_windows()
        if not windows:
            print("\nError: Launcher window not found!")
            print("Please ensure your game launcher is open and visible on screen to calibrate.")
            input("\nPress Enter to exit...")
            sys.exit(1)
            
        target_hwnd, target_title = windows[0]
        print(f"\nCalibrating on Window: '{target_title}'")
        calibrate_coordinates(target_hwnd)
        input("\nPress Enter to exit...")
        sys.exit(0)

    # 2. Otherwise, run the streamlined login flow!
    print("=" * 50)
    print("              GERSANG FAST AUTO LOGIN")
    print("=" * 50)
    user, pwd = load_credentials()

    print("\nStarting launcher process...")
    if os.path.exists(LAUNCHER_PATH):
        print(f"Launching: '{LAUNCHER_PATH}'...")
        launcher_dir = os.path.dirname(LAUNCHER_PATH)
        try:
            subprocess.Popen(LAUNCHER_PATH, cwd=launcher_dir)
        except Exception as e:
            print(f"Error: Could not launch executable: {e}")
            input("\nPress Enter to exit...")
            sys.exit(1)
    else:
        print(f"Error: Launcher executable not found at: {LAUNCHER_PATH}")
        print("Please check the path or ensure it is installed.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Poll for window to appear (wait up to 15 seconds)
    print("Waiting for launcher window to appear...")
    windows = []
    for i in range(300):
        time.sleep(0.5)
        windows = list_active_windows()
        if windows:
            print("Launcher window detected!")
            break

    if not windows:
        print("\nError: Launcher window did not appear within 15 seconds.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    target_hwnd, target_title = windows[0]
    left, top, w, h = get_window_rect(target_hwnd)
    print(f"Launcher window detected: '{target_title}' (Size: {w}x{h})")
    
    # Wait for GUI elements/fields to fully load
    print("Waiting 3 seconds for GUI elements to fully load...")
    time.sleep(3.0)
    
    # Perform auto fill
    perform_auto_fill(target_hwnd, user, pwd)
    time.sleep(1)



if __name__ == "__main__":
    # If run as Administrator, make sure working directory is correct
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        input("\nPress Enter to exit...")
