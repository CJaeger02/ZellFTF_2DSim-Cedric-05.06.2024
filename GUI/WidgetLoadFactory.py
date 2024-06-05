import pandas as pd
import os
import shutil
import numpy as np
import json

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# own packages
from FactoryObjects.Factory import Factory
from FactoryObjects.Warehouse import Warehouse
from FactoryObjects.Machine import Machine
from FactoryObjects.LoadingStation import LoadingStation
from GUI.FactoryScene import FactoryScene
from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects


########################################################################################################################

# The WidgetLoadFactory-Class (inheritance QWidget) is a Sub_QWidget for the WidgetMainWindow.

########################################################################################################################

class WidgetLoadFactory(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar: WidgetListOfFactoryObjects, *args, **kwargs):

        # Init of the GUI
        super(WidgetLoadFactory, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar: WidgetListOfFactoryObjects = sidebar
        self.setFont(QFont('Arial', 10))

        self.resize(300, 100)
        self.setMaximumSize(600, 600)
        self.setWindowTitle('ZellFTF - Loading a factory')
        self.center()

        if not os.path.exists(f'data/Saved_Factories'):
            os.makedirs(f'data/Saved_Factories')

        self.path_factory_folders = 'data/Saved_Factories'

        """self.path_machine_database = f'data/Current_Factory/Machine_Data.csv'
        self.machines_pd = pd.read_csv(self.path_machine_database, sep=';', index_col=0)
        self.amount_of_machines = len(self.machines_pd.index)"""

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        # Create Widgets
        self.label_which_factory = QLabel("Which factory should be loaded?")
        self.combo_box_saved_factories = QComboBox()
        factory_folders = os.listdir(self.path_factory_folders)
        for folder in factory_folders:
            self.combo_box_saved_factories.addItem(folder)
        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)
        self.button_load_factory = QPushButton("Load Factory")
        self.button_cancel = QPushButton("Cancel")

        if self.combo_box_saved_factories.count() == 0:
            self.button_load_factory.setEnabled(False)
        else:
            self.button_load_factory.setEnabled(True)


        # QPushbuttons - functions
        self.button_load_factory.clicked.connect(self.button_load_factory_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        # Add to Layout
        self.hLayout1.addWidget(self.button_load_factory)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addWidget(self.label_which_factory)
        self.vLayout1.addWidget(self.combo_box_saved_factories)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)

        # Set Layout
        self.setLayout(self.vLayout1)

    def button_load_factory_clicked(self):
        chosen_factory = self.combo_box_saved_factories.currentText()
        # Copy the csv-files from the saved factory to the current factory path
        shutil.copyfile('data/Saved_Factories/{}/Factory_Data.csv'.format(chosen_factory),
                        'data/Current_Factory/Factory_Data.csv')
        shutil.copyfile('data/Saved_Factories/{}/Product_Data.csv'.format(chosen_factory),
                        'data/Current_Factory/Product_Data.csv')
        shutil.copyfile('data/Saved_Factories/{}/Warehouse_Data.csv'.format(chosen_factory),
                        'data/Current_Factory/Warehouse_Data.csv')
        shutil.copyfile('data/Saved_Factories/{}/Machine_Data.csv'.format(chosen_factory),
                        'data/Current_Factory/Machine_Data.csv')
        shutil.copyfile('data/Saved_Factories/{}/Loading_Station_Data.csv'.format(chosen_factory),
                        'data/Current_Factory/Loading_Station_Data.csv')
        # TODO: aus CSV-Dateien in die class factory einlesen

        # Dateipfade zu CSV-Dateien setzen
        path_factory_database = f'data/Current_Factory/Factory_Data.csv'
        factory_pd = pd.read_csv(path_factory_database, sep=';', index_col=0)
        path_product_types_database = f'data/Current_Factory/Product_Data.csv'
        product_types_pd = pd.read_csv(path_product_types_database, sep=';', index_col=0)
        amount_of_product_types = len(product_types_pd)
        path_warehouse_database = f'data/Current_Factory/Warehouse_Data.csv'
        warehouses_pd = pd.read_csv(path_warehouse_database, sep=';', index_col=0)
        amount_of_warehouses = len(warehouses_pd.index)
        path_machine_database = f'data/Current_Factory/Machine_Data.csv'
        machines_pd = pd.read_csv(path_machine_database, sep=';', index_col=0)
        amount_of_machines = len(machines_pd.index)
        path_loading_stations_database = f'data/Current_Factory/Loading_Station_Data.csv'
        loading_stations_pd = pd.read_csv(path_loading_stations_database, sep=';', index_col=0)
        amount_of_loading_stations = len(loading_stations_pd.index)

        # In Listen umwandeln
        factory_list = factory_pd.values.tolist()
        product_types_list = product_types_pd.values.tolist()
        warehouses_list = warehouses_pd.values.tolist()
        machines_list = machines_pd.values.tolist()
        loading_stations_list = loading_stations_pd.values.tolist()

        print(f"Loading FACTORY:")
        print(f"Factory: {factory_list}")
        print(f"Product_Types: {product_types_list}")
        print(f"Warehouses: {warehouses_list}")
        print(f"Machines: {machines_list}")
        print(f"Loading_Stations: {loading_stations_list}")

        for i in range(len(product_types_list)):
            self.factory.product_types[product_types_list[i][0]] = dict(length=product_types_list[i][1], width=product_types_list[i][2], weight=product_types_list[i][3])

        i = 0
        for warehouses in warehouses_list:
            warehouse = Warehouse()
            warehouse.id = i
            warehouse.name = warehouses[1]
            warehouse.length = int(warehouses[2])
            warehouse.width = int(warehouses[3])
            warehouse.pos_x = int(warehouses[4])
            warehouse.pos_y = int(warehouses[5])
            pos_input_str = warehouses[6] # data comes as str from csv and needs to be converted to list
            warehouse.pos_input = json.loads(pos_input_str)
            pos_output_str = warehouses[7] # data comes as str from csv and needs to be converted to list
            warehouse.pos_output = json.loads(pos_output_str)
            np_pos_warehouse = np.array([(warehouse.pos_x), (warehouse.pos_y)])
            np_warehouse_pos_input = np.array(warehouse.pos_input)
            np_warehouse_pos_output = np.array(warehouse.pos_output)
            warehouse.local_pos_input = (- np_pos_warehouse + np_warehouse_pos_input).tolist()
            warehouse.local_pos_output = (- np_pos_warehouse + np_warehouse_pos_output).tolist()
            warehouse.input_products = self.string_to_list(warehouses[8]) # data comes as str from csv and needs to be converted to list
            warehouse.output_products = self.string_to_list(warehouses[9])
            warehouse.process_time = int(warehouses[10])
            warehouse.rest_process_time = int(warehouses[10])
            warehouse.buffer_input = self.string_to_list(warehouses[11])
            warehouse.buffer_output = self.string_to_list(warehouses[12])
            warehouse.loading_time_input = self.string_to_list(warehouses[13])
            warehouse.loading_time_output = self.string_to_list(warehouses[14])
            self.factory.add_warehouse(warehouse)
            self.factory.add_to_grid(warehouse)
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_warehouses_table()
            i += 1

        i = 0
        for machines in machines_list:
            machine = Machine()
            machine.id = i
            machine.name = machines[1]
            machine.length = int(machines[2])
            machine.width = int(machines[3])
            machine.pos_x = int(machines[4])
            machine.pos_y = int(machines[5])
            pos_input_str = machines[6]
            machine.pos_input = json.loads(pos_input_str)
            pos_output_str = machines[7]
            machine.pos_output = json.loads(pos_output_str)
            np_pos_machine = np.array([int(machine.pos_x), int(machine.pos_y)])
            np_machine_pos_input = np.array(machine.pos_input)
            np_machine_pos_output = np.array(machine.pos_output)
            machine.local_pos_input = (np_pos_machine + np_machine_pos_input).tolist()
            machine.local_pos_output = (np_pos_machine + np_machine_pos_output).tolist()
            machine.input_products = self.string_to_list(machines[8])
            machine.output_products = self.string_to_list(machines[9])
            machine.process_time = int(machines[10])
            machine.rest_process_time = int(machines[10])
            machine.buffer_input = self.string_to_list(machines[11])
            machine.buffer_output = self.string_to_list(machines[12])
            machine.loading_time_input = self.string_to_list(machines[13])
            machine.loading_time_output = self.string_to_list(machines[14])
            print(machine.name)
            self.factory.add_machine(machine)
            self.factory.add_to_grid(machine)
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_machines_table()
            i += 1

        i = 0
        for loading_stations in loading_stations_list:
            loading_station = LoadingStation()
            loading_station.id = i
            loading_station.name = loading_stations[1]
            loading_station.length = int(loading_stations[2])
            loading_station.width = int(loading_stations[3])
            loading_station.pos_x = int(loading_stations[4])
            loading_station.pos_y = int(loading_stations[5])
            loading_station.charging_time = float(loading_stations[6])
            loading_station.capacity = int(loading_stations[7])
            self.factory.add_loading_station(loading_station)
            self.factory.add_to_grid(loading_station)
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_loading_stations_table()
            i += 1

        print(self.factory.product_types)
        print(self.factory.warehouses)
        print(self.factory.machines)
        print(self.factory.loading_stations)

        self.close()

    def cancel_clicked(self):
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def string_to_list(self, str):
        str_replace = str.replace(",", " ")
        str_replace = str_replace.replace("[", "")
        str_replace = str_replace.replace("]", "")
        str_replace = str_replace.replace("\'", "")
        print(f'str_replace = {str_replace} - TYPE = {type(str_replace)}')
        try:
            liste = list(map(int, str_replace.split(" ")))
        except ValueError:
            liste = list(str_replace.split(" "))
        print(f'liste = {liste} - TYPE = {type(liste)}')
        return liste

