import os

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import numpy as np

# own packages
from FactoryObjects.Factory import Factory
from GUI.WidgetMainWindow_WidgetFabricLayout import WidgetFabricLayout
from GUI.FactoryScene import FactoryScene
from GUI.FactoryView import FactoryView
from VRP_Modelle.VRP import VRP_cellAGV
from FactoryObjects.AGV import AGV

from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects

import pandas as pd


########################################################################################################################

# The WidgetMainWindow-Class (inheritance QWidget) is the QWidget for the main window
# It contains all the widgets of the Main Windows graphical interface.
# These are...
#       ...

########################################################################################################################


class WidgetMainWindow(QWidget):
    # Initiieren
    def __init__(self, app, mother):
        super(WidgetMainWindow, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setMouseTracking(True)


        # Create layout
        self.gridLayout1 = QGridLayout()

        # Init of Factory
        self.factory = Factory()

        # Init the VRP
        self.VRP_cellAGV = VRP_cellAGV(self.factory)

        # Init of folders
        self.create_folders()

        # TODO: nur für Testzwecke eingebaut
        print('TEST-FABRIK ANFANG')
        self.factory.name = 'simple_loop_test_factory'
        self.factory.width = 10
        self.factory.length = 10
        self.factory.cell_size = 1.0
        self.factory.no_columns = int(self.factory.length / self.factory.cell_size)
        self.factory.no_rows = int(self.factory.width / self.factory.cell_size)
        self.factory.np_factory_grid_layout = np.zeros(shape=(self.factory.no_columns, self.factory.no_rows))
        self.factory_grid_layout = self.factory.np_factory_grid_layout.tolist()
        if not os.path.exists(f'data/Saved_Factories/{self.factory.name}'):
            os.mkdir(f'data/Saved_Factories/{self.factory.name}')
        print('TEST-FABRIK ENDE')

        self.factoryScene = FactoryScene(self.factory)

        self.widgetFabricLayout = WidgetFabricLayout(self.factory, self.factoryScene, self.VRP_cellAGV)

        self.factoryView = FactoryView(self.factory, self.widgetFabricLayout.sidebar, self.factoryScene)

        # Add Widgets to gridLayout1
        self.gridLayout1.addWidget(self.widgetFabricLayout, 0, 0)
        self.gridLayout1.addWidget(self.factoryView, 0, 1)

        # Set Layout
        self.setLayout(self.gridLayout1)

    def create_folders(self):
        # if not os.path.isfile(f'data/Current_Factory/Product_Data.csv'):
        print('Creating Path Product Types...')
        current_product_types_database = open(f'data/Current_Factory/Product_Data.csv', 'w')
        current_product_types_database.write(';Name;Length;Width;Weight\n'
                                             '0;default_product_1;500;500;25.0\n'
                                             '1;default_product_2;1000;1000;100.0\n'
                                             '2;default_product_3;1500;1000;150.0\n'
                                             '3;default_product_4;500;1000;50.0')
        current_product_types_database.close()

        # if not os.path.isfile(f'data/Current_Factory/Machine_Data.csv'):
        print('Creating Path Machines...')
        current_machine_database = open(f'data/Current_Factory/Machine_Data.csv', 'w')
        current_machine_database.write(';ID;Name;Length;Width;X-Position;Y-Position;Input-Position;Output-Position;'
                                       'Input Products; Output Products; Processing Times; Input Buffer Sizes;'
                                       'Output Buffer Sizes;Input Loading Times; Output Loading Times')
        # self.machine_data.write('\n0;0;default_machine;1;1;0;0;[0,0];[0,0];[\'default_product\'];'
        #                              '[\'default_product\'];30;1;1;0;0;[\'W0\'];[\'W0\']')
        current_machine_database.close()

        # if not os.path.isfile(f'data/Current_Factory/Warehouse_Data.csv'):
        print('Creating Path Warehouses...')
        current_warehouse_database = open(f'data/Current_Factory/Warehouse_Data.csv', 'w')
        current_warehouse_database.write(';ID;Name;Length;Width;X-Position;Y-Position;Input-Position;'
                                         'Output-Position;Input Products; Output Products; Processing Times;'
                                         'Input Buffer Sizes;'
                                         'Output Buffer Sizes;Input Loading Times; Output Loading Times')
        # self.machine_data.write('\n0;0;default_machine;1;1;0;0;[0,0];[0,0];[\'default_product\'];'
        #                              '[\'default_product\'];30;1;1;0;0;[\'W0\'];[\'W0\']')
        current_warehouse_database.close()

        # if not os.path.isfile(f'data/Current_Factory/Loading_Station_Data.csv'):
        print('Creating Path Loading Station...')
        current_loading_station_database = open(f'data/Current_Factory/Loading_Station_Data.csv', 'w')
        current_loading_station_database.write(';ID;Name;Length;Width;X-Position;Y-Position;Charging Time;Capacity')
        # self.machine_data.write('\n0;0;default_machine;1;1;0;0;[0,0];[0,0];[\'default_product\'];'
        #                              '[\'default_product\'];30;1;1;0;0;[\'W0\'];[\'W0\']')
        current_loading_station_database.close()

        print('Creating Path Factory...')
        current_factory_database = open(f'data/Current_Factory/Factory_Data.csv', 'w')
        current_factory_database.write(f';Name;Length;Width;Cell_Size\n'
                                       f'0;{self.factory.name};{self.factory.length};'
                                       f'{self.factory.width};{self.factory.cell_size}')
        current_factory_database.close()

