# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# other packages
import numpy as np

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.Factory import Machine
from FactoryObjects.Factory import Warehouse

########################################################################################################################

# The FactoryScene-Class (inheritance QGraphicsScene) manages all the 2D graphical items that are visualized inside the
# factory.

########################################################################################################################


class FactoryScene(QGraphicsScene):
    def __init__(self, factory: Factory, *args, **kwargs):
        super(FactoryScene, self).__init__(*args, **kwargs)
        self.factory: Factory = factory
        self.factory_grid = self.draw_factory_grid()
        self.transport_routes = []
        self.max_length = 1600
        self.max_width = 950

    def draw_factory_grid(self):
        # print("DRAWING FUNCTION: ")
        factory_color_grid = self.factory.get_color_grid()
        no_vertical_cells = int(int(self.factory.length) / float(self.factory.cell_size))
        no_horizontal_cells = int(int(self.factory.width) / float(self.factory.cell_size))
        # print(f"Anzahl horizontaler Zellen: {no_horizontal_cells}")
        # print(f"Anzahl vertikaler Zellen: {no_vertical_cells}")
        np_factory_scene_grid = np.zeros(shape=(no_vertical_cells, no_horizontal_cells))
        factory_scene_grid = np_factory_scene_grid.tolist()
        pixels = self.get_cell_size_for_grid()
        # print(pixels)
        for y in range(no_vertical_cells):
            for x in range(no_horizontal_cells):
                brush = QBrush()
                brush_color = QColor()
                brush_color.setRgb(
                    factory_color_grid[y][x][0], factory_color_grid[y][x][1], factory_color_grid[y][x][2])
                brush.setStyle(Qt.SolidPattern)
                brush.setColor(brush_color)
                factory_scene_grid[y][x] = self.addRect(pixels * y, pixels * x, pixels, pixels, brush=brush)
        self.factory_grid = factory_scene_grid
        return factory_scene_grid

    def draw_transport_routes(self):
        amount_of_factory_objects = self.factory.get_amount_of_factory_objects()
        list_of_factory_objects = self.factory.get_list_of_factory_objects()
        connections = []
        pixels = self.get_cell_size_for_grid()
        m = 1
        pen = QPen()
        pen_color = QColor()
        pen_color.setRgb(0, 0, 0)
        pen.setColor(pen_color)
        pen.setWidth(3)
        for i in range(amount_of_factory_objects):
            for j in range(amount_of_factory_objects):
                if type(list_of_factory_objects[i]) == Machine or type(list_of_factory_objects[i]) == Warehouse:
                    if type(list_of_factory_objects[j]) == Machine or type(list_of_factory_objects[j]) == Warehouse:
                        for output_product in list_of_factory_objects[i].output_products:
                            for input_product in list_of_factory_objects[j].input_products:
                                if output_product == input_product:
                                    print(f'{m}. Lieferbeziehung gefunden!')
                                    print(f'Lieferung von {list_of_factory_objects[i].name} nach '
                                          f'{list_of_factory_objects[j].name}, Geliefertes Produkt: {input_product}')
                                    print(list_of_factory_objects[i].pos_output)
                                    print(list_of_factory_objects[j].pos_input)
                                    connect_begin_x = int(
                                        list_of_factory_objects[i].pos_output[0] * pixels + (pixels/2))
                                    connect_begin_y = int(
                                        list_of_factory_objects[i].pos_output[1] * pixels + (pixels/2))
                                    connect_end_x = int(list_of_factory_objects[j].pos_input[0] * pixels + (pixels/2))
                                    connect_end_y = int(list_of_factory_objects[j].pos_input[1] * pixels + (pixels/2))
                                    connections.append(self.addLine(connect_begin_x, connect_begin_y, connect_end_x,
                                                                    connect_end_y, pen=pen))
        self.transport_routes = connections
        return connections

    def delete_transport_routes(self):
        print('Funktion aufgerufen')
        amount_of_connections = len(self.transport_routes)
        print(self.transport_routes)
        for i in range(amount_of_connections):
            self.removeItem(self.transport_routes[i])



    def get_cell_size_for_grid(self):
        # av1 is an auxiliary variable to visualize the length of the factory in the grid
        av1 = int(1600 // int(self.factory.length) // (1/self.factory.cell_size))
        # print(self.av1)
        # av2 is an auxiliary variable to visualize the width of the factory in the grid
        av2 = int(950 // int(self.factory.width) // (1/self.factory.cell_size))
        # print(self.av2)
        if av1 < av2:
            return av1
        elif av2 < av1:
            return av2
        else:
            return av1

    def get_factory_grid(self):
        return self.factory_grid

    def delete_factory_grid(self):
        # print('DELETING FUNCTION')
        no_horizontal_cells = int(int(self.factory.width) / float(self.factory.cell_size))
        no_vertical_cells = int(int(self.factory.length) / float(self.factory.cell_size))
        # print(f"Anzahl horizontaler Zellen: {no_horizontal_cells}")
        # print(f"Anzahl vertikaler Zellen: {no_vertical_cells}")
        # pixels = self.get_cell_size_for_grid(factory)
        # print(self.pixels)
        # self.factory_scene_grid = self.get_factory_grid()
        # print(self.factory_grid)
        for i in range(no_vertical_cells):
            for j in range(no_horizontal_cells):
                self.removeItem(self.factory_grid[i][j])

    def draw_machine_in_grid(self):
        pass

    def delete_machine_in_grid(self):
        pass

    def draw_machines_in_grid(self):
        pass

    def delete_machines_in_grid(self):
        pass