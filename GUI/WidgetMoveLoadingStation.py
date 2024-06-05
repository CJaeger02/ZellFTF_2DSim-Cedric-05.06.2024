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


########################################################################################################################

# The WidgetMoveLoadingStation-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# The loading station can be moved inside the factory.

########################################################################################################################

class WidgetMoveLoadingStation(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, *args, **kwargs):
        super(WidgetMoveLoadingStation, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.count_of_loading_station = 0
        if len(args) == 2:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            loading_station_name = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name
            for i in range(len(self.factory.loading_stations)):
                if loading_station_name == self.factory.loading_stations[i].name:
                    self.count_of_loading_station = i
                    self.loading_station_to_move = self.factory.loading_stations[i]
                    print(
                        f'Inside CLASS - WidgetMoveLoadingStation - Warehouse to move name - {self.factory.loading_stations[i].name}')
                    print(self.count_of_loading_station)
        else:
            loading_station_name = args[0]

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(200, 100)
        self.setWindowTitle('ZellFTF - Moving a loading station')
        self.center()

        self.path_loading_station_database = f'data/Current_Factory/Loading_Station_Data.csv'
        self.loading_stations_pd = pd.read_csv(self.path_loading_station_database, sep=';', index_col=0)
        self.amount_of_loading_stations = len(self.loading_stations_pd.index)

        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()
        self.gridLayout1 = QGridLayout()

        self.label_information = QLabel('You can move the following loading_station:')
        self.lineEdit_machine_name = QLineEdit(self)
        self.lineEdit_machine_name.setText(loading_station_name)
        self.lineEdit_machine_name.setEnabled(False)

        self.label_old_position = QLabel('Old position')
        self.label_new_position = QLabel('New position')
        self.label_pos_x = QLabel('X-position of loading station in factory grid:')
        self.lineEdit_old_pos_x = QLineEdit(self)
        self.lineEdit_old_pos_x.setAlignment(Qt.AlignCenter)
        self.lineEdit_old_pos_x.setText(str(self.loading_station_to_move.pos_x))
        self.lineEdit_old_pos_x.setEnabled(False)
        self.lineEdit_new_pos_x = QLineEdit(self)
        self.lineEdit_new_pos_x.setAlignment(Qt.AlignCenter)
        self.lineEdit_new_pos_x.setText(str(self.factory.loading_stations[self.count_of_loading_station].pos_x))
        self.label_pos_y = QLabel('Y-position of loading station in factory grid:')
        self.lineEdit_old_pos_y = QLineEdit(self)
        self.lineEdit_old_pos_y.setAlignment(Qt.AlignCenter)
        self.lineEdit_old_pos_y.setText(str(self.loading_station_to_move.pos_y))
        self.lineEdit_old_pos_y.setEnabled(False)
        self.lineEdit_new_pos_y = QLineEdit(self)
        self.lineEdit_new_pos_y.setAlignment(Qt.AlignCenter)
        self.lineEdit_new_pos_y.setText(str(self.factory.loading_stations[self.count_of_loading_station].pos_y))
        self.button_save = QPushButton('Save')
        self.button_cancel = QPushButton('Cancel')
        self.label_user_info = QLabel('Waiting for action...')
        self.label_user_info.setAlignment(Qt.AlignCenter)

        self.hLine2 = QFrame(self)
        self.hLine2.setFrameShape(QFrame.HLine)
        self.hLine2.setLineWidth(1)
        self.hLine2.setFrameShadow(QFrame.Sunken)

        self.button_save.clicked.connect(self.save_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        self.hLayout1.addWidget(self.button_save)
        self.hLayout1.addWidget(self.button_cancel)

        self.gridLayout1.addWidget(self.label_old_position, 0, 1)
        self.gridLayout1.addWidget(self.label_new_position, 0, 2)
        self.gridLayout1.addWidget(self.label_pos_x, 1, 0)
        self.gridLayout1.addWidget(self.lineEdit_old_pos_x, 1, 1)
        self.gridLayout1.addWidget(self.lineEdit_new_pos_x, 1, 2)
        self.gridLayout1.addWidget(self.label_pos_y, 2, 0)
        self.gridLayout1.addWidget(self.lineEdit_old_pos_y, 2, 1)
        self.gridLayout1.addWidget(self.lineEdit_new_pos_y, 2, 2)

        self.vLayout1.addWidget(self.label_information)
        self.vLayout1.addWidget(self.lineEdit_machine_name)
        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.hLine2)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_user_info)

        self.setLayout(self.vLayout1)

    def save_clicked(self):
        self.factory.delete_from_grid(self.factory.loading_stations[self.count_of_loading_station])
        self.factory.loading_stations[self.count_of_loading_station].pos_x = int(self.lineEdit_new_pos_x.text())
        self.factory.loading_stations[self.count_of_loading_station].pos_y = int(self.lineEdit_new_pos_y.text())
        print(self.factory.loading_stations[self.count_of_loading_station].pos_x)
        print(self.factory.loading_stations[self.count_of_loading_station].pos_y)
        if self.factory.check_factory_boundaries(self.factory.loading_stations[self.count_of_loading_station]):
            self.label_user_info.setText('<font color=red>The loading station was placed outside the factory...</font>')
            self.factory.loading_stations[self.count_of_loading_station].pos_x = int(self.lineEdit_old_pos_x.text())
            self.factory.loading_stations[self.count_of_loading_station].pos_y = int(self.lineEdit_old_pos_y.text())
            print(self.factory.loading_stations[self.count_of_loading_station].pos_x)
            print(self.factory.loading_stations[self.count_of_loading_station].pos_y)
            self.factory.add_to_grid(self.factory.loading_stations[self.count_of_loading_station])
            print(self.factory.factory_grid_layout)
            return
        if self.factory.check_collision(self.factory.loading_stations[self.count_of_loading_station]):
            self.label_user_info.setText(
                '<font color=red>The area where the object is to be placed is blocked...</font>')
            self.factory.loading_stations[self.count_of_loading_station].pos_x = int(self.lineEdit_old_pos_x.text())
            self.factory.loading_stations[self.count_of_loading_station].pos_y = int(self.lineEdit_old_pos_y.text())
            print(self.factory.loading_stations[self.count_of_loading_station].pos_x)
            print(self.factory.loading_stations[self.count_of_loading_station].pos_y)
            self.factory.add_to_grid(self.factory.loading_stations[self.count_of_loading_station])
            print(self.factory.factory_grid_layout)
            return
        diff_pos_x = int(self.lineEdit_new_pos_x.text()) - int(self.lineEdit_old_pos_x.text())
        diff_pos_y = int(self.lineEdit_new_pos_y.text()) - int(self.lineEdit_old_pos_y.text())
        self.update_factory_loading_stations(diff_pos_x, diff_pos_y)
        self.update_csv(diff_pos_x, diff_pos_y)
        self.factory.add_to_grid(self.factory.loading_stations[self.count_of_loading_station])
        self.factoryScene.delete_factory_grid()
        self.factoryScene.draw_factory_grid()
        self.close()

        pass

    def update_factory_loading_stations(self, diff_pos_x, diff_pos_y):
        print(self.factory.loading_stations[self.count_of_loading_station].create_list())

    def update_csv(self, diff_pos_x, diff_pos_y):
        shutil.copyfile(f'data/Current_Factory/Loading_Station_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Machine_Data/{}_Loading_Station_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        loading_stations_np = self.loading_stations_pd.to_numpy()
        loading_stations_np[self.count_of_loading_station][4] = self.factory.loading_stations[self.count_of_loading_station].pos_x
        loading_stations_np[self.count_of_loading_station][5] = self.factory.loading_stations[self.count_of_loading_station].pos_y
        self.loading_stations_pd = pd.DataFrame(loading_stations_np, columns=['ID', 'Name', 'Length', 'Width',
                                                                              'X-Position', 'Y-Position',
                                                                              'Charging Time', 'Capacity'])
        self.loading_stations_pd.to_csv(self.path_loading_station_database, sep=';')

    def cancel_clicked(self):
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())
