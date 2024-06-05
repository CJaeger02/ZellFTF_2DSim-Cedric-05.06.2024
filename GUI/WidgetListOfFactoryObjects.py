# general packages
import os
import numpy as np

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.LoadingStation import LoadingStation
from FactoryObjects.Machine import Machine
from FactoryObjects.Warehouse import Warehouse
from GUI.FactoryScene import FactoryScene
from GUI.util import colors_and_symbols
from GUI.WidgetDeleteMachine import WidgetDeleteMachine
from GUI.WidgetDeleteWarehouse import WidgetDeleteWarehouse
from GUI.WidgetDeleteLoadingStation import WidgetDeleteLoadingStation


########################################################################################################################

# The WidgetFabricLayout-Class (inheritance QWidget) is a Sub_QWidget for the WidgetMainWindow.
# It contains all the input variables for the factory layout defined by the user.
# These are...
#       ...length of factory in meter
#       ...width of factory in meter
#       ...cell size of a factory module in meter
# Besides factorise can be created, loaded and saved.
# Information about the objects inside the factory are visualized in a small window

########################################################################################################################

class SectionExpandButton(QPushButton):
    """
    A QPushbutton that can expand or collapse its section
    """

    def __init__(self, item, text="", parent=None) -> None:
        super().__init__(text, parent)
        self.section = item
        self.clicked.connect(self.on_clicked)

    def on_clicked(self) -> None:
        """
        Toggle expand/collapse of section by clicking
        :return: None
        """
        if self.section.isExpanded():
            self.section.setExpanded(False)
        else:
            self.section.setExpanded(True)


