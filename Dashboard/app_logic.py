# FILE: app_logic.py
import sys
import asyncio
import websockets
import json
import requests
from functools import partial

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLabel, QMessageBox, QDialog, QLineEdit, QComboBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import (
    Qt, QSettings, QThread, pyqtSignal, QAbstractTableModel, QModelIndex
)

# ===================================================================
# 1. Internationalization (i18n) Setup
# ===================================================================
translations = {
    "en": {
        "window_title": "Hybrid Trading Dashboard",
        "connecting": "Connecting...",
        "connection_status_connected": "Connected to server",
        "connection_status_disconnected": "Disconnected",
        "connection_status_connecting": "Attempting to connect...",
        "main_chart_symbol": "Main Chart Symbol: {symbol}",
        "total_pl": "Total P/L: ",
        "close_all": "Close All",
        "close_profits": "Close Profits",
        "close_losses": "Close Losses",
        "settings": "Settings",
        "confirm_op": "Confirm Operation",
        "confirm_close_all": "Are you sure you want to close all trades?",
        "confirm_close_profits": "Are you sure you want to close all profitable trades?",
        "confirm_close_losses": "Are you sure you want to close all losing trades?",
        "confirm_close_ticket": "Are you sure you want to close trade with ticket {ticket}?",
        "command_error_title": "Connection Error",
        "command_error_message": "Command could not be sent to the server. Please check the server connection and status.",
        "be_fail_title": "Operation Failed",
        "be_fail_message": "Break-even is only possible for trades in profit.",
        "table_header_ticket": "Ticket",
        "table_header_symbol": "Symbol",
        "table_header_type": "Type",
        "table_header_volume": "Volume",
        "table_header_profit": "Profit",
        "table_header_atm": "ATM",
        "table_header_actions": "Actions",
        "atm_on": "Active",
        "atm_off": "Inactive",
        "action_be": "BE",
        "action_close": "Close",
        "settings_title": "Auto-Management Settings",
        "settings_trigger_label_1": "When price reaches",
        "settings_trigger_label_2": "% of target profit:",
        "settings_partial_label_1": "Close",
        "settings_partial_label_2": "% of volume (0=disabled)",
        "settings_be_on": "Break-Even: Enabled",
        "settings_be_off": "Break-Even: Disabled",
        "settings_save": "Save Settings",
        "settings_input_error_title": "Input Error",
        "settings_input_error_message": "Please enter valid numbers.",
    },
    "fa": {
        "window_title": "داشبورد معاملاتی هیبرید",
        "connecting": "در حال اتصال...",
        "connection_status_connected": "به سرور متصل است",
        "connection_status_disconnected": "اتصال قطع شده است",
        "connection_status_connecting": "در حال تلاش برای اتصال...",
        "main_chart_symbol": "نماد اصلی چارت: {symbol}",
        "total_pl": "سود/زیان کل: ",
        "close_all": "بستن همه",
        "close_profits": "بستن سودها",
        "close_losses": "بستن ضررها",
        "settings": "تنظیمات",
        "confirm_op": "تایید عملیات",
        "confirm_close_all": "آیا همه معاملات بسته شوند؟",
        "confirm_close_profits": "آیا تمام معاملات سودده بسته شوند؟",
        "confirm_close_losses": "آیا تمام معاملات در ضرر بسته شوند؟",
        "confirm_close_ticket": "آیا معامله با تیکت {ticket} بسته شود؟",
        "command_error_title": "خطا در ارتباط",
        "command_error_message": "دستور به سرور ارسال نشد. لطفاً اتصال به سرور و وضعیت آن را بررسی کنید.",
        "be_fail_title": "عملیات ناموفق",
        "be_fail_message": "ریسک-فری فقط برای معاملات در سود امکان‌پذیر است.",
        "table_header_ticket": "تیکت",
        "table_header_symbol": "نماد",
        "table_header_type": "نوع",
        "table_header_volume": "حجم",
        "table_header_profit": "سود",
        "table_header_atm": "ATM",
        "table_header_actions": "اقدامات",
        "atm_on": "فعال",
        "atm_off": "غیرفعال",
        "action_be": "BE",
        "action_close": "بستن",
        "settings_title": "تنظیمات مدیریت خودکار",
        "settings_trigger_label_1": "وقتی قیمت به",
        "settings_trigger_label_2": "٪ از سود هدف رسید:",
        "settings_partial_label_1": "بستن",
        "settings_partial_label_2": "درصد از حجم (0=غیرفعال)",
        "settings_be_on": "ریسک-فری کردن: فعال",
        "settings_be_off": "ریسک-فری کردن: غیرفعال",
        "settings_save": "ذخیره تنظیمات",
        "settings_input_error_title": "خطای ورودی",
        "settings_input_error_message": "لطفاً اعداد معتبر وارد کنید.",
    }
}

