# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# other packages
import numpy as np

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.Machine import Machine
from GUI.util.colors_and_symbols import *


########################################################################################################################

# The FactoryScene-Class (inheritance QGraphicsScene) manages all the 2D graphical items that are visualized inside the
# factory.

########################################################################################################################


class MachineScene(QGraphicsScene):
    def __init__(self, factory: Factory, machine: Machine, *args, **kwargs):
        super(MachineScene, self).__init__(*args, **kwargs)
        self.factory: Factory = factory
        self.machine: Machine = machine
        self.pixels = self.get_cell_size_for_grid(self.factory, self.machine.length, self.machine.width)
        self.machine_grid = self.draw_machine_grid(self.factory)
        self.input_output = self.draw_input_output()
        print(f'Inside CLASS MachineScene - PIXELS = {self.pixels}')
        print(f'Inside CLASS MachineScene - Szene = {self}')
        self.max_length = 500
        self.max_width = 500

    def draw_machine_grid(self, factory):
        no_horizontal_cells = int(int(self.machine.width) / float(factory.cell_size))
        no_vertical_cells = int(int(self.machine.length) / float(factory.cell_size))
        np_machine_scene_grid = np.zeros(shape=(no_vertical_cells, no_horizontal_cells))
        machine_scene_grid = np_machine_scene_grid.tolist()
        for i in range(no_vertical_cells):
            for j in range(no_horizontal_cells):
                machine_scene_grid[i][j] = self.addRect(self.pixels * i, self.pixels * j, self.pixels, self.pixels)
        self.machine_grid = machine_scene_grid
        return machine_scene_grid

    @staticmethod
    def get_cell_size_for_grid(factory, machine_length, machine_width):
        # av1 is an auxiliary variable to visualize the length of the factory in the grid
        av1 = int(500 // int(machine_length) // (1 / factory.cell_size))
        # print(self.av1)
        # av2 is an auxiliary variable to visualize the width of the factory in the grid
        av2 = int(500 // int(machine_width) // (1 / factory.cell_size))
        # print(self.av2)
        if av1 < av2:
            return av1
        elif av2 < av1:
            return av2
        else:
            return av1

    def draw_input_output(self):
        pos_x_input = self.machine.pos_input[0] + (self.pixels // 2)
        pos_y_input = self.machine.pos_input[1] + (self.pixels // 2)
        local_position_input_output = [0, 0]  # first is output, second is input, machine coordinates are used
        print(f'Inside CLASS MachineScene - Function draw_input - pos_x_input = {pos_x_input}')
        print(f'Inside CLASS MachineScene - Function draw_input - pos_y_input = {pos_y_input}')
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
        if self.machine.local_pos_input == self.machine.local_pos_output:
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'IF SCHLEIFE (gleiche Position)')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'IF SCHLEIFE: self.machine.pos_output[0] = {self.machine.pos_output[0]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'IF SCHLEIFE: self.machine.pos_output[1] = {self.machine.pos_output[1]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'IF SCHLEIFE: self.machine.pos_input[0] = {self.machine.pos_input[0]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'IF SCHLEIFE: self.machine.pos_input[1] = {self.machine.pos_input[1]}')
            local_position_input_output[0] = self.addRect(self.machine.local_pos_output[0] * self.pixels,
                                                          self.machine.local_pos_output[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_output)
            local_position_input_output[1] = self.addRect(self.machine.local_pos_input[0] * self.pixels,
                                                          self.machine.local_pos_input[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_input_output)
        else:
            # print(f'Inside CLASS MachineScene - Function draw_input - ELSE SCHLEIFE (verschiedene Positionen)')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'ELSE SCHLEIFE: self.machine.pos_output[0] = {self.machine.pos_output[0]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'ELSE SCHLEIFE: self.machine.pos_output[1] = {self.machine.pos_output[1]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'ELSE SCHLEIFE: self.machine.pos_input[0] = {self.machine.pos_input[0]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'ELSE SCHLEIFE: self.machine.pos_input[1] = {self.machine.pos_input[1]}')
            # print(f'Inside CLASS MachineScene - Function draw_input - '
            #       f'ELSE SCHLEIFE: self.pixels = {self.pixels}')
            local_position_input_output[0] = self.addRect(self.machine.local_pos_output[0] * self.pixels,
                                                          self.machine.local_pos_output[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_output)
            local_position_input_output[1] = self.addRect(self.machine.local_pos_input[0] * self.pixels,
                                                          self.machine.local_pos_input[1] * self.pixels,
                                                          self.pixels,
                                                          self.pixels,
                                                          brush=brush_input)
        self.input_output = local_position_input_output
        return local_position_input_output

    def delete_input_output(self):
        self.removeItem(self.input_output[0])
        self.removeItem(self.input_output[1])
