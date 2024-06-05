'''

The colors module contains all the colors used for displaying the Factory

'''

from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Qt

# COLORS
BLACK = QColor(0, 0, 0)
WHITE = QColor(255, 255, 255)
RED = QColor(255, 0, 0)
GREEN = QColor(0, 255, 0)
BLUE = QColor(0, 0, 255)
YELLOW = QColor(255, 255, 0)
PURPLE = QColor(128, 0, 128)
ORANGE = QColor(255, 165 ,0)
GREY = QColor(128, 128, 128)
TURQUOISE = QColor(64, 224, 208)

COLOR_EMPTY_CELL = QColor(255, 255, 255)
COLOR_WAY = QColor(191, 191, 191)
COLOR_MACHINE = QColor(100, 100, 255) # lila
COLOR_LOADING_STATION = QColor(255, 230, 0) # yellow
COLOR_WAREHOUSE = QColor(255, 150, 100) # orange
COLOR_INPUT = QColor(255, 100, 100) # red
COLOR_OUTPUT = QColor(100, 255, 100) # green
COLOR_INPUT_OUTPUT = QColor(255, 0, 220) # pink

# BRUSHES
REDBRUSH = QBrush(Qt.red)

# SYMBOLS
SYMBOL_OUTPUT = "⨂"
SYMBOL_INPUT = "⨀"
SYMBOL_INPUT_OUTPUT = "⨷"