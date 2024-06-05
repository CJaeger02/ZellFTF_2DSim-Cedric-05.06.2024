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
from FactoryObjects.Machine import Machine
from GUI.MachineScene import MachineScene
from GUI.MachineView import MachineView


########################################################################################################################

# The WidgetDeleteMachine-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to delete an existing machine inside the current factory.

########################################################################################################################


class WidgetDeleteMachine(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar, *args, **kwargs):
        super(WidgetDeleteMachine, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar = sidebar
        if len(args) == 2:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            print(f'Inside CLASS - WidgetDeleteMachine - Machine to delete name - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name}')
            print(f'Inside CLASS - WidgetDeleteMachine - Machine to delete pos_x - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_x}')
            print(f'Inside CLASS - WidgetDeleteMachine - Machine to delete pos_y - {self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_y}')
            print(f'Inside CLASS - WidgetDeleteMachine - Machines - {self.factory.machines}')
            machine_name = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name
            for i in range(len(self.factory.machines)):
                if machine_name == self.factory.machines[i].name:
                    self.del_list_entry_no = i
                    self.machine_to_delete = self.factory.machines[i]
                    print(self.factory.machines[i].name)
                    print(self.del_list_entry_no)
        else:
            machine_name = args[0]

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(600, 600)
        self.setWindowTitle('ZellFTF - Deleting a machine')
        self.center()

        self.path_machine_database = f'data/Current_Factory/Machine_Data.csv'
        self.machines_pd = pd.read_csv(self.path_machine_database, sep=';', index_col=0)
        self.amount_of_machines = len(self.machines_pd.index)

        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        self.label_information = QLabel('Do you really want to delete the machine:')
        self.lineEdit_machine_name = QLineEdit(self)
        self.lineEdit_machine_name.setText(machine_name)
        self.lineEdit_machine_name.setEnabled(False)
        self.button_yes = QPushButton('Yes')
        self.button_cancel = QPushButton('Cancel')

        self.button_yes.clicked.connect(self.yes_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        self.hLayout1.addWidget(self.button_yes)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addWidget(self.label_information)
        self.vLayout1.addWidget(self.lineEdit_machine_name)
        self.vLayout1.addLayout(self.hLayout1)

        self.setLayout(self.vLayout1)

    def yes_clicked(self):
        self.factory.delete_from_grid(self.machine_to_delete)
        self.factory.delete_machine(self.del_list_entry_no)
        print(self.factory.machines)
        self.delete_from_csv()
        self.factoryScene.delete_factory_grid()
        self.factoryScene.draw_factory_grid()
        self.sidebar.set_machines_table()
        self.close()

    def cancel_clicked(self):
        self.close()

    def delete_from_csv(self):
        shutil.copyfile(f'data/Current_Factory/Machine_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Machine_Data/{}_Machine_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        machines_np = self.machines_pd.to_numpy()
        amount_of_machines = len(self.factory.machines)
        if self.del_list_entry_no > amount_of_machines:
            print('NOOOOO!!')
            return
        else:
            machines_np = np.delete(machines_np, self.del_list_entry_no, axis=0)
            self.machines_pd = pd.DataFrame(machines_np, columns=['ID', 'Name', 'Length', 'Width', 'X-Position',
                                                                  'Y-Position', 'Input-Position',
                                                                  'Output-Position', 'Input Products', 'Output Products',
                                                                  'Processing Times','Input Buffer Sizes',
                                                                  'Output Buffer Sizes', 'Input Loading Times',
                                                                  'Output Loading Times'])
            print(self.machines_pd)
            '''list_of_machines = self.machines_pd.values.tolist()
            self.machines_pd = pd.DataFrame(list_of_machines)
            self.machines_pd.columns = ['ID', 'Name', 'Length', 'Width', 'X-Position', 'Y-Position', 'Input-Position',
                                        'Output-Position', 'Input Products', 'Output Products', 'Processing Times',
                                        'Input Buffer Sizes', 'Output Buffer Sizes', 'Input Loading Times',
                                        'Output Loading Times']'''
            # IDs neu zählen:
            for i in range(len(self.machines_pd.index)):
                self.machines_pd.iloc[i, self.machines_pd.columns.get_loc('ID')] = float(i + 1)
            self.machines_pd.to_csv(self.path_machine_database, sep=';')
        pass

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())