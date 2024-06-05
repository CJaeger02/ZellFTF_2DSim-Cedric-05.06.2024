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
from FactoryObjects.Warehouse import Warehouse
from GUI.WarehouseScene import WarehouseScene
from GUI.WarehouseView import WarehouseView
from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects

########################################################################################################################

# The WidgetProperties-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to change properties of a factory object (Warehouse, Machine, Loading Station) .
# In this window all necessary data about the factory object can be changed.

########################################################################################################################


class WidgetPropertiesWarehouse(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, sidebar: WidgetListOfFactoryObjects, *args, **kwargs):
        super(WidgetPropertiesWarehouse, self).__init__()
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.sidebar: WidgetListOfFactoryObjects = sidebar
        if len(args) > 0:
            self.column_clicked = args[0]
            self.row_clicked = args[1]
            self.warehouse = self.factory.factory_grid_layout[self.column_clicked][self.row_clicked]
            print(f'Inside CLASS - WidgetPropertiesMachine - Warehouse - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked]}')
            print(f'Inside CLASS - WidgetPropertiesMachine - Warehouse - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].name}')
            print(f'Inside CLASS - WidgetPropertiesMachine - Warehouse X-Position - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_x}')
            print(f'Inside CLASS - WidgetPropertiesMachine - Warehouse Y-Position - '
                  f'{self.factory.factory_grid_layout[self.column_clicked][self.row_clicked].pos_y}')

        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(600, 600)
        self.setWindowTitle(f'ZellFTF - Change properties of "{self.warehouse.name}"')
        self.center()

        self.path_warehouse_database = f'data/Current_Factory/Warehouse_Data.csv'
        self.warehouses_pd = pd.read_csv(self.path_warehouse_database, sep=';', index_col=0)
        self.amount_of_warehouses = len(self.warehouses_pd.index)

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.gridLayout1 = QGridLayout()
        self.hLayout1 = QHBoxLayout()

        # Widgets
        self.label_warehouse_id = QLabel('Warehouse ID:')
        self.lineEdit_warehouse_id = QLineEdit(self)
        self.lineEdit_warehouse_id.setAlignment(Qt.AlignCenter)
        self.lineEdit_warehouse_id.setEnabled(False)
        self.label_warehouse_name = QLabel('Name of the warehouse:')
        self.lineEdit_warehouse_name = QLineEdit(self)
        self.lineEdit_warehouse_name.setAlignment(Qt.AlignCenter)
        self.label_length = QLabel('Length of warehouse (m):')
        self.lineEdit_length = QLineEdit(self)
        self.lineEdit_length.setAlignment(Qt.AlignCenter)
        self.lineEdit_length.setValidator(QIntValidator())
        self.label_width = QLabel('Width of warehouse (m):')
        self.lineEdit_width = QLineEdit(self)
        self.lineEdit_width.setAlignment(Qt.AlignCenter)
        self.lineEdit_width.setValidator(QIntValidator())
        self.label_pos_x = QLabel('X-position of warehouse in factory grid:')
        self.lineEdit_pos_x = QLineEdit(self)
        self.lineEdit_pos_x.setAlignment(Qt.AlignCenter)
        self.label_pos_y = QLabel('Y-position of warehouse in factory grid:')
        self.lineEdit_pos_y = QLineEdit(self)
        self.lineEdit_pos_y.setAlignment(Qt.AlignCenter)
        self.label_pos_input_output = QLabel('Position of the input and output:')
        self.button_pos_input_output = QPushButton("Define position of input/output")
        self.label_input_output_products = QLabel('Input and output products of the warehouse:')
        self.button_input_output_products = QPushButton('Define all input/output products')
        self.label_processing_time = QLabel('Processing time (s):')
        self.lineEdit_processing_time = QLineEdit(self)
        self.lineEdit_processing_time.setAlignment(Qt.AlignCenter)
        self.lineEdit_processing_time.setValidator(QIntValidator())
        self.label_buffer_size_loading_time = QLabel('Input/Output buffer size and loading times for each product:')
        self.button_buffer_size_loading_time = QPushButton('Define buffer size and loading times')
        self.label_buffer_input_output = QLabel('Buffer size of the input and output for each product (pcs):')
        self.button_buffer_input_output = QPushButton('Define input/output buffer size')
        self.label_loading_time_input_output = QLabel('Input/Output loading time for each product (s):')
        self.button_loading_time_input_output = QPushButton('Define loading times')

        self.lineEdit_warehouse_id.setText(str(self.warehouse.id))
        self.lineEdit_warehouse_name.setText(str(self.warehouse.name))
        self.lineEdit_length.setText(str(self.warehouse.length))
        self.lineEdit_width.setText(str(self.warehouse.width))
        self.lineEdit_pos_x.setText(str(self.warehouse.pos_x))
        self.lineEdit_pos_y.setText(str(self.warehouse.pos_y))
        self.lineEdit_processing_time.setText(str(self.warehouse.process_time))

        self.id = self.lineEdit_warehouse_id.text()
        self.name = self.lineEdit_warehouse_name.text()
        self.length = int(self.lineEdit_length.text())
        self.width = int(self.lineEdit_width.text())
        self.pos_x = int(self.lineEdit_pos_x.text())
        self.pos_y = int(self.lineEdit_pos_y.text())
        self.processing_time = int(self.lineEdit_processing_time.text())
        self.pos_input = self.warehouse.pos_input
        self.pos_output = self.warehouse.pos_output
        self.input_products = self.warehouse.input_products
        self.output_products = self.warehouse.output_products
        self.buffer_input = self.warehouse.buffer_input
        self.buffer_output = self.warehouse.buffer_output
        self.loading_time_input = self.warehouse.loading_time_input
        self.loading_time_output = self.warehouse.loading_time_output

        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)

        self.button_cancel = QPushButton('Cancel')
        self.button_change_warehouse = QPushButton('Change Properties Warehouse')
        self.label_user_info = QLabel('Waiting for action...')
        self.label_user_info.setAlignment(Qt.AlignCenter)

        # Add Widgets to gridLayout1
        self.gridLayout1.addWidget(self.label_warehouse_id, 0, 0)
        self.gridLayout1.addWidget(self.lineEdit_warehouse_id, 0, 1)
        self.gridLayout1.addWidget(self.label_warehouse_name, 1, 0)
        self.gridLayout1.addWidget(self.lineEdit_warehouse_name, 1, 1)
        self.gridLayout1.addWidget(self.label_length, 2, 0)
        self.gridLayout1.addWidget(self.lineEdit_length, 2, 1)
        self.gridLayout1.addWidget(self.label_width, 3, 0)
        self.gridLayout1.addWidget(self.lineEdit_width, 3, 1)
        self.gridLayout1.addWidget(self.label_pos_x, 4, 0)
        self.gridLayout1.addWidget(self.lineEdit_pos_x, 4, 1)
        self.gridLayout1.addWidget(self.label_pos_y, 5, 0)
        self.gridLayout1.addWidget(self.lineEdit_pos_y, 5, 1)
        self.gridLayout1.addWidget(self.label_processing_time, 6, 0)
        self.gridLayout1.addWidget(self.lineEdit_processing_time, 6, 1)
        self.gridLayout1.addWidget(self.label_pos_input_output, 7, 0)
        self.gridLayout1.addWidget(self.button_pos_input_output, 7, 1)
        self.gridLayout1.addWidget(self.label_input_output_products, 8, 0)
        self.gridLayout1.addWidget(self.button_input_output_products, 8, 1)
        self.gridLayout1.addWidget(self.label_buffer_input_output, 9, 0)
        self.gridLayout1.addWidget(self.button_buffer_input_output, 9, 1)
        self.gridLayout1.addWidget(self.label_loading_time_input_output, 10, 0)
        self.gridLayout1.addWidget(self.button_loading_time_input_output, 10, 1)

        # QPusButtons - functions
        self.button_pos_input_output.clicked.connect(self.pos_input_output_clicked)
        self.button_input_output_products.clicked.connect(self.define_input_output_products_clicked)
        self.button_buffer_input_output.clicked.connect(self.define_buffer_size_clicked)
        self.button_loading_time_input_output.clicked.connect(self.define_loading_time_clicked)
        self.button_change_warehouse.clicked.connect(self.change_machine_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        # Adding to Layout
        self.hLayout1.addStretch(1)
        self.hLayout1.addWidget(self.button_change_warehouse)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_user_info)

        self.setLayout(self.vLayout1)

    def pos_input_output_clicked(self):
        if (self.lineEdit_length.text() == '' or self.lineEdit_width.text() == '' or
                self.lineEdit_pos_x.text() == '' or self.lineEdit_pos_y.text() == ''):
            self.label_user_info.setText('<font color=red>Please enter correct data...</font>')
            print('ENTER CORRECT DATA')
        else:
            self.factory.delete_from_grid(self.warehouse)
            self.warehouse.length = int(self.lineEdit_length.text())
            self.warehouse.width = int(self.lineEdit_width.text())
            self.warehouse.pos_x = int(self.lineEdit_pos_x.text())
            self.warehouse.pos_y = int(self.lineEdit_pos_y.text())
            if self.factory.check_collision(self.warehouse):
                self.label_user_info.setText(
                '<font color=red>The area where the object is to be placed is blocked...</font>')
                '''self.warehouse.name = self.name
                self.warehouse.length = self.length
                self.warehouse.width = self.width
                self.warehouse.pos_x = self.pos_x
                self.warehouse.pos_y = self.pos_y
                self.warehouse.process_time = self.processing_time
                self.lineEdit_warehouse_name.setText(self.name)
                self.lineEdit_length.setText(str(self.length))
                self.lineEdit_width.setText(str(self.width))
                self.lineEdit_pos_x.setText(str(self.pos_x))
                self.lineEdit_pos_y.setText(str(self.pos_y))
                self.lineEdit_processing_time.setText(str(self.warehouse.process_time))'''
                self.reset_old_properties()
                self.factory.add_to_grid(self.warehouse)
                return
            if self.factory.check_factory_boundaries(self.warehouse):
                self.label_user_info.setText('<font color=red>The object was placed outside the factory...</font>')
                self.reset_old_properties()
                self.factory.add_to_grid(self.warehouse)
                return
            if int(self.warehouse.local_pos_input[0]) >= int(self.warehouse.length) or \
                    int(self.warehouse.local_pos_input[1]) >= int(self.warehouse.width) or \
                    int(self.warehouse.local_pos_output[0]) >= int(self.warehouse.length) or \
                    int(self.warehouse.local_pos_output[1]) >= int(self.warehouse.width):
                self.warehouse.local_pos_input = [0, 0]
                self.warehouse.local_pos_output = [0, 0]
                self.widget_define_input_output_position = WidgetDefineInputOutputPosition(self.factory, self.warehouse)
            else:
                self.widget_define_input_output_position = WidgetDefineInputOutputPosition(self.factory, self.warehouse)
            self.widget_define_input_output_position.show()
            self.factory.add_to_grid(self.warehouse)
        print('WIDGET - DEFINE INPUT/OUTPUT OPENED')

    def define_input_output_products_clicked(self):
        self.widget_define_input_output_products = WidgetDefineInputOutputProducts(self.factory, self.warehouse)
        self.widget_define_input_output_products.show()

    def define_buffer_size_clicked(self):
        self.widget_define_buffer_size_loading_time = WidgetDefineBufferSizeLoadingTime(self.factory, self.warehouse)
        self.widget_define_buffer_size_loading_time.show()

    def define_loading_time_clicked(self):
        self.widget_define_buffer_size_loading_time = WidgetDefineBufferSizeLoadingTime(self.factory, self.warehouse)
        self.widget_define_buffer_size_loading_time.show()

    def change_machine_clicked(self):
        if (self.lineEdit_warehouse_name.text() == '' or self.lineEdit_length.text() == ''
                or self.lineEdit_width.text() == '' or self.lineEdit_pos_x.text() == ''
                or self.lineEdit_pos_y.text() == '' or self.lineEdit_processing_time == ''):
            self.label_user_info.setText('<font color=red>Please enter correct machine data...</font>')
        else:
            self.factory.delete_from_grid(self.warehouse)
            self.warehouse.id = str(self.lineEdit_warehouse_id.text())
            self.warehouse.name = str(self.lineEdit_warehouse_name.text())
            self.warehouse.length = int(self.lineEdit_length.text())
            self.warehouse.width = int(self.lineEdit_width.text())
            self.warehouse.pos_x = int(self.lineEdit_pos_x.text())
            self.warehouse.pos_y = int(self.lineEdit_pos_y.text())
            self.warehouse.process_time = int(self.lineEdit_processing_time.text())
            if self.factory.check_factory_boundaries(self.warehouse):
                self.label_user_info.setText('<font color=red>The warehouse was placed outside the factory...</font>')
                self.reset_old_properties()
                return
            if self.factory.check_collision(self.warehouse):
                self.label_user_info.setText(
                    '<font color=red>The area where the object is to be placed is blocked...</font>')
                self.reset_old_properties()
                return
            if self.factory.check_for_duplicate_names(self.warehouse):
                self.label_user_info.setText('<font color=red>No duplicate names for objects allowed!</font>')
                self.reset_old_properties()
                return
            if self.set_input_output() == False:
                self.label_user_info.setText('<font color=red>Input/Output outside of warehouse!</font>')
                self.reset_old_properties()
                return
            self.change_csv()
            self.factory.add_to_grid(self.warehouse)
            self.factoryScene.delete_factory_grid()
            self.factoryScene.draw_factory_grid()
            self.sidebar.set_warehouses_table()
            self.close()

    def set_input_output(self):
        if (self.warehouse.local_pos_input[0] > (self.warehouse.length - 1) or
                self.warehouse.local_pos_output[0] > (self.warehouse.length - 1) or
                self.warehouse.local_pos_input[1] > (self.warehouse.width - 1) or
                self.warehouse.local_pos_output[1] > (self.warehouse.width - 1)):
            return False
        if self.warehouse.local_pos_input == [0, 0] and self.warehouse.local_pos_output == [0, 0]:
            self.warehouse.pos_input = [self.warehouse.pos_x, self.warehouse.pos_y]
            if self.warehouse.length > 1:
                self.warehouse.pos_output = [self.warehouse.pos_x + 1, self.warehouse.pos_y]
            elif self.warehouse.width > 1:
                self.warehouse.pos_output = [self.warehouse.pos_x, self.warehouse.pos_y + 1]
            else:
                self.warehouse.pos_output = [self.warehouse.pos_x, self.warehouse.pos_y]
        else:
            np_local_pos_input = np.array(self.warehouse.local_pos_input)
            np_pos_machine = np.array([int(self.warehouse.pos_x), int(self.warehouse.pos_y)])
            self.warehouse.pos_input = (np_pos_machine + np_local_pos_input).tolist()
            np_local_pos_output = np.array(self.warehouse.local_pos_output)
            np_pos_machine = np.array([int(self.warehouse.pos_x), int(self.warehouse.pos_y)])
            self.warehouse.pos_output = (np_pos_machine + np_local_pos_output).tolist()

    def change_csv(self):
        shutil.copyfile(f'data/Current_Factory/Warehouse_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Warehouse_Data/{}_Warehouse_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        print(self.warehouses_pd)
        list_warehouse_data = self.warehouse.create_list()
        list_of_warehouses = self.warehouses_pd.values.tolist()
        print(list_of_warehouses)
        for i in range(len(self.factory.warehouses)):
            if self.name == self.factory.warehouses[i].name:
                print(list_of_warehouses[i])
                list_of_warehouses[i] = list_warehouse_data
        print(list_of_warehouses)
        self.warehouses_pd = pd.DataFrame(list_of_warehouses)
        self.warehouses_pd.columns = ['ID', 'Name', 'Length', 'Width', 'X-Position', 'Y-Position', 'Input-Position',
                                      'Output-Position', 'Input Products', 'Output Products', 'Processing Times',
                                      'Input Buffer Sizes', 'Output Buffer Sizes', 'Input Loading Times',
                                      'Output Loading Times']
        self.warehouses_pd.to_csv(self.path_warehouse_database, sep=';')

    def cancel_clicked(self):
        self.warehouse.name = self.name
        self.warehouse.length = self.length
        self.warehouse.width = self.width
        self.warehouse.pos_x = self.pos_x
        self.warehouse.pos_y = self.pos_y
        self.warehouse.process_time = self.processing_time
        self.close()

    def reset_old_properties(self):
        self.warehouse.name = self.name
        self.warehouse.length = self.length
        self.warehouse.width = self.width
        self.warehouse.pos_x = self.pos_x
        self.warehouse.pos_y = self.pos_y
        self.warehouse.process_time = self.processing_time
        self.warehouse.pos_input = self.pos_input
        self.warehouse.pos_output = self.pos_output
        self.warehouse.input_products = self.input_products
        self.warehouse.output_products = self.output_products
        self.warehouse.buffer_input = self.buffer_input
        self.warehouse.buffer_output = self.buffer_output
        self.warehouse.loading_time_input = self.loading_time_input
        self.warehouse.loading_time_output = self.loading_time_output
        self.lineEdit_warehouse_name.setText(self.name)
        self.lineEdit_length.setText(str(self.length))
        self.lineEdit_width.setText(str(self.width))
        self.lineEdit_pos_x.setText(str(self.pos_x))
        self.lineEdit_pos_y.setText(str(self.pos_y))
        self.lineEdit_processing_time.setText(str(self.machine.process_time))

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())


