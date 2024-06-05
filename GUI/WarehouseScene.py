# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# other packages
import numpy as np

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.Warehouse import Warehouse
from GUI.util.colors_and_symbols import *


########################################################################################################################

# The FactoryScene-Class (inheritance QGraphicsScene) manages all the 2D graphical items that are visualized inside the
# factory.

########################################################################################################################


class WarehouseScene(QGraphicsScene):
    def __init__(self, factory: Factory, warehouse: Warehouse, *args, **kwargs):
        super(WarehouseScene, self).__init__(*args, **kwargs)
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        # self.symbol_input = SYMBOL_INPUT
        # self.symbol_output = SYMBOL_OUTPUT
        # self.symbol_input_output = SYMBOL_INPUT_OUTPUT
        # self.machine_length = machine_length
        # self.machine_width = machine_width
        self.pixels = self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width)
        self.warehouse_grid = self.draw_warehouse_grid(self.factory)
        self.input_output = self.draw_input_output()
        print(f'Inside CLASS WarehouseScene - PIXELS = {self.pixels}')
        print(f'Inside CLASS WarehouseScene - Szene = {self}')
        self.max_length = 500
        self.max_width = 500

    def draw_warehouse_grid(self, factory):
        no_horizontal_cells = int(int(self.warehouse.width) / float(factory.cell_size))
        no_vertical_cells = int(int(self.warehouse.length) / float(factory.cell_size))
        np_warehouse_scene_grid = np.zeros(shape=(no_vertical_cells, no_horizontal_cells))
        warehouse_scene_grid = np_warehouse_scene_grid.tolist()
        for i in range(no_vertical_cells):
            for j in range(no_horizontal_cells):
                warehouse_scene_grid[i][j] = self.addRect(self.pixels * i, self.pixels * j, self.pixels, self.pixels)
        self.warehouse_grid = warehouse_scene_grid
        return warehouse_scene_grid

    @staticmethod
    def get_cell_size_for_grid(factory, warehouse_length, warehouse_width):
        # av1 is an auxiliary variable to visualize the length of the factory in the grid
        av1 = int(500 // int(warehouse_length) // (1 / factory.cell_size))
        # print(self.av1)
        # av2 is an auxiliary variable to visualize the width of the factory in the grid
        av2 = int(500 // int(warehouse_width) // (1 / factory.cell_size))
        # print(self.av2)
        if av1 < av2:
            return av1
        elif av2 < av1:
            return av2
        else:
            return av1

    def draw_input_output(self):
        local_position_input_output = [0, 0]  # first is output, second is input, machine coordinates are used
        pen = QPen()
        pen.setWidth(2)
        brush_input = QBrush()
        brush_input.setStyle(Qt.SolidPattern)
        brush_input.setColor(Qt.red)
        brush_output = QBrush()
        brush_output.setStyle(Qt.SolidPattern)
        brush_output.setColor(Qt.green)
        brush_input_output = QBrush()
        brush_input_output.setStyle(Qt.DiagCrossPattern)
        brush_input_output.setColor(Qt.red)
        if self.warehouse.local_pos_input == self.warehouse.local_pos_output:
            """print(f'Inside CLASS WarehouseScene - Function draw_input - IF SCHLEIFE (gleiche Position)')
            print(f'Inside CLASS WarehouseScene - Function draw_input - IF SCHLEIFE: '
                  f'self.machine.pos_output[0] = {self.warehouse.pos_output[0]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - IF SCHLEIFE: '
                  f'self.machine.pos_output[1] = {self.warehouse.pos_output[1]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - IF SCHLEIFE: '
                  f'self.machine.pos_input[0] = {self.warehouse.pos_input[0]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - IF SCHLEIFE: '
                  f'self.machine.pos_input[1] = {self.warehouse.pos_input[1]}')"""
            local_position_input_output[0] = self.addRect(self.warehouse.local_pos_output[0] * self.pixels,
                                                          self.warehouse.local_pos_output[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_output)
            local_position_input_output[1] = self.addRect(self.warehouse.local_pos_input[0] * self.pixels,
                                                          self.warehouse.local_pos_input[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_input_output)
        else:
            """print(f'Inside CLASS WarehouseScene - Function draw_input - ELSE SCHLEIFE (verschiedene Positionen)')
            print(f'Inside CLASS WarehouseScene - Function draw_input - '
                  f'ELSE SCHLEIFE: self.warehouse.pos_output[0] = {self.warehouse.pos_output[0]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - '
                  f'ELSE SCHLEIFE: self.warehouse.pos_output[1] = {self.warehouse.pos_output[1]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - '
                  f'ELSE SCHLEIFE: self.warehouse.pos_input[0] = {self.warehouse.pos_input[0]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - '
                  f'ELSE SCHLEIFE: self.warehouse.pos_input[1] = {self.warehouse.pos_input[1]}')
            print(f'Inside CLASS WarehouseScene - Function draw_input - '
                  f'ELSE SCHLEIFE: self.pixels = {self.pixels}')"""
            local_position_input_output[0] = self.addRect(self.warehouse.local_pos_output[0] * self.pixels,
                                                          self.warehouse.local_pos_output[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_output)
            local_position_input_output[1] = self.addRect(self.warehouse.local_pos_input[0] * self.pixels,
                                                          self.warehouse.local_pos_input[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_input)
        self.input_output = local_position_input_output
        return local_position_input_output

    def delete_input_output(self):
        self.removeItem(self.input_output[0])
        self.removeItem(self.input_output[1])
