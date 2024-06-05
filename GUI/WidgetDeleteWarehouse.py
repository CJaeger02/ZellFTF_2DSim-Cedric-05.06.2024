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

# The WidgetDeleteWarehouse-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to delete an existing warehouse inside the current factory.

########################################################################################################################


class WidgetDeleteWarehouse(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar, *args, **kwargs):
        super(WidgetDeleteWarehouse, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar = sidebar
        if len(args) == 2:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            print(
                f'Inside CLASS - WidgetDeleteWarehouse - Warehouse to delete name - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name}')
            print(
                f'Inside CLASS - WidgetDeleteWarehouse - Warehouse to delete pos_x - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_x}')
            print(
                f'Inside CLASS - WidgetDeleteWarehouse - Warehouse to delete pos_y - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_y}')
            print(f'Inside CLASS - WidgetDeleteWarehouse - Warehouses - {self.factory.warehouses}')
            warehouse_name = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name
            for i in range(len(self.factory.warehouses)):
                if warehouse_name == self.factory.warehouses[i].name:
                    self.del_list_entry_no = i
                    self.warehouse_to_delete = self.factory.warehouses[i]
                    print(self.factory.warehouses[i].name)
                    print(self.del_list_entry_no)
        else:
            warehouse_name = args[0]

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(600, 600)
        self.setWindowTitle('ZellFTF - Deleting a warehouse')
        self.center()

        self.path_warehouse_database = f'data/Current_Factory/Warehouse_Data.csv'
        self.warehouses_pd = pd.read_csv(self.path_warehouse_database, sep=';', index_col=0)
        self.amount_of_warehouses = len(self.warehouses_pd.index)

        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        self.label_information = QLabel('Do you really want to delete the warehouse:')
        self.lineEdit_warehouse_name = QLineEdit(self)
        self.lineEdit_warehouse_name.setText(warehouse_name)
        self.lineEdit_warehouse_name.setEnabled(False)
        self.button_yes = QPushButton('Yes')
        self.button_cancel = QPushButton('Cancel')

        self.button_yes.clicked.connect(self.yes_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        self.hLayout1.addWidget(self.button_yes)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addWidget(self.label_information)
        self.vLayout1.addWidget(self.lineEdit_warehouse_name)
        self.vLayout1.addLayout(self.hLayout1)

        self.setLayout(self.vLayout1)

    def yes_clicked(self):
        self.factory.delete_from_grid(self.warehouse_to_delete)
        self.factory.delete_warehouse(self.del_list_entry_no)
        print(self.factory.warehouses)
        self.delete_from_csv()
        self.factoryScene.delete_factory_grid()
        self.factoryScene.draw_factory_grid()
        self.sidebar.set_warehouses_table()
        self.close()

    def cancel_clicked(self):
        self.close()

    def delete_from_csv(self):
        shutil.copyfile(f'data/Current_Factory/Warehouse_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Warehouse_Data/{}_Warehouse_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        warehouses_np = self.warehouses_pd.to_numpy()
        amount_of_warehouses = len(self.factory.warehouses)
        if self.del_list_entry_no > amount_of_warehouses - 1:
            return
        else:
            warehouses_np = np.delete(warehouses_np, self.del_list_entry_no, axis=0)
            self.warehouses_pd = pd.DataFrame(warehouses_np, columns=['ID', 'Name', 'Length', 'Width', 'X-Position',
                                                                      'Y-Position', 'Input-Position',
                                                                      'Output-Position', 'Input Products',
                                                                      'Output Products',
                                                                      'Processing Times', 'Input Buffer Sizes',
                                                                      'Output Buffer Sizes', 'Input Loading Times',
                                                                      'Output Loading Times'])
            list_of_warehouses = self.warehouses_pd.values.tolist()
            self.warehouses_pd = pd.DataFrame(list_of_warehouses)
            self.warehouses_pd.columns = ['ID', 'Name', 'Length', 'Width', 'X-Position', 'Y-Position', 'Input-Position',
                                          'Output-Position', 'Input Products', 'Output Products', 'Processing Times',
                                          'Input Buffer Sizes', 'Output Buffer Sizes', 'Input Loading Times',
                                          'Output Loading Times']
            # IDs neu zählen:
            for i in range(len(self.warehouses_pd.index)):
                self.warehouses_pd.iloc[i, self.warehouses_pd.columns.get_loc('ID')] = float(i + 1)
            self.warehouses_pd.to_csv(self.path_warehouse_database, sep=';')
        pass

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())