class WidgetDefineInputOutputPosition(QWidget):
    def __init__(self, factory: Factory, warehouse: Warehouse, *args, **kwargs):
        super(WidgetDefineInputOutputPosition, self).__init__()
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        print(f'Inside CLASS WidgetDefineInputOutputPosition - #####################################')
        print(f'Inside CLASS WidgetDefineInputOutputPosition - Warehouse Length = {warehouse.length}')
        print(f'Inside CLASS WidgetDefineInputOutputPosition - Warehouse Input Position = {warehouse.pos_input}')
        print(f'Inside CLASS WidgetDefineInputOutputPosition - Warehouse Output Position = {warehouse.pos_output}')
        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(500, 500)
        self.setMaximumSize(600, 800)
        self.setWindowTitle('ZellFTF - Changing Warehouse - Define Input and Output')
        self.center()

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        # Widgets
        self.warehouseScene = WarehouseScene(self.factory, self.warehouse)
        self.warehouseView = WarehouseView(self.factory, self.warehouse, self.warehouseScene)
        print(f'Inside CLASS WidgetDefineInputOutputPosition - Szene = {self.warehouseScene}')
        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)
        self.button_save_positions = QPushButton('Save positions')

        # Add Widgets to Layout
        self.hLayout1.addStretch(1)
        self.hLayout1.addWidget(self.button_save_positions)

        self.vLayout1.addWidget(self.warehouseView)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)

        # Buttons functions
        self.button_save_positions.clicked.connect(self.save_positions_clicked)

        # Set Layout
        self.setLayout(self.vLayout1)

    def save_positions_clicked(self):
        print(
            f'Saved Positions Clicked - Input Position = {self.warehouse.pos_input}, Output Position = {self.warehouse.pos_output}')
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())


