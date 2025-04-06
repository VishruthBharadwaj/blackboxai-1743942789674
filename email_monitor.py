import os
import re
from exchangelib import Credentials, Account, Configuration, Message
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import time

class EmailDLPHandler:
    def __init__(self):
        self.server_url = "http://localhost:5000"
        self.email_account = None
        
    def connect_email(self, email, password, server):
        try:
            credentials = Credentials(email, password)
            config = Configuration(server=server, credentials=credentials)
            self.email_account = Account(
                primary_smtp_address=email,
                config=config,
                autodiscover=False,
                access_type='delegate'
            )
            return True
        except Exception as e:
            print(f"Email connection error: {e}")
            return False

    def check_outgoing_emails(self):
        if not self.email_account:
            return
            
        for item in self.email_account.sent.all().order_by('-datetime_received')[:10]:
            if not hasattr(item, 'is_processed'):
                self.process_email(item)
                item.is_processed = True
                item.save()

    def process_email(self, email):
        try:
            # Check attachments
            for attachment in email.attachments:
                if attachment.name.lower().endswith(('.docx', '.xlsx', '.pptx', '.pdf')):
                    temp_path = f"/tmp/{attachment.name}"
                    with open(temp_path, 'wb') as f:
                        f.write(attachment.content)
                    
                    # Check if document is classified
                    classification = self.check_document_classification(temp_path)
                    if classification and classification['level'] in ['Top Secret', 'Secret']:
                        # Block sending and notify admin
                        self.block_email(email, attachment.name, classification)
                        return
                    
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"Email processing error: {e}")

    def check_document_classification(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read(5000).decode('utf-8', errors='ignore')
                match = re.search(r'Classification:\s*(.*?)\s*\|', content)
                if match:
                    classification = match.group(1)
                    return {
                        'level': classification,
                        'file': os.path.basename(file_path)
                    }
        except Exception as e:
            print(f"Document check error: {e}")
        return None

    def block_email(self, email, filename, classification):
        try:
            # Move email to drafts
            email.move_to_folder(self.email_account.drafts)
            
            # Notify admin
            admin_msg = Message(
                account=self.email_account,
                subject="DLP Alert: Blocked Email with Classified Attachment",
                body=f"""A classified document was blocked from being sent:
                
File: {filename}
Classification: {classification['level']}
Sender: {email.sender.email_address}
Recipients: {', '.join(r.email_address for r in email.to_recipients)}
                
The email has been moved to drafts.""",
                to_recipients=['admin@yourcompany.com']
            )
            admin_msg.send()
            
            # Notify sender
            sender_msg = Message(
                account=self.email_account,
                subject="Action Required: Email Blocked Due to Classified Content",
                body=f"""Your email containing '{filename}' was not sent because it contains classified information ({classification['level']}).

Please contact IT security if you believe this is an error.""",
                to_recipients=[email.sender.email_address]
            )
            sender_msg.send()
            
            # Log to DLP system
            requests.post(f"{self.server_url}/api/log_document", json={
                'filename': filename,
                'path': 'email_attachment',
                'classification_id': self.get_classification_id(classification['level']),
                'user': email.sender.email_address,
                'action': 'email_blocked'
            })
            
        except Exception as e:
            print(f"Email blocking error: {e}")

    def get_classification_id(self, level):
        # Map classification levels to IDs
        levels = {
            'Top Secret': 1,
            'Secret': 2,
            'Confidential': 3,
            'Public': 4
        }
        return levels.get(level)

def main():
    handler = EmailDLPHandler()
    if not handler.connect_email(
        os.getenv('DLP_EMAIL'),
        os.getenv('DLP_EMAIL_PASSWORD'),
        os.getenv('EXCHANGE_SERVER')
    ):
        print("Failed to connect to email server")
        return

    print("Email DLP monitoring started...")
    while True:
        handler.check_outgoing_emails()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()