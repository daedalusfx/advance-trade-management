# FILE: main.py
import sys
from PyQt6.QtWidgets import QApplication
from app_logic import MainWindow

if __name__ == "__main__":
    """
The main starting point of the program
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())