class WidgetListOfFactoryObjects(QDialog):
    """
    A dialog to which collapsible sections can be added;
    subclass and reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
    """
    def __init__(self, factory: Factory, factoryScene: FactoryScene, *args, **kwargs):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)

        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene

        self.machines_table = QListWidget(parent=self)
        self.warehouses_table = QListWidget(parent=self)
        self.loading_stations_table = QListWidget(parent=self)
        self.legend_table = QListWidget(parent=self)

        item_machine = QListWidgetItem(self.tr('Machine'), self.legend_table)
        item_machine.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_MACHINE)
        item_machine.setIcon(QIcon(pixmap))

        item_warehouse = QListWidgetItem(self.tr('Warehouse'), self.legend_table)
        item_warehouse.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_WAREHOUSE)
        item_warehouse.setIcon(QIcon(pixmap))

        item_loading_station = QListWidgetItem(self.tr('Loading Station'), self.legend_table)
        item_loading_station.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_LOADING_STATION)
        item_loading_station.setIcon(QIcon(pixmap))

        item_input = QListWidgetItem(self.tr('Input'), self.legend_table)
        item_input.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_INPUT)
        item_input.setIcon(QIcon(pixmap))

        item_output = QListWidgetItem(self.tr('Output'), self.legend_table)
        item_output.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_OUTPUT)
        item_output.setIcon(QIcon(pixmap))

        item_input_output = QListWidgetItem(self.tr('Input_Output'), self.legend_table)
        item_input_output.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_INPUT_OUTPUT)
        item_input_output.setIcon(QIcon(pixmap))

        item_path = QListWidgetItem(self.tr('Path'), self.legend_table)
        item_path.setForeground(colors_and_symbols.BLACK)
        pixmap = QPixmap(100, 100)
        pixmap.fill(colors_and_symbols.COLOR_WAY)
        item_path.setIcon(QIcon(pixmap))

        '''self.context_menu = QMenu(self)
        self.delete_machine = self.context_menu.addAction('Delete Machine')
        self.delete_warehouse = self.context_menu.addAction('Delete Warehouse')
        self.delete_loading_station = self.context_menu.addAction('Delete Loading Station')
        self.context_menu.addSeparator()
        self.properties = self.context_menu.addAction('Properties')
        self.delete_machine.setEnabled(False)
        self.delete_warehouse.setEnabled(False)
        self.delete_loading_station.setEnabled(False)
        self.properties.setEnabled(False)

        self.delete_machine.triggered.connect(self.delete_machine_clicked)
        self.delete_warehouse.triggered.connect(self.delete_warehouse_clicked)
        self.delete_loading_station.triggered.connect(self.delete_loading_station_clicked)

        self.properties.triggered.connect(self.properties_clicked)'''

        self.sections = []
        self.items_machine = []
        self.items_warehouses = []
        self.items_loading_stations = []
        self.define_sections()
        self.add_sections()

    def add_sections(self) -> None:
        """
        Adds a collapsible sections for every
        (title, widget) tuple in self.sections
        :return: None
        """
        for (title, widget) in self.sections:
            button1 = self.add_button(title)
            section1 = self.add_widget(button1, widget)
            button1.addChild(section1)
            if title == self.tr('Legend'):
                button1.setToolTip(0, self.tr('The legends shows the meanings of colors for each factory object'))
            elif title == self.tr('Machines'):
                button1.setToolTip(0, self.tr('All the machines inside the factory'))
            elif title == self.tr('Warehouses'):
                button1.setToolTip(0, self.tr('All the warehouses inside the factory'))
            elif title == self.tr('Loading Stations'):
                button1.setToolTip(0, self.tr('All the loading stations inside the factory'))

    def define_sections(self) -> None:
        """
        This adds sections to our collapsible Dialog
        :return: None
        """
        self.sections.append((self.tr("Legend"), self.legend_table))
        self.sections.append((self.tr("Machines"), self.machines_table))
        self.sections.append((self.tr("Warehouses"), self.warehouses_table))
        self.sections.append((self.tr("Loading Stations"), self.loading_stations_table))
        print(self.sections)

    def add_button(self, title) -> QTreeWidgetItem:
        """
                creates a QTreeWidgetItem containing a button
                to expand or collapse its section
                :param title: Title of our created section
                :return: None
                """
        item = QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        self.tree.setItemWidget(item, 0, SectionExpandButton(item, text=title))
        return item

    def add_widget(self, button, widget) -> QTreeWidgetItem:
        """
        creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        :param button: The button for expanding our Widget
        :param widget: Widget to display after expansion
        :return: None
        """
        section = QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section

    def clear_facilities_table(self) -> None:
        """
        Deletes all elements from the fac_table.
        :return: None
        """
        self.machines_table.clear()
        self.warehouses_table.clear()
        self.loading_stations_table.clear()

    def set_machines_table(self):
        """
        Fills the facility table with all of our machines in our factory and places a square with
        the corresponding color next to them.
        Already placed facilities are marked in a different text color.
        :param scene_facilities: List of our facilities which are already placed in our scene
        :return: None
        """
        self.machines_table.clear()
        for machine in self.factory.machines:
            print(machine.name)
            item = QListWidgetItem(machine.name, self.machines_table)
            item.setForeground(colors_and_symbols.BLACK)
            pixmap = QPixmap(100, 100)
            pixmap.fill(colors_and_symbols.COLOR_MACHINE)
            item.setIcon(QIcon(pixmap))

    def set_warehouses_table(self):
        """
        Fills the facility table with all of our warehouses in our factory and places a square with
        the corresponding color next to them.
        Already placed facilities are marked in a different text color.
        :param scene_facilities: List of our facilities which are already placed in our scene
        :return: None
        """
        self.warehouses_table.clear()
        for warehouse in self.factory.warehouses:
            print(warehouse.name)
            item = QListWidgetItem(warehouse.name, self.warehouses_table)
            item.setForeground(colors_and_symbols.BLACK)
            pixmap = QPixmap(100, 100)
            pixmap.fill(colors_and_symbols.COLOR_WAREHOUSE)
            item.setIcon(QIcon(pixmap))

    def set_loading_stations_table(self):
        """
        Fills the facility table with all of our loading stations in our factory and places a square with
        the corresponding color next to them.
        Already placed facilities are marked in a different text color.
        :param scene_facilities: List of our facilities which are already placed in our scene
        :return: None
        """
        self.loading_stations_table.clear()
        self.items_loading_stations = []
        for loading_station in self.factory.loading_stations:
            # print(f'loading_station = {loading_station}')
            item = QListWidgetItem(loading_station.name, self.loading_stations_table)
            item.setForeground(colors_and_symbols.BLACK)
            pixmap = QPixmap(100, 100)
            pixmap.fill(colors_and_symbols.COLOR_LOADING_STATION)
            item.setIcon(QIcon(pixmap))
            self.items_loading_stations.append(item)

    def mousePressEvent(self, event):
        pos = event.position() # relative to widget
        gp = self.mapToGlobal(pos) # relative to screen
        rw = self.window().mapToGlobal(gp) # relative to window
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        self.mouse_x_pos = pos.x()
        self.mouse_y_pos = pos.y()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()

    '''def contextMenuEvent(self,event):
        pos = event.pos()  # relative to widget
        gp = self.mapToGlobal(pos)  # relative to screen
        rw = self.window().mapToGlobal(gp)  # relative to window
        print(f"Mouse Coordinates: X = {pos.x()}, Y = {pos.y()}")
        self.context_menu_else()
        self.context_menu_machine()
        self.context_menu_warehouse()
        self.context_menu_loading_station()
        self.context_menu.exec(event.globalPos())
        self.mouse_x_pos = pos.x()
        self.mouse_y_pos = pos.y()

    def context_menu_else(self):
        self.delete_machine.setEnabled(False)
        self.delete_warehouse.setEnabled(False)
        self.delete_loading_station.setEnabled(False)
        self.properties.setEnabled(False)

    def context_menu_machine(self):
        # print(self.factory.get_type_by_name(self.machines_table.currentItem().text()))
        if self.machines_table.currentItem() is not None:
            if self.factory.get_type_by_name(self.machines_table.currentItem().text()) == Machine:
                self.delete_machine.setEnabled(True)
                self.delete_warehouse.setEnabled(False)
                self.delete_loading_station.setEnabled(False)
                self.properties.setEnabled(True)

    def context_menu_warehouse(self):
        if self.warehouses_table.currentItem() is not None:
            if self.factory.get_type_by_name(self.warehouses_table.currentItem().text()) == Warehouse:
                self.delete_machine.setEnabled(False)
                self.delete_warehouse.setEnabled(True)
                self.delete_loading_station.setEnabled(False)
                self.properties.setEnabled(True)

    def context_menu_loading_station(self):
        if self.loading_stations_table.currentItem() is not None:
            print(self.loading_stations_table.currentItem().text())
            if self.factory.get_type_by_name(self.loading_stations_table.currentItem().text()) == LoadingStation:
                self.delete_machine.setEnabled(False)
                self.delete_warehouse.setEnabled(False)
                self.delete_loading_station.setEnabled(True)
                self.properties.setEnabled(True)

    def item_clicked(self, item):
        return item.text()

    def delete_machine_clicked(self):
        self.widget_delete_machine = WidgetDeleteMachine(self.factory, self.factoryScene, self.machines_table)
        self.widget_delete_machine.show()

    def delete_warehouse_clicked(self):
        self.widget_delete_warehouse = WidgetDeleteWarehouse(self.factory, self.factoryScene, self.warehouses_table)
        self.widget_delete_warehouse.show()

    def delete_loading_station_clicked(self):
        self.widget_delete_loading_station = WidgetDeleteLoadingStation(self.factory, self.factoryScene, self.loading_stations_table)
        self.widget_delete_loading_station.show()

    def properties_clicked(self):
        pass'''

