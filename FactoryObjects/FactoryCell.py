# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from GUI.util.colors_and_symbols import *
from FactoryObjects.Factory import Factory

########################################################################################################################

# The FactoryCell-Class is a class for every cell inside the factory grid
# It contains all the necessary information of the Cell

########################################################################################################################

class FactoryCell:
    def __init__(self, factory: Factory):
        self.factory: Factory = factory
        self.cell_length = factory.cell_size
        self.cell_width = factory.cell_size
        self.color = COLOR_EMPTY_CELL
        self.symbol = None
        self.factory_grid_layout = factory.factory_grid_layout
        self.type = None

    def is_machine(self):
        self.color = COLOR_MACHINE

    def is_way(self):
        self.color = COLOR_WAY

    def is_source(self):
        self.color = COLOR_MACHINE
        self.symbol = SYMBOL_SOURCE

    def is_drain(self):
        self.color = COLOR_MACHINE
        self.symbol = SYMBOL_DRAIN

    def is_drain_source(self):
        self.color = COLOR_MACHINE
        self.symbol = SYMBOL_DRAIN_SOURCE
    def is_loading_station(self):
        self.color = COLOR_CHARGING_STATION
        pass

    def is_storage(self):
        self.color = COLOR_STORAGE
        pass