class Translator:
    def __init__(self, settings):
        self.settings = settings
        self.language = self.settings.value("language", "fa", type=str)

    def set_language(self, lang):
        self.language = lang
        self.settings.setValue("language", lang)

    def tr(self, key, **kwargs):
        return translations.get(self.language, {}).get(key, key).format(**kwargs)

# ===================================================================
# 2. Model/View Architecture for better table management
# ===================================================================
class TradeTableModel(QAbstractTableModel):
    """
    Data model for displaying trades in a QTableView.
    This class is responsible for managing the data and notifying the view to update.
    """
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.trades = []
        self.translator = translator
        self.headers = []
        self.update_headers()

    def update_headers(self):
        self.headers = [
            self.translator.tr("table_header_ticket"), self.translator.tr("table_header_symbol"),
            self.translator.tr("table_header_type"), self.translator.tr("table_header_volume"),
            self.translator.tr("table_header_profit"), self.translator.tr("table_header_atm"),
            self.translator.tr("table_header_actions")
        ]
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(self.headers) -1)


    def rowCount(self, parent=QModelIndex()):
        return len(self.trades)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        col = index.column()
        trade = self.trades[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(trade.get('ticket', ''))
            if col == 1: return trade.get('symbol', '')
            if col == 2: return trade.get('type', '')
            if col == 3: return f"{trade.get('volume', 0.0):.2f}"
            if col == 4: return f"{trade.get('profit', 0.0):+.2f} $"
        
        elif role == Qt.ItemDataRole.ForegroundRole and col == 4:
            return QColor("#16a34a") if trade.get('profit', 0) >= 0 else QColor("#dc2626")
            
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def update_trades(self, new_trades):
        """ This method updates the model with new data and notifies the view. """
        self.layoutAboutToBeChanged.emit()
        self.trades = new_trades
        self.layoutChanged.emit()

    def get_trade_at_row(self, row):
        return self.trades[row] if 0 <= row < len(self.trades) else None

# ===================================================================
# Other application classes and logic
# ===================================================================

def _load_stylesheet(filename):
    """ A helper function to read stylesheets from a file. """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Stylesheet file not found: {filename}")
        return ""

class SettingsDialog(QDialog):
    def __init__(self, current_settings, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setFixedSize(500, 200)
        
        self.trigger_label_1 = QLabel()
        self.trigger_edit = QLineEdit(str(current_settings.get("triggerPercent", 40.0)))
        self.trigger_label_2 = QLabel()
        
        self.partial_label_1 = QLabel()
        self.partial_edit = QLineEdit(str(current_settings.get("closePercent", 50.0)))
        self.partial_label_2 = QLabel()

        self.be_button = QPushButton()
        self.be_button.setCheckable(True)
        self.be_button.setChecked(current_settings.get("moveToBE", True))
        self.be_button.clicked.connect(self.update_be_button_style)
        
        self.save_button = QPushButton()
        self.save_button.setObjectName("SaveBtn")
        self.save_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(self.trigger_label_1)
        trigger_layout.addWidget(self.trigger_edit)
        trigger_layout.addWidget(self.trigger_label_2)
        
        partial_layout = QHBoxLayout()
        partial_layout.addWidget(self.partial_label_1)
        partial_layout.addWidget(self.partial_edit)
        partial_layout.addWidget(self.partial_label_2)
        
        be_layout = QHBoxLayout()
        be_layout.addWidget(self.be_button)
        be_layout.addStretch()
        
        layout.addLayout(trigger_layout)
        layout.addLayout(partial_layout)
        layout.addLayout(be_layout)
        layout.addStretch()
        layout.addWidget(self.save_button)

        self.retranslate_ui()
        self.apply_theme(parent.is_light_theme())


    def retranslate_ui(self):
        self.setWindowTitle(self.translator.tr("settings_title"))
        self.trigger_label_1.setText(self.translator.tr("settings_trigger_label_1"))
        self.trigger_label_2.setText(self.translator.tr("settings_trigger_label_2"))
        self.partial_label_1.setText(self.translator.tr("settings_partial_label_1"))
        self.partial_label_2.setText(self.translator.tr("settings_partial_label_2"))
        self.save_button.setText(self.translator.tr("settings_save"))
        self.update_be_button_style()

    def update_be_button_style(self):
        is_light = self.parent().is_light_theme()
        if self.be_button.isChecked():
            self.be_button.setText(self.translator.tr("settings_be_on"))
            self.be_button.setStyleSheet(f"background-color: {'#16a34a' if is_light else '#22c55e'};")
        else:
            self.be_button.setText(self.translator.tr("settings_be_off"))
            self.be_button.setStyleSheet("background-color: #6b7280;")

    def get_settings(self):
        try:
            trigger = float(self.trigger_edit.text() or 0)
            partial = float(self.partial_edit.text() or 0)
            return {"triggerPercent": trigger, "moveToBE": self.be_button.isChecked(), "closePercent": partial}
        except ValueError:
            QMessageBox.warning(self, self.translator.tr("settings_input_error_title"), self.translator.tr("settings_input_error_message"))
            return None
            
    def apply_theme(self, is_light):
        self.setStyleSheet(_load_stylesheet("light.qss") if is_light else _load_stylesheet("dark.qss"))
        self.update_be_button_style()

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True

    async def listen(self):
        uri = "ws://127.0.0.1:5000"
        while self.running:
            try:
                self.connection_status_changed.emit("connecting")
                async with websockets.connect(uri) as websocket:
                    self.connection_status_changed.emit("connected")
                    while self.running:
                        message = await websocket.recv()
                        self.message_received.emit(json.loads(message))
            except Exception as e:
                self.connection_status_changed.emit("disconnected")
                if self.running:
                    await asyncio.sleep(3)

    def run(self):
        asyncio.run(self.listen())

    def stop(self):
        self.running = False
        # A small delay to allow the listen loop to exit
        self.msleep(100) 


def send_command(payload):
    """ Sends a command to the server and returns the success status. """
    API_URL = "http://127.0.0.1:5000/command"
    try:
        print(f"[API Client] 📤 Sending command: {payload}")
        response = requests.post(API_URL, json=payload, timeout=2)
        if response.status_code == 200:
            return True
        else:
            print(f"[API Client] ❌ Error sending command: {response.text}")
            return False
    except Exception as e:
        print(f"[API Client] ❌ Server connection error while sending command: {e}")
        return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("GeminiTrader", "HybridPanel")
        self.translator = Translator(self.settings)
        self.current_settings = {}
        self.setGeometry(100, 100, 950, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        main_layout.addWidget(self.create_header())
        
        self.trade_model = TradeTableModel(self.translator)
        self.trade_table = self.create_trade_table()
        self.trade_table.setModel(self.trade_model)
        main_layout.addWidget(self.trade_table)
        
        main_layout.addWidget(self.create_footer())
        
        self.ws_thread = WebSocketThread()
        self.ws_thread.message_received.connect(self.handle_message)
        self.ws_thread.connection_status_changed.connect(self.update_connection_status)
        self.ws_thread.start()
        
        self.load_theme()
        self.retranslate_ui()

    def handle_message(self, message):
        msg_type = message.get("type")
        if msg_type == "trade_data":
            self.update_ui(message.get("data", {}))
        elif msg_type == "settings":
            self.current_settings = message.get("data", {})

    def create_header(self):
        header_widget = QWidget(objectName="Header")
        layout = QHBoxLayout(header_widget)
        self.connection_status_label = QLabel("⚪")
        self.symbol_label = QLabel()
        self.symbol_label.setStyleSheet("font-weight: bold;")
        self.theme_toggle_btn = QPushButton("🌙")
        self.theme_toggle_btn.setObjectName("ThemeBtn")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("فارسی", "fa")
        self.lang_combo.currentIndexChanged.connect(self.change_language)

        layout.addWidget(self.connection_status_label)
        layout.addWidget(self.symbol_label)
        layout.addStretch()
        layout.addWidget(self.lang_combo)
        layout.addWidget(self.theme_toggle_btn)
        return header_widget

    def create_trade_table(self):
        """ Use QTableView instead of QTableWidget for performance. """
        table = QTableView()
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        # Set fixed widths for specific columns
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(6, 150)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(5, 100)
        return table

    def create_footer(self):
        footer_widget = QWidget(objectName="Footer")
        layout = QHBoxLayout(footer_widget)
        self.pnl_label = QLabel()
        self.pnl_value = QLabel("...")
        layout.addWidget(self.pnl_label)
        layout.addWidget(self.pnl_value)
        layout.addStretch()
        
        self.btn_close_profit = QPushButton()
        self.btn_close_loss = QPushButton()
        self.btn_close_all = QPushButton()
        self.btn_settings = QPushButton()
        
        self.btn_close_all.clicked.connect(lambda: self.confirm_and_send("close_all", self.translator.tr("confirm_close_all")))
        self.btn_close_profit.clicked.connect(lambda: self.confirm_and_send("close_profits", self.translator.tr("confirm_close_profits")))
        self.btn_close_loss.clicked.connect(lambda: self.confirm_and_send("close_losses", self.translator.tr("confirm_close_losses")))
        self.btn_settings.clicked.connect(self.open_settings_dialog)

        layout.addWidget(self.btn_close_all)
        layout.addWidget(self.btn_close_profit)
        layout.addWidget(self.btn_close_loss)
        layout.addWidget(self.btn_settings)
        return footer_widget

    def update_ui(self, data):
        """ The UI update function is now much simpler and more efficient. """
        symbol = data.get('symbol', 'N/A')
        self.symbol_label.setText(self.translator.tr("main_chart_symbol", symbol=symbol))
        
        total_pl = data.get('total_pl', 0.0)
        self.pnl_value.setText(f"{total_pl:+.2f} $")
        self.pnl_value.setObjectName("ProfitLabel" if total_pl >= 0 else "LossLabel")
        
        trades = data.get('trades', [])
        self.trade_model.update_trades(trades)
        
        has_profit = False
        has_loss = False
        for row, trade in enumerate(trades):
            if trade.get('profit', 0) > 0: has_profit = True
            if trade.get('profit', 0) < 0: has_loss = True
            self.add_action_buttons(row)
        
        self.btn_close_profit.setEnabled(has_profit)
        self.btn_close_loss.setEnabled(has_loss)

    def add_action_buttons(self, row):
        """ This function now just takes the row and reads data from the model. """
        trade = self.trade_model.get_trade_at_row(row)
        if not trade: return
        
        ticket = trade.get('ticket')
        profit = trade.get('profit')
        atm_enabled = trade.get('atm_enabled', True)
        
        # ATM Toggle Button
        model_index_atm = self.trade_model.index(row, 5)
        atm_widget = QWidget()
        atm_layout = QHBoxLayout(atm_widget); atm_layout.setContentsMargins(0,0,0,0); atm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_atm = QPushButton(self.translator.tr("atm_on") if atm_enabled else self.translator.tr("atm_off"))
        btn_atm.setObjectName("AtmOn" if atm_enabled else "AtmOff")
        btn_atm.setCheckable(True)
        btn_atm.setChecked(atm_enabled)
        btn_atm.clicked.connect(lambda state, t=ticket, b=btn_atm: self.toggle_atm_for_trade(state, t, b))
        atm_layout.addWidget(btn_atm)
        self.trade_table.setIndexWidget(model_index_atm, atm_widget)

        # Actions Buttons
        model_index_actions = self.trade_model.index(row, 6)
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget); actions_layout.setContentsMargins(5,0,5,0); actions_layout.addStretch()
        btn_be = QPushButton(self.translator.tr("action_be"))
        btn_be.setObjectName("BEBtn")
        btn_be.clicked.connect(lambda: self.handle_be_click(ticket, profit))
        btn_close = QPushButton(self.translator.tr("action_close"))
        btn_close.setObjectName("CloseBtn")
        handler = partial(self.confirm_and_send, "close", self.translator.tr("confirm_close_ticket", ticket=ticket), ticket=ticket)
        btn_close.clicked.connect(handler)
        actions_layout.addWidget(btn_be)
        actions_layout.addWidget(btn_close)
        actions_layout.addStretch()
        self.trade_table.setIndexWidget(model_index_actions, actions_widget)

    def handle_be_click(self, ticket, profit):
        if profit <= 0:
            QMessageBox.information(self, self.translator.tr("be_fail_title"), self.translator.tr("be_fail_message"))
            return
        if not send_command({"action": "breakeven", "ticket": ticket}):
            self.show_command_error()
            
    def toggle_atm_for_trade(self, state, ticket, button):
        if not send_command({"action": "toggle_atm_trade", "ticket": ticket, "atm_trade_state": state}):
            self.show_command_error()
            button.setChecked(not state) # Revert button state on failure
        else:
            button.setText(self.translator.tr("atm_on") if state else self.translator.tr("atm_off"))
            button.setObjectName("AtmOn" if state else "AtmOff")
            button.style().unpolish(button); button.style().polish(button)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.current_settings, self.translator, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            if new_settings:
                if not send_command({"action": "update_settings", "settings": new_settings}):
                    self.show_command_error()
        
    def confirm_and_send(self, action, message, ticket=0):
        reply = QMessageBox.question(self, self.translator.tr("confirm_op"), message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            payload = {"action": action}
            if ticket: payload["ticket"] = ticket
            if not send_command(payload):
                self.show_command_error()

    def show_command_error(self):
        """ Helper function to show a consistent error message. """
        QMessageBox.critical(self, self.translator.tr("command_error_title"), self.translator.tr("command_error_message"))

    def update_connection_status(self, status):
        if status == "connected": 
            self.connection_status_label.setText("�")
            self.connection_status_label.setToolTip(self.translator.tr("connection_status_connected"))
        elif status == "disconnected": 
            self.connection_status_label.setText("🔴")
            self.connection_status_label.setToolTip(self.translator.tr("connection_status_disconnected"))
        else: 
            self.connection_status_label.setText("🟡")
            self.connection_status_label.setToolTip(self.translator.tr("connection_status_connecting"))
            
    def toggle_theme(self):
        new_theme = "dark" if self.is_light_theme() else "light"
        self.settings.setValue("theme", new_theme)
        self.apply_theme(new_theme)

    def load_theme(self):
        theme = self.settings.value("theme", "light", type=str)
        self.apply_theme(theme)
        
        # Set combo box to saved language
        lang_code = self.translator.language
        index = self.lang_combo.findData(lang_code)
        if index != -1:
            self.lang_combo.setCurrentIndex(index)


    def apply_theme(self, theme_name):
        # Reading styles from .qss files
        stylesheet = _load_stylesheet("dark.qss" if theme_name == "dark" else "light.qss")
        self.setStyleSheet(stylesheet)
        self.theme_toggle_btn.setText("☀️" if theme_name == "dark" else "🌙")
            
    def is_light_theme(self):
        return self.settings.value("theme", "light", type=str) == "light"

    def change_language(self, index):
        lang_code = self.lang_combo.itemData(index)
        if lang_code and lang_code != self.translator.language:
            self.translator.set_language(lang_code)
            self.retranslate_ui()
    
    def retranslate_ui(self):
        """ Update all UI elements with the current language translations. """
        tr = self.translator.tr
        self.setWindowTitle(tr("window_title"))
        self.symbol_label.setText(tr("connecting"))
        self.update_connection_status(self.ws_thread.connection_status_changed.emit) # Re-evaluate tooltip
        
        # Footer
        self.pnl_label.setText(tr("total_pl"))
        self.btn_close_all.setText(tr("close_all"))
        self.btn_close_profit.setText(tr("close_profits"))
        self.btn_close_loss.setText(tr("close_losses"))
        self.btn_settings.setText(tr("settings"))

        # Table Headers
        self.trade_model.update_headers()
        
        # Force a repaint of the table to update widgets inside
        self.update_ui(data={"trades": self.trade_model.trades, "total_pl": 0})


    def closeEvent(self, event):
        self.ws_thread.stop()
        self.ws_thread.wait() # Wait for thread to finish
        super().closeEvent(event)