class WidgetDefineInputOutputProducts(QWidget):
    def __init__(self, factory: Factory, warehouse: Warehouse, *args, **kwargs):
        super(WidgetDefineInputOutputProducts, self).__init__()
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        print(f'Inside CLASS WidgetDefineInputProducts - Warehouse Length = {self.warehouse.length}')
        print(f'Inside CLASS WidgetDefineInputProducts - Warehouse Input Position = {self.warehouse.pos_input}')
        print(f'Inside CLASS WidgetDefineInputProducts - Warehouse Output Position = {self.warehouse.pos_output}')
        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(450, 600)
        self.setMaximumSize(500, 600)
        self.setWindowTitle('ZellFTF - Changing warehouse - Define Input and Output')
        self.center()

        self.path_product_types_database = f'data/Current_Factory/Product_Data.csv'
        self.product_types_pd = pd.read_csv(self.path_product_types_database, sep=';', index_col=0)
        self.amount_of_product_types = len(self.product_types_pd.index)

        self.input_product_types = []  # This variable contains all input products of the machine
        self.output_product_types = []  # This variable contains all output products of the machine
        self.temp_buffer_size_input = []  # This variable contains a temporary buffer size for each input product
        self.temp_buffer_size_output = []  # This variable contains a temporary buffer size for each output product
        self.temp_loading_time_input = []  # This variable contains a temporary loading time for each input product
        self.temp_loading_time_output = []  # This variable contains a temporary loading time for each output product

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        # Widgets for vLayout1
        self.label_input = QLabel('<b>Input<b>')
        self.label_input.setStyleSheet('background-color: red; border: 1px solid black')
        self.label_input.setAlignment(Qt.AlignCenter)
        self.label_description_input = QLabel('Chose all products, which are input of the machine:')
        self.table_product_types_input = TableProductTypesWidget(self.factory, self.warehouse,
                                                                 self.path_product_types_database,
                                                                 self.product_types_pd,
                                                                 self.amount_of_product_types, 'input')

        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)

        self.label_output = QLabel('<b>Output<b>')
        self.label_output.setStyleSheet('background-color: lightgreen; border: 1px solid black')
        self.label_output.setAlignment(Qt.AlignCenter)
        self.label_description_output = QLabel('Chose all products, which are output of the machine:')
        self.table_product_types_output = TableProductTypesWidget(self.factory, self.warehouse,
                                                                  self.path_product_types_database,
                                                                  self.product_types_pd,
                                                                  self.amount_of_product_types, 'output')
        self.hLine2 = QFrame(self)
        self.hLine2.setFrameShape(QFrame.HLine)
        self.hLine2.setLineWidth(1)
        self.hLine2.setFrameShadow(QFrame.Sunken)

        self.button_save = QPushButton('Save')
        self.button_check_state = QPushButton('Check State')

        # Add to Layout
        self.vLayout1.addWidget(self.label_input)
        self.vLayout1.addWidget(self.label_description_input)
        self.vLayout1.addWidget(self.table_product_types_input)
        self.vLayout1.addStretch(1)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addStretch(1)
        self.vLayout1.addWidget(self.label_output)
        self.vLayout1.addWidget(self.label_description_output)
        self.vLayout1.addWidget(self.table_product_types_output)
        self.vLayout1.addWidget(self.hLine2)
        self.vLayout1.addWidget(self.button_save)
        self.vLayout1.addWidget(self.button_check_state)

        # Buttons functions
        self.button_check_state.clicked.connect(self.check_state)
        self.button_save.clicked.connect(self.save_clicked)

        # Set Layout
        self.setLayout(self.vLayout1)

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def check_state(self):
        self.table_product_types_input.check_state()
        self.table_product_types_output.check_state()

    def save_clicked(self):
        input_product_types = self.table_product_types_input.check_state()
        output_product_types = self.table_product_types_output.check_state()
        self.input_product_types = input_product_types
        self.output_product_types = output_product_types
        self.warehouse.input_products = input_product_types
        self.warehouse.output_products = output_product_types
        print(
            f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Input Product Types = {self.warehouse.input_products}')
        print(
            f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Output Product Types = {self.warehouse.output_products}')
        if len(self.warehouse.input_products) != 1:
            for i in range(len(self.warehouse.input_products)):
                self.temp_buffer_size_input.append(1)
                self.temp_loading_time_input.append(0)
        if len(self.warehouse.input_products) == 1:
            self.temp_buffer_size_input = [1]
            self.temp_loading_time_input = [0]
        if len(self.warehouse.output_products) != 1:
            for i in range(len(self.warehouse.output_products)):
                self.temp_buffer_size_output.append(1)
                self.temp_loading_time_output.append(0)
        if len(self.warehouse.output_products) == 1:
            self.temp_buffer_size_output = [1]
            self.temp_loading_time_output = [0]
        self.warehouse.buffer_input = self.temp_buffer_size_input
        self.warehouse.buffer_output = self.temp_buffer_size_output
        self.warehouse.loading_time_input = self.temp_loading_time_input
        self.warehouse.loading_time_output = self.temp_loading_time_output
        print(f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Input Buffer = {self.warehouse.buffer_input}')
        print(f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Output Buffer = {self.warehouse.buffer_output}')
        print(
            f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Input Loading Time = {self.warehouse.loading_time_input}')
        print(
            f'Inside CLASS WidgetDefineInputOutputProducts - warehouse Output Loading Time = {self.warehouse.loading_time_output}')
        self.close()


class TableProductTypesWidget(QTableWidget):
    def __init__(self, factory: Factory, warehouse: Warehouse, path_product_types_database, product_types_pd,
                 amount_of_product_types, loading_type):
        super(TableProductTypesWidget, self).__init__()
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        self.setFont(QFont('Arial', 10))

        self.path_product_types_database = path_product_types_database
        self.product_types_pd = product_types_pd
        content = self.product_types_pd.values.tolist()
        self.amount_of_product_types = amount_of_product_types
        self.type = loading_type
        self.setColumnCount(4)
        self.setRowCount(self.amount_of_product_types)
        self.setHorizontalHeaderLabels(['Name', 'Length (mm)', 'Width (mm)', 'Weight (kg)'])

        for i in range(self.amount_of_product_types):
            for j in range(4):
                if j % 4 == 0:
                    item = QTableWidgetItem(str(content[i][j]).format(i, j))
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    if loading_type == 'input' and str(content[i][j]).format(i, j) in self.warehouse.input_products:
                        print(f'Input - {(str(content[i][j]).format(i, j))}')
                        item.setCheckState(Qt.CheckState.Checked)
                    elif loading_type == 'output' and str(content[i][j]).format(i, j) in self.warehouse.output_products:
                        print(f'Output - {(str(content[i][j]).format(i, j))}')
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)
                    self.setItem(i, j, item)
                else:
                    self.setItem(i, j, QTableWidgetItem(str(content[i][j])))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.selectionModel().selectionChanged.connect(self.cell_was_clicked)

    def check_state(self):
        content = self.product_types_pd.values.tolist()
        chosen_product_types = []
        # print(self.amount_of_product_types)
        for row in range(self.amount_of_product_types):
            if self.item(row, 0).checkState() == Qt.CheckState.Checked:
                print(f'Inside CLASS TableProductTypesWidget (Add Machine) - Chosen Products')
                print(content[row][0])
                print(self.factory.product_types[content[row][0]])
                chosen_product_types.append(content[row][0])
                print(chosen_product_types)
        return chosen_product_types

    def table_update(self):
        self.product_types_pd = pd.read_csv(self.path_product_types_database, sep=';', index_col=0)
        self.amount_of_product_types = len(self.product_types_pd.index)
        content = self.product_types_pd.values.tolist()
        self.setColumnCount(4)
        self.setRowCount(self.amount_of_product_types)
        self.setHorizontalHeaderLabels(['Name', 'Length (mm)', 'Width (mm)', 'Weight (kg)'])

        for i in range(self.amount_of_product_types):
            for j in range(4):
                self.setItem(i, j, QTableWidgetItem(str(content[i][j])))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.selectionModel().selectionChanged.connect(self.cell_was_clicked)

    def cell_was_clicked(self):
        row = self.currentItem().row()
        col = self.currentItem().column()
        item = self.horizontalHeaderItem(col).text()
        print(row, col, item)


class WidgetDefineBufferSizeLoadingTime(QWidget):
    def __init__(self, factory: Factory, warehouse: Warehouse, *args, **kwargs):
        super(WidgetDefineBufferSizeLoadingTime, self).__init__()
        self.factory: Factory = factory
        self.warehouse: Warehouse = warehouse
        print(f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Length = {self.warehouse.length}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Input Product Types = {self.warehouse.input_products}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Output Product Types = {self.warehouse.output_products}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Input Loading Time = {self.warehouse.loading_time_input}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Output Loading Time = {self.warehouse.loading_time_output}')
        print(f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Input Buffer = {self.warehouse.buffer_input}')
        print(f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Output Buffer = {self.warehouse.buffer_output}')
        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(200, 100)
        self.setMaximumSize(500, 600)
        self.setWindowTitle('ZellFTF - Adding a machine - Buffer Size and Loading Times')
        self.center()

        self.path_product_types_database = f'data/Current_Factory/Product_Data.csv'
        self.product_types_pd = pd.read_csv(self.path_product_types_database, sep=';', index_col=0)
        self.amount_of_product_types = len(self.product_types_pd.index)

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.gridLayoutInput = QGridLayout()
        self.gridLayoutOutput = QGridLayout()

        # Create Widgets
        self.label_description = QLabel('Define the buffer size and loading time of all chosen products:')
        self.label_input = QLabel('<b>Input<b>')
        self.label_input.setStyleSheet('background-color: red; border: 1px solid black')
        self.label_input.setAlignment(Qt.AlignCenter)
        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)
        self.label_output = QLabel('<b>Output<b>')
        self.label_output.setStyleSheet('background-color: lightgreen; border: 1px solid black')
        self.label_output.setAlignment(Qt.AlignCenter)
        self.hLine2 = QFrame(self)
        self.hLine2.setFrameShape(QFrame.HLine)
        self.hLine2.setLineWidth(1)
        self.hLine2.setFrameShadow(QFrame.Sunken)
        self.button_save = QPushButton('Save')

        self.labels_input = []
        self.lineEdit_buffer_size_input = []
        self.lineEdit_loading_time_input = []
        self.label_input_product = QLabel('<b>Input product<b>')
        self.label_buffer_size_input = QLabel('<b>Buffer size (pcs)<b>')
        self.label_loading_time_input = QLabel('<b>Loading time (s)<b>')
        self.gridLayoutInput.addWidget(self.label_input_product, 0, 0)
        self.gridLayoutInput.addWidget(self.label_buffer_size_input, 0, 1)
        self.gridLayoutInput.addWidget(self.label_loading_time_input, 0, 2)

        for i in range(len(warehouse.input_products)):
            self.labels_input.append(QLabel(str(warehouse.input_products[i])))
            self.lineEdit_buffer_size_input.append(QLineEdit(self))
            self.lineEdit_buffer_size_input[i].setAlignment(Qt.AlignCenter)
            self.lineEdit_buffer_size_input[i].setValidator(QIntValidator())
            self.lineEdit_buffer_size_input[i].setText(str(warehouse.buffer_input[i]))
            self.lineEdit_loading_time_input.append(QLineEdit(self))
            self.lineEdit_loading_time_input[i].setAlignment(Qt.AlignCenter)
            self.lineEdit_loading_time_input[i].setValidator(QIntValidator())
            self.lineEdit_loading_time_input[i].setText(str(warehouse.loading_time_input[i]))
            self.gridLayoutInput.addWidget(self.labels_input[i], i + 1, 0)
            self.gridLayoutInput.addWidget(self.lineEdit_buffer_size_input[i], i + 1, 1)
            self.gridLayoutInput.addWidget(self.lineEdit_loading_time_input[i], i + 1, 2)

        self.labels_output = []
        self.lineEdit_buffer_size_output = []
        self.lineEdit_loading_time_output = []
        self.label_output_product = QLabel('<b>Output product<b>')
        self.label_buffer_size_output = QLabel('<b>Buffer size (pcs)<b>')
        self.label_loading_time_output = QLabel('<b>Loading time (s)<b>')
        self.gridLayoutOutput.addWidget(self.label_output_product, 0, 0)
        self.gridLayoutOutput.addWidget(self.label_buffer_size_output, 0, 1)
        self.gridLayoutOutput.addWidget(self.label_loading_time_output, 0, 2)

        for i in range(len(warehouse.output_products)):
            self.labels_output.append(QLabel(str(warehouse.output_products[i])))
            self.lineEdit_buffer_size_output.append(QLineEdit(self))
            self.lineEdit_buffer_size_output[i].setAlignment(Qt.AlignCenter)
            self.lineEdit_buffer_size_output[i].setValidator(QIntValidator())
            self.lineEdit_buffer_size_output[i].setText(str(warehouse.buffer_output[i]))
            self.lineEdit_loading_time_output.append(QLineEdit(self))
            self.lineEdit_loading_time_output[i].setAlignment(Qt.AlignCenter)
            self.lineEdit_loading_time_output[i].setValidator(QIntValidator())
            self.lineEdit_loading_time_output[i].setText(str(warehouse.loading_time_output[i]))
            self.gridLayoutOutput.addWidget(self.labels_output[i], i + 1, 0)
            self.gridLayoutOutput.addWidget(self.lineEdit_buffer_size_output[i], i + 1, 1)
            self.gridLayoutOutput.addWidget(self.lineEdit_loading_time_output[i], i + 1, 2)

        # QPushButtons Funcktionen
        self.button_save.clicked.connect(self.button_saved_clicked)

        # Add to Layout
        self.vLayout1.addWidget(self.label_description)
        self.vLayout1.addWidget(self.label_input)
        self.vLayout1.addLayout(self.gridLayoutInput)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addWidget(self.label_output)
        self.vLayout1.addLayout(self.gridLayoutOutput)
        self.vLayout1.addWidget(self.hLine2)
        self.vLayout1.addWidget(self.button_save)
        self.vLayout1.addStretch(1)

        # Set Layout
        self.setLayout(self.vLayout1)

    def button_saved_clicked(self):
        for i in range(len(self.warehouse.input_products)):
            self.warehouse.buffer_input[i] = int(self.lineEdit_buffer_size_input[i].text())
            self.warehouse.loading_time_input[i] = int(self.lineEdit_loading_time_input[i].text())
        for i in range(len(self.warehouse.output_products)):
            self.warehouse.buffer_output[i] = int(self.lineEdit_buffer_size_output[i].text())
            self.warehouse.loading_time_output[i] = int(self.lineEdit_loading_time_output[i].text())
        print(f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Input Buffer = {self.warehouse.buffer_input}')
        print(f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Output Buffer = {self.warehouse.buffer_output}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Input Loading Time = {self.warehouse.loading_time_input}')
        print(
            f'Inside CLASS WidgetDefineBufferSizeLoadingTime - warehouse Output Loading Time = {self.warehouse.loading_time_output}')
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())