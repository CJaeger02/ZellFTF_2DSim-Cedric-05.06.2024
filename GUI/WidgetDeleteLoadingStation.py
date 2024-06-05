# general packages
import shutil
import os

import numpy as np
import pandas as pd
import numpy as np
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

# The WidgetDeleteLoadingstation-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to delete an existing loading station inside the current factory.

########################################################################################################################


class WidgetDeleteLoadingStation(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar, *args, **kwargs):
        super(WidgetDeleteLoadingStation, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar = sidebar
        if len(args) == 2:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            print(
                f'Inside CLASS - WidgetDeleteLoadingStation - LoadingStation to delete name - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name}')
            print(
                f'Inside CLASS - WidgetDeleteLoadingStation - LoadingStation to delete pos_x - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_x}')
            print(
                f'Inside CLASS - WidgetDeleteLoadingStation - LoadingStation to delete pos_y - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_y}')
            print(f'Inside CLASS - WidgetDeleteLoadingStation - LoadingStation - {self.factory.loading_stations}')
            loading_station_name = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name
            for i in range(len(self.factory.loading_stations)):
                if loading_station_name == self.factory.loading_stations[i].name:
                    self.del_list_entry_no = i
                    self.loading_station_to_delete = self.factory.loading_stations[i]
                    print(self.factory.loading_stations[i].name)
                    print(self.del_list_entry_no)
        else:
            loading_station_name = args[0]

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(600, 600)
        self.setWindowTitle('ZellFTF - Deleting a loading station')
        self.center()

        self.path_loading_station_database = f'data/Current_Factory/Loading_Station_Data.csv'
        self.loading_stations_pd = pd.read_csv(self.path_loading_station_database, sep=';', index_col=0)
        self.amount_of_loading_stations = len(self.loading_stations_pd.index)

        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        self.label_information = QLabel('Do you really want to delete the loading station:')
        self.lineEdit_loading_station_name = QLineEdit(self)
        self.lineEdit_loading_station_name.setText(loading_station_name)
        self.lineEdit_loading_station_name.setEnabled(False)
        self.button_yes = QPushButton('Yes')
        self.button_cancel = QPushButton('Cancel')

        self.button_yes.clicked.connect(self.yes_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        self.hLayout1.addWidget(self.button_yes)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addWidget(self.label_information)
        self.vLayout1.addWidget(self.lineEdit_loading_station_name)
        self.vLayout1.addLayout(self.hLayout1)

        self.setLayout(self.vLayout1)

    def yes_clicked(self):
        self.factory.delete_from_grid(self.loading_station_to_delete)
        self.factory.delete_loading_station(self.del_list_entry_no)
        print(self.factory.loading_stations)
        self.delete_from_csv()
        self.factoryScene.delete_factory_grid()
        self.factoryScene.draw_factory_grid()
        self.sidebar.set_loading_stations_table()
        self.close()

    def cancel_clicked(self):
        self.close()

    def delete_from_csv(self):
        shutil.copyfile(f'data/Current_Factory/Loading_Station_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Loading_Station_Data/{}Loading_Station_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        loading_stations_np = self.loading_stations_pd.to_numpy()
        amount_of_loading_stations = len(self.factory.loading_stations)
        if self.del_list_entry_no > amount_of_loading_stations - 1:
            return
        else:
            loading_stations_np = np.delete(loading_stations_np, self.del_list_entry_no, axis=0)
            self.loading_stations_pd = pd.DataFrame(loading_stations_np,
                                                    columns=['ID', 'Name', 'Length', 'Width', 'X-Position',
                                                             'Y-Position', 'Charging Time', 'Capacity'])
            list_of_loading_stations = self.loading_stations_pd.values.tolist()
            self.loading_stations_pd = pd.DataFrame(list_of_loading_stations)
            self.loading_stations_pd.columns = ['ID', 'Name', 'Length', 'Width', 'X-Position', 'Y-Position',
                                                'Charging Time', 'Capacity']
            # IDs neu zählen:
            for i in range(len(self.loading_stations_pd.index)):
                self.loading_stations_pd.iloc[i, self.loading_stations_pd.columns.get_loc('ID')] = float(i + 1)
            self.loading_stations_pd.to_csv(self.path_loading_station_database, sep=';')
        pass

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())
