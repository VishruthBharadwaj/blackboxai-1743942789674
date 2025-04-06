import os
import sys
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tkinter import Tk, Label, Radiobutton, Button, StringVar, messagebox
import pythoncom
from win32com.client import Dispatch

# Configuration
SERVER_URL = "http://localhost:5000"
WATCH_FOLDERS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Desktop")
]

class DocumentHandler(FileSystemEventHandler):
    def __init__(self):
        self.office_app = None
        self.classification_cache = {}
        
    def on_created(self, event):
        if not event.is_directory and self.is_supported_file(event.src_path):
            self.prompt_classification(event.src_path)
            
    def is_supported_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.docx', '.xlsx', '.pptx', '.pdf']
    
    def prompt_classification(self, file_path):
        try:
            # Get classifications from server
            if not self.classification_cache:
                response = requests.get(f"{SERVER_URL}/api/classifications")
                if response.status_code == 200:
                    self.classification_cache = response.json()
            
            # Create classification dialog
            root = Tk()
            root.title("Document Classification")
            
            Label(root, text="Please classify this document:").pack(pady=10)
            Label(root, text=os.path.basename(file_path)).pack()
            
            classification = StringVar()
            for cls in self.classification_cache:
                Radiobutton(root, 
                          text=cls['name'],
                          variable=classification,
                          value=cls['id']).pack(anchor='w')
            
            def on_submit():
                if not classification.get():
                    messagebox.showerror("Error", "Please select a classification")
                    return
                
                # Stamp document and log to server
                self.stamp_document(file_path, classification.get())
                self.log_action(file_path, 'create', classification.get())
                root.destroy()
            
            Button(root, text="Submit", command=on_submit).pack(pady=10)
            root.mainloop()
            
        except Exception as e:
            print(f"Error classifying document: {e}")

    def stamp_document(self, file_path, classification_id):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            cls = next(c for c in self.classification_cache if c['id'] == classification_id)
            
            if ext == '.docx':
                self.stamp_word(file_path, cls)
            elif ext == '.pdf':
                self.stamp_pdf(file_path, cls)
            # Add other file type handlers as needed
            
        except Exception as e:
            print(f"Error stamping document: {e}")

    def stamp_word(self, file_path, classification):
        try:
            pythoncom.CoInitialize()
            word = Dispatch("Word.Application")
            doc = word.Documents.Open(file_path)
            
            # Add footer with classification
            for section in doc.Sections:
                footer = section.Footers(1)
                footer.Range.Text = f"Classification: {classification['name']} | User: {os.getlogin()}"
                footer.Range.Font.Color = classification['color']
            
            doc.Save()
            doc.Close()
            word.Quit()
            
        except Exception as e:
            print(f"Error stamping Word document: {e}")

    def stamp_pdf(self, file_path, classification):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            # Create watermark
            packet = BytesIO()
            can = canvas.Canvas(packet)
            can.setFillColor(classification['color'])
            can.drawString(50, 20, f"Classification: {classification['name']} | User: {os.getlogin()}")
            can.save()
            
            # Move to beginning of StringIO buffer
            packet.seek(0)
            watermark = PdfReader(packet)
            
            # Stamp each page
            reader = PdfReader(file_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.merge_page(watermark.pages[0])
                writer.add_page(page)
            
            # Write output
            with open(file_path, "wb") as output:
                writer.write(output)
                
        except Exception as e:
            print(f"Error stamping PDF document: {e}")

    def log_action(self, file_path, action, classification_id=None):
        try:
            requests.post(f"{SERVER_URL}/api/log_document", json={
                'filename': os.path.basename(file_path),
                'path': os.path.dirname(file_path),
                'classification_id': classification_id,
                'user': os.getlogin(),
                'action': action
            })
        except Exception as e:
            print(f"Error logging action: {e}")

if __name__ == "__main__":
    event_handler = DocumentHandler()
    observer = Observer()
    
    for folder in WATCH_FOLDERS:
        if os.path.exists(folder):
            observer.schedule(event_handler, folder, recursive=True)
    
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()