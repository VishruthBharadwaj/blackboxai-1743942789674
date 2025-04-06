
Built by https://www.blackbox.ai

---

```markdown
# Company Data Loss Prevention (DLP) System

## Project Overview
The Company DLP System is designed to prevent data loss by providing features such as document classification, USB device monitoring, email content scanning, and centralized logging. The solution incorporates a web-based dashboard for monitoring and managing document classifications, as well as client agents for monitoring file actions on user machines.

## Installation
To install the DLP system, run the installer script provided in the project. This script will set up the server and client components. Follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/company-dlp.git
   cd company-dlp
   ```

2. Run the installer:
   ```bash
   python installer.py
   ```

3. Follow the on-screen instructions to complete the installation.

## Usage
Once installed, you can run the DLP server by executing the `app.py` script. This will start the web application that provides an interface for managing document classifications and viewing logs.

```bash
python app.py
```

You can access the admin interface at [http://localhost:5000](http://localhost:5000).

### Client Agents
Client components like `client_agent.py`, `email_monitor.py`, and `usb_monitor.py` should be set up to run on user machines to ensure monitoring of document creation, email sending, and USB activities. You can run these scripts using Python directly.

## Features
- **Document Classification**: Classify documents based on their sensitivity.
- **Dashboard**: View statistics and recent activities related to document logs.
- **USB Device Monitoring**: Block USB devices containing classified documents.
- **Email Scanning**: Detect and block emails with classified attachments.
- **Logging**: Centralized logging of actions like document creation, emailing, and USB usage.

## Dependencies
The project requires the following Python packages, which can be found in `requirements.txt`:

```plaintext
flask==2.3.2
flask-sqlalchemy==3.0.3
werkzeug==2.3.6
python-dotenv==1.0.0
watchdog==3.0.0
python-docx==0.8.11
pypdf2==3.0.1
exchangelib==4.7.2
imaplib2==3.5
pywin32==306; sys_platform == "win32"
```

Make sure to install them using pip before running the application:
```bash
pip install -r requirements.txt
```

## Project Structure
```plaintext
project-root/
│
├── app.py                     # Main application file, sets up Flask server and routes
├── client_agent.py            # Client script for monitoring document creation
├── email_monitor.py           # Monitors outgoing emails for classified content
├── usb_monitor.py             # Monitors USB devices for classified documents
├── installer.py               # Installs the system and sets up directories
├── requirements.txt           # List of Python dependencies
└── office_addin/              # Directory for Office add-in files
```

You can extend functionality or modify existing features as per your requirements.

## Support
For issues, please contact the IT Security Team:
- Email: dlp-support@yourcompany.com
- Phone: x5555
```