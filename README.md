# SecureIOT
### Detection of Unencrypted Traffic and Automated Encryption Recommendation System for IoT Devices and Legacy Systems

SecureIOT is a cloud-enabled, mobile-ready, offline-storage compatible Web Application.

## Overview  
In today’s interconnected world, ensuring secure communication is vital—yet many IoT devices and legacy systems still transmit data without encryption, leaving them vulnerable to cyberattacks. This project aims to **detect unencrypted traffic** in real-time and provide **automated recommendations for implementing encryption** to enhance network security.  

By identifying vulnerabilities in both modern and outdated systems, this project strives to reduce the risk of data breaches and bolster overall system reliability.

---

## Objectives  
- **Detect Unencrypted Traffic**: Monitor and identify unencrypted network traffic in real-time.  
- **Automated Recommendations**: Suggest encryption mechanisms tailored to the device or system.  
- **Support for IoT and Legacy Systems**: Provide practical solutions for devices with limited processing power or older architectures.  
- **User-Friendly Dashboard**: Visualize traffic insights and vulnerabilities for better decision-making.  

---

## Features  
- **Traffic Analysis**: Scans network traffic to detect unencrypted data streams.  
- **Encryption Recommendations**: Automated guidance for securing identified vulnerabilities using appropriate encryption techniques.  
- **IoT Device Compatibility**: Optimized for resource-constrained IoT devices.  
- **Support for Legacy Systems**: Addresses challenges unique to older infrastructure.  
- **Real-Time Monitoring**: Live traffic scanning with actionable alerts.  

---

## How It Works  
1. **Traffic Detection**: The system scans network packets for unencrypted traffic patterns.  
2. **Classification**: Uses algorithms to categorize the devices and their encryption states.  
3. **Recommendation Engine**: Provides actionable steps and compatible encryption methods tailored to each device/system.  
4. **Dashboard**: Displays findings in a clear and concise manner for end users.  

---

## Tech Stack  
- **Programming Language**: Python  
- **Traffic Analysis**: Wireshark, Scapy, or Python-nmap  
- **Dashboard Framework**: Flask/Django with a Bootstrap UI  
- **Database**: SQLite or PostgreSQL (for storing traffic logs and recommendations)  
- **Machine Learning**: Optional for advanced traffic classification  

---

## Installation
---

**Clone the repository**:  
```bash
git clone https://github.com/Vikas-Kshirsagar/SecureIOT
cd SecureIOT
```

**Install dependencies**:  
```
pip install -r requirements.txt
```

**Run the application**:  
```
python app.py
```

**Access the Dashboard**:  
```
http://localhost:5000
```

## Development & Contributing

Contributions are welcome! If you want to contribute:
1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Submit a pull request with a detailed description of your changes.

## License
MIT

## Contact
If you have any questions or feedback, feel free to reach out at vikas.kshirsagar@outlook.com.

## Acknowledgments
Special thanks to the tools and resources that supported this project:
- Wireshark
- Scapy
- Python Nmap

## Screenshots

**Development Environment**:

![image](/static/images/Development_Environment.png)

**Dashboard**:

![image](/static/images/Dashboard.png)

**packet Capture**:

![image](/static/images/Packet_Capture.png)

**Recommendations**:

![image](/static/images/Recommendations.png)

**Firmware Recommendation**:

![image](/static/images/Firmware_Recommendation.png)
