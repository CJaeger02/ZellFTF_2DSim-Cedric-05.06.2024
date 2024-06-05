# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.LoadingStation import LoadingStation
from FactoryObjects.Machine import Machine
from FactoryObjects.Path import Path
from FactoryObjects.Warehouse import Warehouse
from GUI.util.colors_and_symbols import *

from GUI.WidgetAddMachine import WidgetAddMachine
from GUI.WidgetAddWarehouse import WidgetAddWarehouse
from GUI.WidgetAddLoadingStation import WidgetAddLoadingStation
from GUI.WidgetDeleteMachine import WidgetDeleteMachine
from GUI.WidgetDeleteWarehouse import WidgetDeleteWarehouse
from GUI.WidgetDeleteLoadingStation import WidgetDeleteLoadingStation
from GUI.WidgetMoveMachine import WidgetMoveMachine
from GUI.WidgetMoveWarehouse import WidgetMoveWarehouse
from GUI.WidgetMoveLoadingStation import WidgetMoveLoadingStation
from GUI.WidgetPropertiesMachine import WidgetPropertiesMachine
from GUI.WidgetPropertiesWarehouse import WidgetPropertiesWarehouse
from GUI.WidgetPropertiesLoadingStation import WidgetPropertiesLoadingStation


########################################################################################################################

# The FactoryView-Class (inheritance QGraphicsView) visualizes the contents of the FactoryScene.

########################################################################################################################

