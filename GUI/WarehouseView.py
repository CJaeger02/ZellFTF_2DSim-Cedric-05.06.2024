# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.Factory import Warehouse
from GUI.util.colors_and_symbols import *


########################################################################################################################

# The FactoryView-Class (inheritance QGraphicsView) visualizes the contents of the FactoryScene.

########################################################################################################################

class WarehouseView(QGraphicsView):
    def __init__(self, factory: Factory, warehouse: Warehouse, parent=None) -> None:
        print('OPENED MACHINE VIEW:')
        super(WarehouseView, self).__init__(parent)
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        self.mouse_x_pos = 0
        self.mouse_y_pos = 0
        self.column = 0
        self.row = 0
        self.pixels = self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width)
        # self.mousePressEvent = self.get_column_and_row
        # self.machine_length = machine_length
        # self.machine_width = machine_width
        self.setFixedSize(503, 503)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.context_menu = QMenu(self)
        add_input = self.context_menu.addAction('Input')
        add_output = self.context_menu.addAction('Output')

        add_input.triggered.connect(self.add_input_clicked)
        add_output.triggered.connect(self.add_output_clicked)

        print(f'Inside CLASS WarehouseView - Factory Cell Size = {self.factory.cell_size}')
        print(f'Inside CLASS WarehouseView - Factory Length = {self.factory.length}')
        print(f'Inside CLASS WarehouseView - Factory Width = {self.factory.width}')
        print(f'Inside CLASS WarehouseView - PIXELS = {self.pixels}')
        print(f'Inside CLASS WarehouseView - Szene = {self.scene()}')

    def mousePressEvent(self, event):
        pos = event.position()  # relative to widget
        gp = self.mapToGlobal(pos)  # relative to screen
        rw = self.window().mapToGlobal(gp)  # relative to window
        column = int(pos.x() // self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width))
        row = int(pos.y() // self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width))
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        print(f'Mouse Coordinates: Col = {column}, Row = {row}')
        self.mouse_x_pos = pos.x()
        self.mouse_y_pos = pos.y()
        self.row = row
        self.column = column

    def contextMenuEvent(self, event):
        pos = event.pos()  # relative to widget
        gp = self.mapToGlobal(pos)  # relative to screen
        rw = self.window().mapToGlobal(gp)  # relative to window
        column = int(pos.x() // self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width))
        row = int(pos.y() // self.get_cell_size_for_grid(self.factory, self.warehouse.length, self.warehouse.width))
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        print(f'Mouse Coordinates: Col = {column}, Row = {row}')
        self.context_menu.exec(event.globalPos())
        self.mouse_x_pos = pos.x()
        self.mouse_y_pos = pos.y()
        self.row = row
        self.column = column

    @staticmethod
    def get_cell_size_for_grid(factory, warehouse_length, warehouse_width):
        # av1 is an auxiliary variable to visualize the length of the factory in the grid
        av1 = int(500 // int(warehouse_length) // (1/factory.cell_size))
        # print(self.av1)
        # av2 is an auxiliary variable to visualize the width of the factory in the grid
        av2 = int(500 // int(warehouse_width) // (1/factory.cell_size))
        # print(self.av2)
        if av1 < av2:
            return av1
        elif av2 < av1:
            return av2
        else:
            return av1

    def add_input_clicked(self):
        print(f'Inside CLASS WarehouseView - INPUT CLICKED')
        print(f'Inside CLASS WarehouseView - X = {self.mouse_x_pos}, Y = {self.mouse_y_pos} ,'
              f'Column = {self.column}, Row = {self.row}')
        print(f'Inside CLASS WarehouseView - Function add_input_clicked - BEFORE '
              f'self.machine.pos_input[0] = {self.warehouse.pos_input[0]}, '
              f'self.machine.pos_input[1] = {self.warehouse.pos_input[1]}')
        self.warehouse.local_pos_input = [self.column, self.row]
        self.scene().delete_input_output()
        self.scene().draw_input_output()
        print(f'Inside CLASS WarehouseView - Function add_input_clicked - AFTER '
              f'self.warehouse.pos_input[0] = {self.warehouse.pos_input[0]}, '
              f'self.warehouse.pos_input[1] = {self.warehouse.pos_input[1]}')

    def add_output_clicked(self):
        print(f'Inside CLASS WarehouseView - OUTPUT CLICKED')
        print(f'Inside CLASS WarehouseView - X = {self.mouse_x_pos}, Y = {self.mouse_y_pos} ,'
              f'Column = {self.column}, Row = {self.row}')
        print(f'Inside CLASS WarehouseView - Function add_output_clicked - BEFORE '
              f'self.machine.pos_output[0] = {self.warehouse.pos_output[0]}, '
              f'self.machine.pos_output[1] = {self.warehouse.pos_output[1]}')
        self.warehouse.local_pos_output = [self.column, self.row]
        self.scene().delete_input_output()
        self.scene().draw_input_output()
        print(f'Inside CLASS MachineView - Function add_output_clicked - AFTER '
              f'self.machine.pos_output[0] = {self.warehouse.pos_output[0]}, '
              f'self.machine.pos_output[1] = {self.warehouse.pos_output[1]}')

    def mouseMoveEvent(self, event):
        """pos = event.position()  # relative to widget
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        print(type(pos.x()))"""
        pass
