import os
import re
import time
import json
import win32api
import win32con
import win32file
import win32gui
import pythoncom
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

class USBDLPHandler:
    def __init__(self):
        self.server_url = "http://localhost:5000"
        self.blocked_devices = set()
        
    def monitor_usb(self):
        print("USB DLP monitoring started...")
        while True:
            self.check_usb_devices()
            time.sleep(5)  # Check every 5 seconds

    def check_usb_devices(self):
        try:
            drive_list = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
            for drive in drive_list:
                if win32file.GetDriveType(drive) == win32con.DRIVE_REMOVABLE:
                    if drive not in self.blocked_devices:
                        self.scan_usb_device(drive)
        except Exception as e:
            print(f"USB monitoring error: {e}")

    def scan_usb_device(self, drive_path):
        try:
            for root, _, files in os.walk(drive_path):
                for file in files:
                    if file.lower().endswith(('.docx', '.xlsx', '.pptx', '.pdf')):
                        file_path = os.path.join(root, file)
                        classification = self.check_document_classification(file_path)
                        if classification and classification['level'] in ['Top Secret', 'Secret']:
                            self.block_device(drive_path, file_path, classification)
                            return
        except Exception as e:
            print(f"USB scan error: {e}")

    def check_document_classification(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read(5000).decode('utf-8', errors='ignore')
                match = re.search(r'Classification:\s*(.*?)\s*\|', content)
                if match:
                    return {
                        'level': match.group(1),
                        'file': os.path.basename(file_path)
                    }
        except Exception as e:
            print(f"Document check error: {e}")
        return None

    def block_device(self, drive_path, file_path, classification):
        try:
            # Eject the USB device
            win32api.PostQuitMessage(0)
            self.blocked_devices.add(drive_path)
            
            # Log to DLP system
            requests.post(f"{self.server_url}/api/log_document", json={
                'filename': classification['file'],
                'path': file_path,
                'classification_id': self.get_classification_id(classification['level']),
                'user': os.getlogin(),
                'action': 'usb_blocked'
            })
            
            print(f"Blocked USB device {drive_path} containing classified document")
            
        except Exception as e:
            print(f"USB blocking error: {e}")

    def get_classification_id(self, level):
        # Map classification levels to IDs
        levels = {
            'Top Secret': 1,
            'Secret': 2,
            'Confidential': 3,
            'Public': 4
        }
        return levels.get(level)

if __name__ == "__main__":
    handler = USBDLPHandler()
    handler.monitor_usb()