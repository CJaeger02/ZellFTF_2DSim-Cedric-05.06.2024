# general packages
import os
import numpy as np
import shutil
from datetime import datetime

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# own packages
from FactoryObjects.Factory import Factory
from GUI.DialogNewFactory import DialogNewFactory, DialogOverwriteDefaultFactory
from GUI.DialogSaveFactory import DialogSaveFactory
from GUI.DialogLoadFactory import DialogLoadFactory
from GUI.WidgetLoadFactory import WidgetLoadFactory
from GUI.WidgetDefineProducts import WidgetDefineProductTypes
from GUI.WidgetAddMachine import WidgetAddMachine
from GUI.WidgetAddWarehouse import WidgetAddWarehouse
from GUI.WidgetAddLoadingStation import WidgetAddLoadingStation
from GUI.FactoryScene import FactoryScene
from GUI.WidgetListOfFactoryObjects import WidgetListOfFactoryObjects
from VRP_Modelle.VRP import VRP_cellAGV


# from SimpleLoopTest import LoopTest

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


class WidgetFabricLayout(QWidget):
    def __init__(self, factory: Factory, factoryScene: FactoryScene, vrp_cell_AGV: VRP_cellAGV, *args, **kwargs):
        super(WidgetFabricLayout, self).__init__(parent=None)
        self.factory: Factory = factory
        self.factoryScene: FactoryScene = factoryScene
        self.vrp_cellAGV: VRP_cellAGV = vrp_cell_AGV
        # self.factoryScene.draw_factory_grid(self.factory)
        self.path_factory_database = 'data/Current_Factory/Factory_Data.csv'
        self.setFont(QFont('Arial', 10))

        # Create Layout
        self.hLayout1 = QHBoxLayout()  # Layout for Buttons "New factory", "Load factory", "Save factory"
        self.gridLayout1 = QGridLayout()  # Layout for buttons "Add machine", "Add warehouse", "Add Way", "Add Loading Station"
        self.vLayout1 = QVBoxLayout()  # Main Layout
        self.hLayout2 = QHBoxLayout()  # Layout for Calculate Buttons

        # Create widgets
        self.button_new_factory = QPushButton('New Factory')
        self.button_load_factory = QPushButton('Load Factory')
        self.button_save_factory = QPushButton('Save Factory')
        self.hLine2 = QFrame(self)
        self.hLine2.setFrameShape(QFrame.HLine)
        self.hLine2.setLineWidth(1)
        self.hLine2.setFrameShadow(QFrame.Sunken)
        self.label_description = QLabel('<b>Information about the factory:<b>')
        self.label_factory_name = QLabel('Factory name:')
        self.lineEdit_factory_name = QLineEdit(self)
        self.lineEdit_factory_name.setText(str(self.factory.name))
        self.lineEdit_factory_name.setAlignment(Qt.AlignCenter)
        self.lineEdit_factory_name.setEnabled(False)
        self.label_factory_length = QLabel('Length of the factory in meter:')
        self.lineEdit_factory_length = QLineEdit(self)
        self.lineEdit_factory_length.setValidator(QIntValidator())
        self.lineEdit_factory_length.setMaxLength(3)
        self.lineEdit_factory_length.setText(str(self.factory.length))
        self.lineEdit_factory_length.setAlignment(Qt.AlignCenter)
        self.lineEdit_factory_length.setEnabled(False)
        self.label_factory_width = QLabel('Width of the factory in meter:')
        self.lineEdit_factory_width = QLineEdit(self)
        self.lineEdit_factory_width.setValidator(QIntValidator())
        self.lineEdit_factory_width.setText(str(self.factory.width))
        self.lineEdit_factory_width.setAlignment(Qt.AlignCenter)
        self.lineEdit_factory_width.setEnabled(False)
        self.label_factory_resolution = QLabel('Resolution of the factory in meter:')
        self.doubleSpinBox_factory_resolution = QDoubleSpinBox(self)
        self.doubleSpinBox_factory_resolution.setRange(0.5, 5.0)
        self.doubleSpinBox_factory_resolution.setSingleStep(0.5)
        self.doubleSpinBox_factory_resolution.setValue(float((self.factory.cell_size)))
        self.doubleSpinBox_factory_resolution.setAlignment(Qt.AlignCenter)
        self.doubleSpinBox_factory_resolution.setDecimals(1)
        self.doubleSpinBox_factory_resolution.setEnabled(False)
        self.doubleSpinBox_factory_resolution.setToolTip('The value for the resolution is fixed.')
        self.button_apply = QPushButton('Apply')
        self.button_apply.setEnabled(False)
        self.button_cancel_new_factory = QPushButton('Cancel')
        self.button_cancel_new_factory.setEnabled(False)
        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)

        self.sidebar = WidgetListOfFactoryObjects(self.factory, self.factoryScene)

        self.hLine3 = QFrame(self)
        self.hLine3.setFrameShape(QFrame.HLine)
        self.hLine3.setLineWidth(1)
        self.hLine3.setFrameShadow(QFrame.Sunken)
        self.button_add_machine = QPushButton('Add Machine')
        self.button_add_warehouse = QPushButton('Add Warehouse')
        self.button_add_way = QPushButton('Add Path')
        self.button_add_way.setEnabled(False)
        self.button_add_loading_station = QPushButton('Add Loading Station')
        self.button_define_products = QPushButton('Define Products')
        self.hLine4 = QFrame(self)
        self.hLine4.setFrameShape(QFrame.HLine)
        self.hLine4.setLineWidth(1)
        self.hLine4.setFrameShadow(QFrame.Sunken)

        self.button_calculate_distance_matrix = QPushButton('Calculate Distance Matrix')
        self.button_calculate_distance_matrix.setToolTip('The distances between the individual locations are '
                                                         'calculated using the locations of the machines, warehouses '
                                                         'and charging stations. The Manhattan metric is used as the '
                                                         'distance. The data is stored in a matrix.')
        self.button_calculate_transport_routes = QPushButton('Calculate Transport Routes')
        self.button_calculate_transport_routes.setToolTip('The transport routes are calculated using the assigned '
                                                          'products. The data for the transportation routes represent '
                                                          'a directed graph')

        # QPushButtons - functions
        self.button_new_factory.clicked.connect(self.new_factory_clicked)
        self.button_load_factory.clicked.connect(self.load_factory_clicked)
        self.button_save_factory.clicked.connect(self.save_factory_clicked)
        self.button_apply.clicked.connect(self.apply_clicked)
        self.button_cancel_new_factory.clicked.connect(self.cancel_new_factory_clicked)
        self.button_add_machine.clicked.connect(self.add_machine_clicked)
        self.button_add_warehouse.clicked.connect(self.add_warehouse_clicked)
        # self.button_add_way.clicked.connect(self.add_way_clicked)
        self.button_add_loading_station.clicked.connect(self.add_loading_station_clicked)
        self.button_define_products.clicked.connect(self.define_products_clicked)

        # Add buttons to hLayout1
        self.hLayout1.addWidget(self.button_new_factory)
        self.hLayout1.addWidget(self.button_load_factory)
        self.hLayout1.addWidget(self.button_save_factory)

        # Add buttons to gridLayout1
        self.gridLayout1.addWidget(self.button_add_machine, 0, 0)
        self.gridLayout1.addWidget(self.button_add_warehouse, 0, 1)
        self.gridLayout1.addWidget(self.button_add_way, 1, 0)
        self.gridLayout1.addWidget(self.button_add_loading_station, 1, 1)

        # Add buttons to hLayout2
        self.hLayout2.addWidget(self.button_calculate_distance_matrix)
        self.hLayout2.addWidget(self.button_calculate_transport_routes)

        # Add labels and buttons to vLayout1
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.hLine2)
        self.vLayout1.addWidget(self.label_description)
        self.vLayout1.addWidget(self.label_factory_name)
        self.vLayout1.addWidget(self.lineEdit_factory_name)
        self.vLayout1.addWidget(self.label_factory_length)
        self.vLayout1.addWidget(self.lineEdit_factory_length)
        self.vLayout1.addWidget(self.label_factory_width)
        self.vLayout1.addWidget(self.lineEdit_factory_width)
        self.vLayout1.addWidget(self.label_factory_resolution)
        self.vLayout1.addWidget(self.doubleSpinBox_factory_resolution)
        self.vLayout1.addWidget(self.button_apply)
        self.vLayout1.addWidget(self.button_cancel_new_factory)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.button_define_products)
        self.vLayout1.addWidget(self.hLine3)
        self.vLayout1.addWidget(self.sidebar)
        self.vLayout1.addWidget(self.hLine4)
        self.vLayout1.addLayout(self.hLayout2)
        self.vLayout1.addStretch(50)

        # Set Layout
        self.setLayout(self.vLayout1)

    def new_factory_clicked(self):
        self.dialog_new_factory = DialogNewFactory()
        if self.dialog_new_factory.exec():
            print('yay!')
            self.create_folders()
            # disabling and enabling buttons
            self.button_new_factory.setEnabled(False)
            self.button_load_factory.setEnabled(False)
            self.button_save_factory.setEnabled(False)
            self.button_add_machine.setEnabled(False)
            self.button_add_warehouse.setEnabled(False)
            self.button_add_way.setEnabled(False)
            self.button_add_loading_station.setEnabled(False)
            self.button_define_products.setEnabled(False)
            self.lineEdit_factory_name.setEnabled(True)
            self.lineEdit_factory_length.setEnabled(True)
            self.lineEdit_factory_width.setEnabled(True)
            self.button_apply.setEnabled(True)
            self.button_cancel_new_factory.setEnabled(True)
        else:
            print('Definitely not!')
            return

    def load_factory_clicked(self):
        """
        The function opens a dialog to open a saved factory to restore it from the CSV files.
        :return: None
        """
        self.dialog_load_factory = DialogLoadFactory()
        if self.dialog_load_factory.exec():
            self.widget_load_factory = WidgetLoadFactory(self.factory, self.factoryScene, self.sidebar)
            self.widget_load_factory.show()
        else:
            return

    def save_factory_clicked(self):
        """
        This function saves the current factory in a folder with the factory name with all necessary data.
        :return: None
        """
        if (self.lineEdit_factory_name.text() == 'default_factory'
                or self.lineEdit_factory_name.text() == 'test_factory'):
            # The default_factory and the test_factory cannot be overwritten
            print('It is not possible to overwrite the default/test factory!')
            self.dialog_overwrite_default_factory = DialogOverwriteDefaultFactory()
            self.dialog_overwrite_default_factory.exec()
        else:
            # This else-loop saves the factory data
            self.dialog_save_factory = DialogSaveFactory()
            if self.dialog_save_factory.exec():
                print(f'Gespeicherte Fabrik - Name: {self.factory.name}')
                print(f'Gespeicherte Fabrik - Länge: {self.factory.length}')
                print(f'Gespeicherte Fabrik - Breite: {self.factory.width}')
                print(f'Gespeicherte Fabrik - Res: {self.factory.cell_size}')
                # Creates the path, where the data is saved
                if not os.path.exists(f'data/Saved_Factories/{self.factory.name}'):
                    os.makedirs(f'data/Saved_Factories/{self.factory.name}')
                if not os.path.exists(f'data/Saved_Factories/{self.factory.name}/config'):
                    os.makedirs(f'data/Saved_Factories/{self.factory.name}/config')

                # Copy the csv-files from the current factory to the saved factory path
                shutil.copyfile(f'data/Current_Factory/Warehouse_Data.csv',
                                'data/Saved_Factories/{}/Warehouse_Data.csv'
                                .format(self.factory.name))
                shutil.copyfile(f'data/Current_Factory/Machine_Data.csv',
                                'data/Saved_Factories/{}/Machine_Data.csv'
                                .format(self.factory.name))
                shutil.copyfile(f'data/Current_Factory/Loading_Station_Data.csv',
                                'data/Saved_Factories/{}/Loading_Station_Data.csv'
                                .format(self.factory.name))
                shutil.copyfile(f'data/Current_Factory/Product_Data.csv',
                                'data/Saved_Factories/{}/Product_Data.csv'
                                .format(self.factory.name))
                shutil.copyfile(f'data/Current_Factory/Factory_Data.csv',
                                'data/Saved_Factories/{}/Factory_Data.csv'
                                .format(self.factory.name))

                self.factory.save_factory()  # Function to save the data from the layout and calculated data.
                dlg = QMessageBox(self)
                dlg.setText("Factory saved!")
                dlg.exec()
                print('FACTORY SAVED!')

            else:
                print('NOT SAVED!')

    def apply_clicked(self):
        if self.lineEdit_factory_name.text() == 'default_factory':
            print('It is not possible to overwrite the default/test factory!')
            self.dialog_overwrite_default_factory = DialogOverwriteDefaultFactory()
            self.dialog_overwrite_default_factory.exec()
        else:
            # Disabling and enabling buttons
            self.button_new_factory.setEnabled(True)
            self.button_load_factory.setEnabled(True)
            self.button_save_factory.setEnabled(True)
            self.button_add_machine.setEnabled(True)
            self.button_add_warehouse.setEnabled(True)
            self.button_add_way.setEnabled(True)
            self.button_add_loading_station.setEnabled(True)
            self.button_define_products.setEnabled(True)
            self.lineEdit_factory_name.setEnabled(False)
            self.lineEdit_factory_length.setEnabled(False)
            self.lineEdit_factory_width.setEnabled(False)
            self.button_apply.setEnabled(False)
            self.button_cancel_new_factory.setEnabled(False)

            # Deleting the old factory layout
            self.factoryScene.delete_factory_grid()
            print(f"Old name: {self.factory.name}")
            print(f"Old length: {self.factory.length}")
            print(f"Old width: {self.factory.width}")
            print(f"Old res: {self.factory.cell_size}")

            # Setting new factory layout
            self.factory.name = str(self.lineEdit_factory_name.text())
            self.factory.length = int(self.lineEdit_factory_length.text())
            self.factory.width = int(self.lineEdit_factory_width.text())
            self.factory.cell_size = float(self.doubleSpinBox_factory_resolution.text().replace(',', "."))
            self.factory.no_columns = int(self.factory.length // self.factory.cell_size)
            self.factory.no_rows = int(self.factory.width // self.factory.cell_size)
            self.factory.np_factory_grid_layout = np.zeros(
                shape=(self.factory.no_columns, self.factory.no_rows))  # in this matrix all the data of
            self.factory.factory_grid_layout = self.factory.np_factory_grid_layout.tolist()
            print(f"New name: {self.factory.name}")
            print(f"New length: {self.factory.length}")
            print(f"New width: {self.factory.width}")
            print(f"New res: {self.factory.cell_size}")
            self.factoryScene.draw_factory_grid()

            # Creating Path for factory
            if not os.path.exists(f'data/Saved_Factories/{self.factory.name}'):
                os.makedirs(f'data/Saved_Factories/{self.factory.name}')

            # Saving the factory data in a csv-file:
            self.add_to_csv()

    def add_to_csv(self):
        current_factory_database = open(f'data/Current_Factory/Factory_Data.csv', 'w')
        current_factory_database.write(f';Name;Length;Width;Cell_Size\n'
                                       f'0;{self.factory.name};{self.factory.length};'
                                       f'{self.factory.width};{self.factory.cell_size}')
        current_factory_database.close()


    def cancel_new_factory_clicked(self):
        # TODO: wieder alte Informationen der Fabrik einblenden!
        self.button_new_factory.setEnabled(True)
        self.button_load_factory.setEnabled(True)
        self.button_save_factory.setEnabled(True)
        self.button_add_machine.setEnabled(True)
        self.button_add_warehouse.setEnabled(True)
        self.button_add_way.setEnabled(True)
        self.button_add_loading_station.setEnabled(True)
        self.button_define_products.setEnabled(True)
        self.lineEdit_factory_name.setEnabled(False)
        self.lineEdit_factory_length.setEnabled(False)
        self.lineEdit_factory_width.setEnabled(False)
        self.button_apply.setEnabled(False)
        self.button_cancel_new_factory.setEnabled(False)

    def add_machine_clicked(self):
        self.widget_add_machine = WidgetAddMachine(self.factory, self.factoryScene, self.sidebar)
        self.widget_add_machine.show()

    def add_warehouse_clicked(self):
        self.widget_add_warehouse = WidgetAddWarehouse(self.factory, self.factoryScene, self.sidebar)
        self.widget_add_warehouse.show()

    def add_way_clicked(self):
        pass

    def add_loading_station_clicked(self):
        self.widget_add_loading_station = WidgetAddLoadingStation(self.factory, self.factoryScene, self.sidebar)
        self.widget_add_loading_station.show()
        pass

    def define_products_clicked(self):
        self.widget_define_products = WidgetDefineProductTypes(self.factory)
        self.widget_define_products.show()

    def calculate_distance_matrix_clicked(self):
        pass

    def create_folders(self):
        # if not os.path.isfile(f'data/Current_Factory/Product_Data.csv'):
        print('Creating Path Product Types...')
        current_product_types_database = open(f'data/Current_Factory/Product_Data.csv', 'w')
        current_product_types_database.write(';Name;Length;Width;Weight\n'
                                             '0;default_product_1;500;500;25.0\n'
                                             '1;default_product_2;1000;1000;100.0\n'
                                             '2;default_product_3;1500;1500;150.0\n'
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
        print('Creating Path Loading Stations...')
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
