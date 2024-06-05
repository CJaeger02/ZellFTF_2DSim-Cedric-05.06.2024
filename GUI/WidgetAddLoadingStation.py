# general packages
import shutil
import os

import pandas as pd
from datetime import datetime

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# own packages
from FactoryObjects.Factory import Factory
from GUI.FactoryScene import FactoryScene
from FactoryObjects.LoadingStation import LoadingStation
from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects


########################################################################################################################

# The WidgetAddLoadingstation-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to create a new loading station for the current factory.
# In this window all necessary data about the loading station are entered.

########################################################################################################################


class WidgetAddLoadingStation(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar: WidgetListOfFactoryObjects,
                 *args):
        super(WidgetAddLoadingStation, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar: WidgetListOfFactoryObjects = sidebar
        self.loading_station = LoadingStation()
        if len(args) > 0:
            self.loading_station.pos_x = args[0]
            self.loading_station.pos_y = args[1]
        print(f'Inside CLASS - WidgetAddLoadingStation - Loading Station - {self.loading_station}')

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        """if not os.path.isfile(f'data/Current_Factory/Loading_Station_Data.csv'):
            print('Creating Path...')
            current_loading_station_database = open(f'data/Current_Factory/Loading_Station_Data.csv', 'w')
            current_loading_station_database.write(';ID;Name;Length;Width;X-Position;Y-Position;Charging Time;'
                                                   'Capacity;')
            # self.machine_data.write('\n0;0;default_machine;1;1;0;0;[0,0];[0,0];[\'default_product\'];'
            #                              '[\'default_product\'];30;1;1;0;0;[\'W0\'];[\'W0\']')
            current_loading_station_database.close()"""

        if not os.path.isfile(f'data/Saved_Factories/{self.factory.name}/Loading_Station_Data.csv'):
            print('Creating Path...')
            loading_station_database = open(f'data/Saved_Factories/{self.factory.name}/Loading_Station_Data.csv', 'w')
            loading_station_database.write(';ID;Name;Length;Width;X-Position;Y-Position;Charging Time;Capacity;')
            # self.machine_data.write('\n0;0;default_machine;1;1;0;0;[0,0];[0,0];[\'default_product\'];'
            #                              '[\'default_product\'];30;1;1;0;0;[\'W0\'];[\'W0\']')
            loading_station_database.close()

        if not os.path.exists(f'data/Saved_Factories/{self.factory.name}/Archiv/Loading_Station_Data'):
            os.makedirs(f'data/Saved_Factories/{self.factory.name}/Archiv/Loading_Station_Data')

        self.resize(500, 250)
        self.setMaximumSize(600, 600)
        self.setWindowTitle('ZellFTF - Adding a loading station')
        self.center()

        # self.path_loading_station_database = f'data/Saved_Factories/{self.factory.name}/Loading_Station_Data.csv'
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

        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)

        self.button_cancel = QPushButton('Cancel')
        self.button_add_loading_station = QPushButton('Add Loading Station')
        self.label_user_info = QLabel('Waiting for action...')
        self.label_user_info.setAlignment(Qt.AlignCenter)

        # Automatic setting of the ID
        print(f'Anzahl Maschinen: {self.amount_of_loading_stations}')
        print(self.loading_stations_pd.iloc)
        if self.amount_of_loading_stations == 0:
            self.lineEdit_loading_station_id.setText('0')
        else:
            print(self.loading_stations_pd.iloc[self.amount_of_loading_stations - 1]['ID'] + 1)
            id_no = (self.loading_stations_pd.iloc[self.amount_of_loading_stations - 1]['ID'] + 1).item()
            self.lineEdit_loading_station_id.setText(str(id_no))

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
        self.button_add_loading_station.clicked.connect(self.add_loading_station_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        # Adding to Layout
        self.hLayout1.addStretch(1)
        self.hLayout1.addWidget(self.button_add_loading_station)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_user_info)

        self.setLayout(self.vLayout1)

    def add_loading_station_clicked(self):
        if (self.lineEdit_loading_station_name.text() == '' or self.lineEdit_length.text() == ''
                or self.lineEdit_width.text() == '' or self.lineEdit_pos_x.text() == ''
                or self.lineEdit_pos_y.text() == '' or self.lineEdit_charging_time.text() == ''
                or self.lineEdit_capacity.text() == ''):
            self.label_user_info.setText('<font color=red>Please enter correct data...</font>')
        else:
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
                    '<font color=red>The loading station was placed outside the factory...</font>')
                return
            if self.factory.check_collision(self.loading_station):
                self.label_user_info.setText(
                    '<font color=red>The area where the object is to be placed is blocked...</font>')
                return
            if self.factory.check_for_duplicate_names(self.loading_station):
                self.label_user_info.setText('<font color=red>No duplicate names for objects allowed!</font>')
                return
            """
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station ID = {self.loading_station.id}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station Name = {self.loading_station.name}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station Length = {self.loading_station.length}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station Width = {self.loading_station.width}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station X-POS = {self.loading_station.pos_x}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station Y-POS = {self.loading_station.pos_y}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Station Charging Time = '
                  f'{self.loading_station.charging_time}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Stations = {self.factory.loading_stations}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Stations = {self.factory.loading_stations[0]}')
            print(f'Inside CLASS WidgetAddLoadingStation - Loading Stations = {self.factory.loading_stations[0].name}')
            """
            self.factory.add_loading_station(self.loading_station)
            self.add_to_csv()
            self.factory.add_to_grid(self.loading_station)
            # self.factory.fill_grid()
            """for y in range(self.factory.no_rows):
                for x in range(self.factory.no_columns):
                    print(f'Inside CLASS WidgetAddLoadingStation - '
                          f'factory_grid_layout[{x}][{y}] = {self.factory.factory_grid_layout[x][y]}')"""
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_loading_stations_table()
            self.close()

    def add_to_csv(self):
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
