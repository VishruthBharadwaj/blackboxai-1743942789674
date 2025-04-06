# Company DLP System Deployment Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation Options](#installation-options)
4. [Group Policy Configuration](#group-policy-configuration)
5. [Post-Installation Tasks](#post-installation-tasks)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## System Overview
The Data Loss Prevention (DLP) system provides:
- Document classification and tracking
- USB device monitoring
- Email content scanning
- Office integration
- Centralized logging and reporting

## Prerequisites
### Hardware Requirements
- Server: 4 CPU cores, 8GB RAM, 50GB storage
- Clients: 2 CPU cores, 4GB RAM

### Software Requirements
- Windows 10/11 or Windows Server 2016+
- Microsoft Office 2016+ (for add-in)
- .NET Framework 4.8
- Python 3.8+

## Installation Options

### 1. MSI Package (Recommended for Enterprise)
```powershell
msiexec /i CompanyDLP.msi /quiet ALLUSERS=1 SERVERURL="https://dlp.yourcompany.com"
```

### 2. Scripted Installation
```powershell
.\installer.ps1 -DeploymentType "Silent" -ServerURL "https://dlp.yourcompany.com"
```

### 3. Manual Installation
```bash
python installer.py --configure
```

## Group Policy Configuration

1. Copy ADMX/ADML files to PolicyDefinitions:
   ```powershell
   Copy-Item .\gptemplates\* C:\Windows\PolicyDefinitions\
   ```

2. Configure DLP policies:
   ```powershell
   gpupdate /force
   ```

Recommended Policy Settings:
- Enable USB Monitoring: Yes
- Enable Email Monitoring: Yes  
- Classification Level: 2 (Secret)
- Server URL: https://dlp.yourcompany.com

## Post-Installation Tasks

1. Verify services are running:
   ```powershell
   Get-Service | Where-Object {$_.Name -like "*DLP*"}
   ```

2. Test document classification:
   - Create a test document in Word
   - Verify classification footer appears

3. Configure admin users:
   ```powershell
   .\dlp_admin.ps1 -AddAdmin "domain\username"
   ```

## Troubleshooting

### Common Issues
| Symptom | Solution |
|---------|----------|
| Add-in not loading | Enable Office add-ins in Trust Center |
| USB blocking fails | Verify service is running as SYSTEM |
| Email scanning skipped | Check Exchange server permissions |

### Log Locations
- Server: `C:\ProgramData\CompanyDLP\logs\`
- Client: `%LocalAppData%\CompanyDLP\client.log`

## Maintenance

### Updating
```powershell
.\dlp_update.ps1 -Version 2.1.0
```

### Monitoring
```powershell
# Check system status
.\dlp_monitor.ps1 -HealthCheck

# Generate report
.\dlp_report.ps1 -Output HTML
```

## Support
Contact IT Security Team:
- Email: dlp-support@yourcompany.com
- Phone: x5555
- Emergency Pager: 555-1212