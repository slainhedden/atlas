import pyautogui
import os
import time
import pytesseract
from PIL import Image
import io
import threading
from collections import deque
from mss import mss
import sys
import pygetwindow as gw
from screeninfo import get_monitors
import ctypes

class ScreenshotHandler:
    def __init__(self, max_screenshots=15, screenshot_dir="screenshots", compression_quality=85):
        self.screenshot_buffer = deque(maxlen=max_screenshots)
        self.screenshot_dir = screenshot_dir
        self.compression_quality = compression_quality
        self.lock = threading.Lock()
        self.make_directory()
        self.os = sys.platform # Get the operating system of the user
        if self.os == "win32":
            ctypes.windll.shcore.SetProcessDpiAwareness(2)

    def make_directory(self):
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def screenshot_memory(self):
        with self.lock:
            return list(self.screenshot_buffer)
        
    def get_active_monitor(self):
        active_window = gw.getActiveWindow()
        if not active_window:
            print("No active window detected.")
            return None

        window_center_x = active_window.left + active_window.width // 2
        window_center_y = active_window.top + active_window.height // 2

        with mss() as sct:
            for monitor in sct.monitors[1:]:  # Skip the first entry (combined monitor)
                if (monitor["left"] <= window_center_x < monitor["left"] + monitor["width"] and
                    monitor["top"] <= window_center_y < monitor["top"] + monitor["height"]):
                    return monitor
        return None

    def capture_screenshot(self):
        monitor = self.get_active_monitor()
        if monitor is None:
            print("Could not determine the active monitor.")
            return

        with mss() as sct:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            # Using monitor index to capture the screen
            monitor_index = sct.monitors.index(monitor)  # Get index of the monitor in the list
            sct.shot(mon=monitor_index, output=filepath)

        with self.lock:
            if len(self.screenshot_buffer) == self.screenshot_buffer.maxlen:
                old_screenshot = self.screenshot_buffer.popleft()
                self._remove_file(old_screenshot)
            self.screenshot_buffer.append(filepath)
        
        return filepath
        # Compress and save the screenshot
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG", quality=self.compression_quality)
        img_data = buffer.getvalue()

        with open(filepath, "wb") as f:
            f.write(img_data)

      

        return filepath
    
    def _remove_file(self, filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            print(f"Error removing file {filepath}: {e}")

    def cleanup(self):
        with self.lock:
            for screenshot in self.screenshot_buffer:
                self._remove_file(screenshot)
            self.screenshot_buffer.clear()
            

    def get_screenshot_info(self):
        with self.lock:
            total_size = sum(os.path.getsize(f) for f in self.screenshot_buffer)
            return {
                "count": len(self.screenshot_buffer),
                "total_size_mb": total_size / (1024 * 1024),
                "oldest": self.screenshot_buffer[0] if self.screenshot_buffer else None,
                "newest": self.screenshot_buffer[-1] if self.screenshot_buffer else None
            }

    def set_interval(self, interval):
        self.screenshot_interval = interval

    def get_settings(self):
        return {
            "interval": self.screenshot_interval,
            "max_screenshots": self.screenshot_buffer.maxlen,
            "compression_quality": self.compression_quality
        }