class FactoryView(QGraphicsView):
    def __init__(self, factory: Factory, sidebar, parent=None) -> None:
        super(FactoryView, self).__init__(parent)
        self.factory: Factory = factory
        self.sidebar = sidebar
        self.mouse_x_pos = 0
        self.mouse_y_pos = 0
        self.column = 0
        self.row = 0
        self.pixels = self.get_cell_size_for_grid(self.factory)
        print(self.pixels)
        self.setFixedSize(1603, 953)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.context_menu = QMenu(self)
        self.add_path = self.context_menu.addAction('Add Path')
        self.add_machine = self.context_menu.addAction('Add Machine')
        self.add_warehouse = self.context_menu.addAction('Add Warehouse')
        self.add_loading_station = self.context_menu.addAction('Add Loading Station')
        self.context_menu.addSeparator()
        self.move_machine = self.context_menu.addAction('Move Machine')
        self.move_warehouse = self.context_menu.addAction('Move Warehouse')
        self.move_loading_station = self.context_menu.addAction('Move Loading Station')
        self.context_menu.addSeparator()
        self.delete_path = self.context_menu.addAction('Delete Path')
        self.delete_machine = self.context_menu.addAction('Delete Machine')
        self.delete_warehouse = self.context_menu.addAction('Delete Warehouse')
        self.delete_loading_station = self.context_menu.addAction('Delete Loading Station')
        self.context_menu.addSeparator()
        self.properties = self.context_menu.addAction('Properties')

        self.add_path.triggered.connect(self.add_path_clicked)
        self.add_machine.triggered.connect(self.add_machine_clicked)
        self.add_warehouse.triggered.connect(self.add_warehouse_clicked)
        self.add_loading_station.triggered.connect(self.add_loading_station_clicked)

        self.move_machine.triggered.connect(self.move_machine_clicked)
        self.move_warehouse.triggered.connect(self.move_warehouse_clicked)
        self.move_loading_station.triggered.connect(self.move_loading_station_clicked)

        self.delete_path.triggered.connect(self.delete_path_clicked)
        self.delete_machine.triggered.connect(self.delete_machine_clicked)
        self.delete_warehouse.triggered.connect(self.delete_warehouse_clicked)
        self.delete_loading_station.triggered.connect(self.delete_loading_station_clicked)

        self.properties.triggered.connect(self.properties_clicked)


    def mousePressEvent(self, event):
        pos = event.position()  # relative to widget
        gp = self.mapToGlobal(pos)  # relative to screen
        rw = self.window().mapToGlobal(gp)  # relative to window
        column = int(pos.x()) // self.get_cell_size_for_grid(self.factory)
        row = int(pos.y()) // self.get_cell_size_for_grid(self.factory)
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
        column = int(pos.x()) // self.get_cell_size_for_grid(self.factory)
        row = int(pos.y()) // self.get_cell_size_for_grid(self.factory)
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        print(f'Mouse Coordinates: Col = {column}, Row = {row}')
        print(type(self.factory.factory_grid_layout[column][row]))
        print(self.factory.factory_grid_layout[column][row])
        self.context_menu_empty(column, row)
        self.context_menu_path(column, row)
        self.context_menu_machine(column, row)
        self.context_menu_warehouse(column, row)
        self.context_menu_loading_station(column, row)
        self.context_menu.exec(event.globalPos())
        self.mouse_x_pos = pos.x()
        self.mouse_y_pos = pos.y()
        self.row = row
        self.column = column

    def context_menu_empty(self, column, row):
        if type(self.factory.factory_grid_layout[column][row]) == float:
            self.add_path.setEnabled(True)
            self.add_machine.setEnabled(True)
            self.add_warehouse.setEnabled(True)
            self.add_loading_station.setEnabled(True)
            self.move_machine.setEnabled(False)
            self.move_warehouse.setEnabled(False)
            self.move_loading_station.setEnabled(False)
            self.delete_path.setEnabled(False)
            self.delete_machine.setEnabled(False)
            self.delete_warehouse.setEnabled(False)
            self.delete_loading_station.setEnabled(False)
            self.properties.setEnabled(False)

    def context_menu_path(self, column, row):
        if type(self.factory.factory_grid_layout[column][row]) == Path:
            self.add_path.setEnabled(False)
            self.add_machine.setEnabled(False)
            self.add_warehouse.setEnabled(False)
            self.add_loading_station.setEnabled(False)
            self.move_machine.setEnabled(False)
            self.move_warehouse.setEnabled(False)
            self.move_loading_station.setEnabled(False)
            self.delete_path.setEnabled(True)
            self.delete_machine.setEnabled(False)
            self.delete_warehouse.setEnabled(False)
            self.delete_loading_station.setEnabled(False)
            self.properties.setEnabled(True)

    def context_menu_machine(self, column, row):
        if type(self.factory.factory_grid_layout[column][row]) == Machine:
            self.add_path.setEnabled(False)
            self.add_machine.setEnabled(False)
            self.add_warehouse.setEnabled(False)
            self.add_loading_station.setEnabled(False)
            self.move_machine.setEnabled(True)
            self.move_warehouse.setEnabled(False)
            self.move_loading_station.setEnabled(False)
            self.delete_path.setEnabled(False)
            self.delete_machine.setEnabled(True)
            self.delete_warehouse.setEnabled(False)
            self.delete_loading_station.setEnabled(False)
            self.properties.setEnabled(True)

    def context_menu_warehouse(self, column, row):
        if type(self.factory.factory_grid_layout[column][row]) == Warehouse:
            self.add_path.setEnabled(False)
            self.add_machine.setEnabled(False)
            self.add_warehouse.setEnabled(False)
            self.add_loading_station.setEnabled(False)
            self.move_machine.setEnabled(False)
            self.move_warehouse.setEnabled(True)
            self.move_loading_station.setEnabled(False)
            self.delete_path.setEnabled(False)
            self.delete_machine.setEnabled(False)
            self.delete_warehouse.setEnabled(True)
            self.delete_loading_station.setEnabled(False)
            self.properties.setEnabled(True)

    def context_menu_loading_station(self, column, row):
        if type(self.factory.factory_grid_layout[column][row]) == LoadingStation:
            self.add_path.setEnabled(False)
            self.add_machine.setEnabled(False)
            self.add_warehouse.setEnabled(False)
            self.add_loading_station.setEnabled(False)
            self.move_machine.setEnabled(False)
            self.move_warehouse.setEnabled(False)
            self.move_loading_station.setEnabled(True)
            self.delete_path.setEnabled(False)
            self.delete_machine.setEnabled(False)
            self.delete_warehouse.setEnabled(False)
            self.delete_loading_station.setEnabled(True)
            self.properties.setEnabled(True)

    @staticmethod
    def get_cell_size_for_grid(factory):
        # av1 is an auxiliary variable to visualize the length of the factory in the grid
        av1 = int(1600 // int(factory.length) // (1/factory.cell_size))
        # av2 is an auxiliary variable to visualize the width of the factory in the grid
        av2 = int(950 // int(factory.width) // (1/factory.cell_size))
        if av1 < av2:
            return av1
        elif av2 < av1:
            return av2
        else:
            return av1

    def add_path_clicked(self):
        if self.factory.factory_grid_layout[self.column][self.row] == 0.0:
            self.factory.factory_grid_layout[self.column][self.row] = Path()
            self.scene().delete_factory_grid()
            self.scene().draw_factory_grid()
            self.print_factory_grid_layout()
        else:
            print('BLOCKED!')

    def add_machine_clicked(self):
        self.widget_add_machine = WidgetAddMachine(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_add_machine.show()
        pass

    def add_warehouse_clicked(self):
        self.widget_add_warehouse = WidgetAddWarehouse(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_add_warehouse.show()

    def add_loading_station_clicked(self):
        self.widget_add_loading_station = WidgetAddLoadingStation(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_add_loading_station.show()

    def move_machine_clicked(self):
        self.widget_move_machine = WidgetMoveMachine(
            self.factory, self.scene(), self.column, self.row)
        self.widget_move_machine.show()
        pass

    def move_warehouse_clicked(self):
        self.widget_move_warehouse = WidgetMoveWarehouse(
            self.factory, self.scene(), self.column, self.row)
        self.widget_move_warehouse.show()

    def move_loading_station_clicked(self):
        self.widget_move_loading_station = WidgetMoveLoadingStation(
            self.factory, self.scene(), self.column, self.row)
        self.widget_move_loading_station.show()
        pass

    def delete_path_clicked(self):
        self.factory.factory_grid_layout[self.column][self.row] = 0.0
        self.scene().delete_factory_grid()
        self.scene().draw_factory_grid()
        self.print_factory_grid_layout()
        pass

    def delete_machine_clicked(self):
        self.widget_delete_machine = WidgetDeleteMachine(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_delete_machine.show()

    def delete_warehouse_clicked(self):
        self.widget_delete_warehouse = WidgetDeleteWarehouse(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_delete_warehouse.show()

    def delete_loading_station_clicked(self):
        self.widget_delete_loading_station = WidgetDeleteLoadingStation(
            self.factory, self.scene(), self.sidebar, self.column, self.row)
        self.widget_delete_loading_station.show()

    def properties_clicked(self):
        if type(self.factory.factory_grid_layout[self.column][self.row]) == Machine:
            self.widget_machine_properties = WidgetPropertiesMachine(
                self.factory, self.scene(), self.sidebar, self.column, self.row)
            self.widget_machine_properties.show()
        if type(self.factory.factory_grid_layout[self.column][self.row]) == Warehouse:
            self.widget_warehouse_properties = WidgetPropertiesWarehouse(
                self.factory, self.scene(), self.sidebar, self.column, self.row)
            self.widget_warehouse_properties.show()
        if type(self.factory.factory_grid_layout[self.column][self.row]) == LoadingStation:
            self.widget_loading_station_properties = WidgetPropertiesLoadingStation(
                self.factory, self.scene(), self.sidebar, self.column, self.row)
            self.widget_loading_station_properties.show()

    def print_factory_grid_layout(self):
        for y in range(self.factory.no_rows):
            for x in range(self.factory.no_columns):
                print(
                    f'Inside CLASS WidgetAddMachine - factory_grid_layout[{x}][{y}] = '
                    f'{self.factory.factory_grid_layout[x][y]}')
                print(
                    f'Inside CLASS WidgetAddMachine - TYPE factory_grid_layout[{x}][{y}] = '
                    f'{type(self.factory.factory_grid_layout[x][y])}')

    def mouseMoveEvent(self, event):
        # pos = event.position()  # relative to widget
        # print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        # print(type(pos.x()))
        pass
