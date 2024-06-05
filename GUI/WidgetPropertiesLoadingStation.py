# general packages
import shutil
import os

import numpy as np
import pandas as pd
from datetime import datetime

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

import config
# own packages
from FactoryObjects.Factory import Factory
from GUI.FactoryScene import FactoryScene
from FactoryObjects.Machine import Machine
from GUI.MachineScene import MachineScene
from GUI.MachineView import MachineView
from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects

########################################################################################################################

# The WidgetProperties-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to change properties of a factory object (Warehouse, Machine, Loading Station) .
# In this window all necessary data about the factory object can be changed.

########################################################################################################################


class WidgetPropertiesLoadingStation(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar: WidgetListOfFactoryObjects,
                 *args, **kwargs):
        super(WidgetPropertiesLoadingStation, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar: WidgetListOfFactoryObjects = sidebar
        if len(args) > 0:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            self.loading_station = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked]
            print(f'Inside CLASS - WidgetPropertiesLoadingStation - LoadingStation - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked]}')
            print(f'Inside CLASS - WidgetPropertiesLoadingStation - LoadingStation - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name}')
            print(f'Inside CLASS - WidgetPropertiesLoadingStation - LoadingStation X-Position - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_x}')
            print(f'Inside CLASS - WidgetPropertiesLoadingStation - LoadingStation Y-Position - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_y}')

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(500, 250)
        self.setMaximumSize(600, 600)
        self.setWindowTitle(f'ZellFTF - Change properties of "{self.loading_station.name}"')
        self.center()

        self.path_loading_station_database = f'data/Current_Factory/Loading_Station_Data.csv'
        self.loading_stations_pd = pd.read_csv(self.path_loading_station_database, sep=';', index_col=0)
        self.amount_of_loading_stations = len(self.loading_stations_pd.index)

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.gridLayout1 = QGridLayout()
        self.hLayout1 = QHBoxLayout()

        # Widgets
        self.label_loading_station_id = QLabel('Loading station ID:')
        self.lineEdit_loading_station_id = QLineEdit(self)
        self.lineEdit_loading_station_id.setAlignment(Qt.AlignCenter)
        self.lineEdit_loading_station_id.setEnabled(False)
        self.label_loading_station_name = QLabel('Name of the loading station:')
        self.lineEdit_loading_station_name = QLineEdit(self)
        self.lineEdit_loading_station_name.setAlignment(Qt.AlignCenter)
        self.label_length = QLabel('Length of loading station (m):')
        self.lineEdit_length = QLineEdit(self)
        self.lineEdit_length.setAlignment(Qt.AlignCenter)
        self.lineEdit_length.setValidator(QIntValidator())
        self.lineEdit_length.setEnabled(False)
        self.label_width = QLabel('Width of loading station (m):')
        self.lineEdit_width = QLineEdit(self)
        self.lineEdit_width.setAlignment(Qt.AlignCenter)
        self.lineEdit_width.setValidator(QIntValidator())
        self.lineEdit_width.setEnabled(False)
        self.label_pos_x = QLabel('X-position of loading station in factory grid:')
        self.lineEdit_pos_x = QLineEdit(self)
        self.lineEdit_pos_x.setAlignment(Qt.AlignCenter)
        self.label_pos_y = QLabel('Y-position of loading station in factory grid:')
        self.lineEdit_pos_y = QLineEdit(self)
        self.lineEdit_pos_y.setAlignment(Qt.AlignCenter)
        self.label_charging_time = QLabel('Charging time time (%/min):')
        self.lineEdit_charging_time = QLineEdit(self)
        self.lineEdit_charging_time.setAlignment(Qt.AlignCenter)
        self.lineEdit_charging_time.setValidator(QDoubleValidator())
        self.label_capacity = QLabel('Capacity of AGVs (pcs):')
        self.lineEdit_capacity = QLineEdit(self)
        self.lineEdit_capacity.setAlignment(Qt.AlignCenter)
        self.lineEdit_capacity.setValidator(QIntValidator())

        self.lineEdit_loading_station_name.setText(str(self.loading_station.name))
        self.lineEdit_length.setText(str(self.loading_station.length))
        self.lineEdit_width.setText(str(self.loading_station.width))
        self.lineEdit_pos_x.setText(str(self.loading_station.pos_x))
        self.lineEdit_pos_y.setText(str(self.loading_station.pos_y))
        self.lineEdit_charging_time.setText(str(self.loading_station.charging_time))
        self.lineEdit_capacity.setText(str(self.loading_station.capacity))

        self.id = self.lineEdit_loading_station_id.text()
        self.name = self.lineEdit_loading_station_name.text()
        self.length = int(self.lineEdit_length.text())
        self.width = int(self.lineEdit_width.text())
        self.pos_x = int(self.lineEdit_pos_x.text())
        self.pos_y = int(self.lineEdit_pos_y.text())
        self.charging_time = float(self.lineEdit_charging_time.text())
        self.capacity = int(self.lineEdit_capacity.text())

        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)

        self.button_cancel = QPushButton('Cancel')
        self.button_change_loading_station = QPushButton('Change Properties')
        self.label_user_info = QLabel('Waiting for action...')
        self.label_user_info.setAlignment(Qt.AlignCenter)

        # Add Widgets to gridLayout1
        self.gridLayout1.addWidget(self.label_loading_station_id, 0, 0)
        self.gridLayout1.addWidget(self.lineEdit_loading_station_id, 0, 1)
        self.gridLayout1.addWidget(self.label_loading_station_name, 1, 0)
        self.gridLayout1.addWidget(self.lineEdit_loading_station_name, 1, 1)
        self.gridLayout1.addWidget(self.label_length, 2, 0)
        self.gridLayout1.addWidget(self.lineEdit_length, 2, 1)
        self.gridLayout1.addWidget(self.label_width, 3, 0)
        self.gridLayout1.addWidget(self.lineEdit_width, 3, 1)
        self.gridLayout1.addWidget(self.label_pos_x, 4, 0)
        self.gridLayout1.addWidget(self.lineEdit_pos_x, 4, 1)
        self.gridLayout1.addWidget(self.label_pos_y, 5, 0)
        self.gridLayout1.addWidget(self.lineEdit_pos_y, 5, 1)
        self.gridLayout1.addWidget(self.label_charging_time, 6, 0)
        self.gridLayout1.addWidget(self.lineEdit_charging_time, 6, 1)
        self.gridLayout1.addWidget(self.label_capacity, 7, 0)
        self.gridLayout1.addWidget(self.lineEdit_capacity, 7, 1)

        # QPusButtons - functions
        self.button_change_loading_station.clicked.connect(self.change_loading_station_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        # Adding to Layout
        self.hLayout1.addStretch(1)
        self.hLayout1.addWidget(self.button_change_loading_station)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_user_info)

        self.setLayout(self.vLayout1)

    def change_loading_station_clicked(self):
        if (self.lineEdit_loading_station_name.text() == '' or self.lineEdit_length.text() == ''
                or self.lineEdit_width.text() == '' or self.lineEdit_pos_x.text() == ''
                or self.lineEdit_pos_y.text() == '' or self.lineEdit_charging_time == ''
                or self.lineEdit_capacity.text() == ''):
            self.label_user_info.setText('<font color=red>Please enter correct data...</font>')
        else:
            self.factory.delete_from_grid(self.loading_station)
            self.loading_station.id = str(self.lineEdit_loading_station_id.text())
            self.loading_station.name = str(self.lineEdit_loading_station_name.text())
            self.loading_station.length = int(self.lineEdit_length.text())
            self.loading_station.width = int(self.lineEdit_width.text())
            self.loading_station.pos_x = int(self.lineEdit_pos_x.text())
            self.loading_station.pos_y = int(self.lineEdit_pos_y.text())
            self.loading_station.charging_time = float(self.lineEdit_charging_time.text().replace(',', '.'))
            self.loading_station.capacity = int(self.lineEdit_capacity.text())
            if self.factory.check_factory_boundaries(self.loading_station):
                self.label_user_info.setText(
                    '<font color=red>The loading_station was placed outside the factory...</font>')
                self.loading_station.name = self.name
                self.loading_station.length = self.length
                self.loading_station.width = self.width
                self.loading_station.pos_x = self.pos_x
                self.loading_station.pos_y = self.pos_y
                self.loading_station.charging_time = self.charging_time
                self.loading_station.capacity = self.capacity
                self.lineEdit_loading_station_name.setText(self.name)
                self.lineEdit_length.setText(str(self.length))
                self.lineEdit_width.setText(str(self.width))
                self.lineEdit_pos_x.setText(str(self.pos_x))
                self.lineEdit_pos_y.setText(str(self.pos_y))
                self.lineEdit_charging_time.setText(str(self.loading_station.charging_time))
                self.lineEdit_capacity.setText(str(self.loading_station.capacity))
                return
            if self.factory.check_collision(self.loading_station):
                self.label_user_info.setText(
                    '<font color=red>The area where the object is to be placed is blocked...</font>')
                self.loading_station.name = self.name
                self.loading_station.length = self.length
                self.loading_station.width = self.width
                self.loading_station.pos_x = self.pos_x
                self.loading_station.pos_y = self.pos_y
                self.loading_station.charging_time = self.charging_time
                self.loading_station.capacity = self.capacity
                self.lineEdit_loading_station_name.setText(self.name)
                self.lineEdit_length.setText(str(self.length))
                self.lineEdit_width.setText(str(self.width))
                self.lineEdit_pos_x.setText(str(self.pos_x))
                self.lineEdit_pos_y.setText(str(self.pos_y))
                self.lineEdit_charging_time.setText(str(self.loading_station.charging_time))
                self.lineEdit_capacity.setText(str(self.loading_station.capacity))
                return
            if self.factory.check_for_duplicate_names(self.loading_station):
                self.label_user_info.setText('<font color=red>No duplicate names for objects allowed!</font>')
                self.loading_station.name = self.name
                self.loading_station.length = self.length
                self.loading_station.width = self.width
                self.loading_station.pos_x = self.pos_x
                self.loading_station.pos_y = self.pos_y
                self.loading_station.charging_time = self.charging_time
                self.loading_station.capacity = self.capacity
                self.lineEdit_loading_station_name.setText(self.name)
                self.lineEdit_length.setText(str(self.length))
                self.lineEdit_width.setText(str(self.width))
                self.lineEdit_pos_x.setText(str(self.pos_x))
                self.lineEdit_pos_y.setText(str(self.pos_y))
                self.lineEdit_charging_time.setText(str(self.loading_station.charging_time))
                self.lineEdit_capacity.setText(str(self.loading_station.capacity))
                return
            self.change_csv()
            self.factory.add_to_grid(self.loading_station)
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_loading_stations_table()
            self.close()

    def change_csv(self):
        shutil.copyfile(f'data/Current_Factory/Loading_Station_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Loading_Station_Data/{}_Loading_Station_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        print(self.loading_stations_pd)
        list_loading_station_data = self.loading_station.create_list()
        list_of_loading_stations = self.loading_stations_pd.values.tolist()
        print(self.amount_of_loading_stations)
        list_of_loading_stations.append(list_loading_station_data)
        print(list_of_loading_stations)
        self.loading_stations_pd = pd.DataFrame(list_of_loading_stations)
        self.loading_stations_pd.columns = ['ID', 'Name', 'Length', 'Width', 'X-Position', 'Y-Position',
                                            'Charging Time', 'Capacity']
        self.loading_stations_pd.to_csv(self.path_loading_station_database, sep=';')

    def cancel_clicked(self):
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())

