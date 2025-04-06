import os
import sys
import subprocess
import shutil
from pathlib import Path

class DLPInstaller:
    def __init__(self):
        self.install_dir = Path('C:\\Program Files\\CompanyDLP' if sys.platform == 'win32' 
                              else '/opt/companydlp')
        self.config = {
            'server_port': 5000,
            'db_path': str(self.install_dir / 'data' / 'dlp.db'),
            'log_dir': str(self.install_dir / 'logs')
        }

    def run(self):
        print("Company DLP System Installer")
        print("============================")
        
        self.create_directories()
        self.install_python_dependencies()
        self.copy_files()
        self.configure_services()
        self.initialize_database()
        
        print("\nInstallation completed successfully!")
        print(f"DLP system installed to: {self.install_dir}")
        print("Access the admin interface at: http://localhost:5000")

    def create_directories(self):
        print("\nCreating installation directories...")
        (self.install_dir / 'data').mkdir(parents=True, exist_ok=True)
        (self.install_dir / 'logs').mkdir(parents=True, exist_ok=True)
        (self.install_dir / 'client').mkdir(parents=True, exist_ok=True)

    def install_python_dependencies(self):
        print("\nInstalling Python dependencies...")
        requirements = [
            'flask==2.3.2',
            'flask-sqlalchemy==3.0.3',
            'werkzeug==2.3.6',
            'python-dotenv==1.0.0',
            'watchdog==3.0.0',
            'python-docx==0.8.11',
            'pypdf2==3.0.1',
            'exchangelib==4.7.2',
            'imaplib2==3.5',
            'pywin32==306; sys_platform == "win32"'
        ]
        
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + requirements, check=True)

    def copy_files(self):
        print("\nCopying system files...")
        # Server files
        shutil.copy('app.py', self.install_dir)
        shutil.copy('requirements.txt', self.install_dir)
        shutil.copy('.env', self.install_dir)
        
        # Client components
        shutil.copy('client_agent.py', self.install_dir / 'client')
        shutil.copy('email_monitor.py', self.install_dir / 'client')
        shutil.copy('usb_monitor.py', self.install_dir / 'client')
        
        # Office add-in
        shutil.copytree('office_addin', self.install_dir / 'office_addin', dirs_exist_ok=True)

    def configure_services(self):
        print("\nConfiguring system services...")
        if sys.platform == 'win32':
            self._configure_windows_services()
        else:
            self._configure_linux_services()

    def _configure_windows_services(self):
        # Create Windows service for the DLP server
        service_script = f"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os

class DLPService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'CompanyDLP'
    _svc_display_name_ = 'Company Data Loss Prevention Service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        os.chdir(r'{self.install_dir}')
        subprocess.Popen([r'{sys.executable}', 'app.py'])

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DLPService)
        """
        
        with open(self.install_dir / 'dlp_service.py', 'w') as f:
            f.write(service_script)
            
        # Install the service
        subprocess.run([
            sys.executable, str(self.install_dir / 'dlp_service.py'), 'install'
        ], check=True)
        
        # Start the service
        subprocess.run([
            sys.executable, str(self.install_dir / 'dlp_service.py'), 'start'
        ], check=True)

    def _configure_linux_services(self):
        # Create systemd service file
        service_file = f"""
[Unit]
Description=Company Data Loss Prevention Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.install_dir}
ExecStart={sys.executable} app.py
Restart=always

[Install]
WantedBy=multi-user.target
        """
        
        with open('/etc/systemd/system/company-dlp.service', 'w') as f:
            f.write(service_file)
            
        # Reload and enable the service
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', 'company-dlp.service'], check=True)
        subprocess.run(['systemctl', 'start', 'company-dlp.service'], check=True)

    def initialize_database(self):
        print("\nInitializing database...")
        subprocess.run([
            sys.executable, str(self.install_dir / 'app.py'), 'initdb'
        ], check=True)

if __name__ == "__main__":
    installer = DLPInstaller()
    installer.run()