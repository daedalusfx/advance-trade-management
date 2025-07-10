# 🧠 Advanced Hybrid Trade Management (ATM)

> 🌐  Languages | زبان‌ها: [English](README.md) | [فارسی](README_fa.md)

🎯 **MetaTrader Expert Advisor** for managing open trades 

---

![Dashboard Screenshot](https://github.com/daedalusfx/advance-trade-management/blob/main/screenshouts/darkmoden.png
)
![Dashboard Screenshot](https://github.com/daedalusfx/advance-trade-management/blob/main/screenshouts/darkmodfa.png)
![Dashboard Screenshot](https://github.com/daedalusfx/advance-trade-management/blob/main/screenshouts/lightmod.png)

An advanced trade management tool that combines the power and speed of MQL5 execution with the flexibility and beauty of a modern user interface written in Python. This project allows you to monitor and manage your trades live via a beautiful and interactive desktop dashboard.

---

## ✨ Key Features

* **Hybrid Architecture:** Time-sensitive logic in MQL5 for maximum execution speed, and a powerful Python interface for the best user experience.
* **Live Dashboard:** View all open trades, instant profit and loss, and overall account status in a clean and minimal interface.
* **Auto Trade Management:**
* **Auto Breakeven:** Automatically move the stop-loss to the entry point based on the target profit percentage.
* **Auto Partial Exit:** Close a percentage of the trade volume to lock in profit.
* **Full Manual Control:** Send instant commands (Close Trade, Close All, Close Profit/Loss) from the Python dashboard to MetaTrader.
* **Dynamic Settings:** Change and save auto management rules live from the dashboard, without having to recompile the Expert Advisor.
* **Instantaneous communication:** Using websockets for instant and lag-free dashboard updates.

---

## 🏗️ System architecture

The project uses a three-tier client-server architecture to achieve the best performance and flexibility:

1. **MQL5 Expert Advisor (Smart Operator):**
* Runs on MetaTrader 5.
* Responsible for fast and direct execution of trading orders.
* Contains time-sensitive logic (such as `ProcessAutoManagement`).
* Sends raw account data to the server and receives rules and commands from it.

2. **Node.js server (communication bridge):**
* A lightweight and fast server that acts as an intermediary.
* Receives raw data from MQL5, converts it to JSON format, and broadcasts it to the Python dashboard via websockets.
* Receives commands and settings from the Python Dashboard and queues them for the MQL5 Expert Advisor.

Three. **Python Dashboard (Command Center):**
* A desktop application built with PyQt6.
* Is your main user interface for monitoring and management.
* Connects to the websocket server and displays live data.
* Sends commands and settings to the server.

[Python Dashboard (UI)] <--- (WebSocket) ---> [Node.js Server (API)] <--- (HTTP) ---> [MQL5 Expert Advisor (Engine)]

---

## 🛠️ Installation and Setup

To run this system, you need to setup all three parts separately.

### Prerequisites

* **MetaTrader 5** software
* **Node.js** (version 14 or higher)
* **Python** (version 3.8 or higher)

### Step 1: Setting up the Node.js server

1. Go to the ``server`` folder.
2. Install the required packages with ``npm``:
```bash
npm install express ws
```
3. Run the server:
```bash
node server.js
```
You should see the message `🚀 Final server is running...`.

### Step 2: Setting up the MQL5 Expert Advisor

1. Copy the ``hybrid_expert_final.mq5` file to the ``MQL5/Experts` folder in your MetaTrader installation.
2. Open MetaTrader and go to the ``Expert Advisors`` tab from the ``Tools -> Options`` menu.
3. Check the box **`Allow WebRequest for listed URL`**.
4. Add the address `http://127.0.0.1:5000` to the list of allowed addresses.
5. Compile the Expert Advisor in MetaEditor and run it on the chart of your choice.

### Step 3: Setting up the Python Dashboard

1. Go to the `dashboard` folder.
2. It is recommended to create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # on Linux or macOS
venv\Scripts\activate # on Windows
```
3. Install the required packages with `pip`:
```bash
pip install PyQt6 websockets requests
```
4. Run the dashboard:
```bash
python main_app.py
```

Your dashboard should now open and display live data from MetaTrader.

---

## 🚀 How to use

* **Monitoring:** Easily view your open trades and total profit and loss.
* **Manual management:** Use the "Close", "Close All", "Close Profit/Loss" buttons to quickly manage your trades.
* **Automatic management:**
1. Click the **"Settings"** button.
2. Define and save your auto-management rules (trigger percentage, risk-free and partial volume closing).
3. Make sure that the **"Auto: On"** button in the dashboard header is enabled.
4. The Expert Advisor will automatically manage your trades based on the defined rules.

---

## 📜 License

This project is released under the **GNU General Public License v3.0**. For more information, read the `LICENSE` file.

---

## 🤝 Contributions and Future Ideas

We are honored by your participation in the development of this project. You can contribute to this project by submitting a Pull Request or filing an Issue.

Some ideas for future development:
* Add advanced Trailing Stop functionality.
* Add an account statistics and performance dashboard.
* Build
Web or mobile version for dashboard.
* Added risk management functionality for prop accounts.

## Changelog
This version uses a stable architecture based on **Short Polling HTTP**, where the Expert Advisor prevents data transmission interference with an internal queue mechanism.

---

### [Version 2.5.0] - Stable Polling Architecture with State Management - (Current Date)

This version focuses on connection stability, data corruption prevention, and adding full transaction management logic.

---
### Expert Advisor (`api.c`)

#### Improvements (Changed)
- **Non-blocking data transmission architecture:** To solve the problem of web request interference and data corruption, an internal queue mechanism (`g_data_queue`) and status flag (`g_is_sending`) were implemented. The Expert Advisor now queues data and sends it in a controlled manner.
- **Full ATM status management:** Full logic for enabling/disabling auto-management for each trade individually (`ToggleAtmForTicket`) has been implemented.
- **Migration to JSON format:** The data exchange format with the server has been completely changed to standard JSON.

#### Features (Added)
- **Comprehensive auto-management logic (`ProcessAutoManagement`):** Advanced features such as closing a portion of the volume, automatic risk-freeing, and executing rules based on the target profit percentage have been added to the Expert Advisor.
- **Stop Loss status persistence:** Initial stop losses of trades are saved in a `.dat` file so that information is not lost when the Expert Advisor is restarted.

#### Bug Fixes (Fixed)
- **Fixed `Content-Length` bug:** The critical issue that caused JSON parsing error on the server has been completely resolved by removing the `\0` character from the end of the sent data.

---
### Server (`server.js`)

#### Improvements (Changed)
- **Full support for new commands:** The server has been updated to receive and handle all new commands sent from the dashboard (such as `update_settings`, `toggle_auto`, etc.).
- **Direct JSON reception:** The server has been optimized to accept JSON data directly from the expert and no longer needs to parse custom text strings.

#### Features (Added)
- **Two-way communication with the dashboard:** Using WebSocket, data received from the expert is sent to all connected dashboards in real time.
- **Settings Management:** An `endpoint` has been added to receive and update the settings of the automated management via the dashboard.

---
### Python Dashboard (`app.py`)

*(This log is based on your previous files and is fully compatible with this version of the Expert Advisor and the server)*

#### Improvements (Changed)
- **Table architecture changed to `Model/View`:** The trade display table has been rewritten to increase performance and stability.
- **Styles moved to `.qss` files:** CSS codes have been moved to external files for better readability.

#### Bug Fixes (Fixed)
- **App Crash Fix:** The issue of the app crashing when clicking the "Close Trade" button has been fixed.
- **Error Feedback Added:** Now the user is notified with an error message if the order submission fails.