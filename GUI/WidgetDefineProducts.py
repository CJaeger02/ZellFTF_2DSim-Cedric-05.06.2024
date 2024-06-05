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

# own packages
from FactoryObjects.Factory import Factory


########################################################################################################################

# The WidgetAddMachine-Class (inheritance QWidget) is a Sub_QWidget for the WidgetFabricLayout.
# A new window will be opened to create a new machine for the current factory.
# In this window all necessary data about the machine are entered.

########################################################################################################################

class WidgetDefineProductTypes(QWidget):
    def __init__(self, factory: Factory):
        super(WidgetDefineProductTypes, self).__init__()
        self.factory: Factory = factory
        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        if not os.path.isfile(f'data/Saved_Factories/{self.factory.name}/Product_Data.csv'):
            print('Creating Path...')
            self.product_types_database = open(f'data/Saved_Factories/{self.factory.name}/Product_Data.csv', 'w')
            self.product_types_database.write(';Name;Length;Width;Weight\n'
                                              '0;default_product_1;500;500;25.0\n'
                                              '1;default_product_2;1000;1000;100.0\n'
                                              '2;default_product_3;1500;1500;150.0\n'
                                              '3;default_product_4;500;1000;50.0')
            self.product_types_database.close()

        if not os.path.exists(f'data/Saved_Factories/{self.factory.name}/Archiv/Product_Data'):
            os.makedirs(f'data/Saved_Factories/{self.factory.name}/Archiv/Product_Data')

        self.resize(440, 400)
        self.setMaximumSize(440, 800)
        self.setWindowTitle('ZellFTF - Define Products')
        self.center()

        # self.path_product_types_database = f'data/Saved_Factories/{self.factory.name}/Product_Data.csv'
        self.path_product_types_database = f'data/Current_Factory/Product_Data.csv'
        self.product_types_pd = pd.read_csv(self.path_product_types_database, sep=';', index_col=0)
        self.amount_of_product_types = len(self.product_types_pd.index)

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.hLayout1 = QHBoxLayout()

        # Widgets for Layouts
        self.label_description = QLabel('The following products can be used in the factory:')
        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)
        self.table_product_types = TableProductTypesWidget(self.factory, self.path_product_types_database,
                                                           self.product_types_pd,
                                                           self.amount_of_product_types)
        self.button_add_product = QPushButton('Add product...')
        self.button_delete_product = QPushButton('Delete selected product')
        self.button_close = QPushButton('Close')
        self.button_update = QPushButton('Update')

        # Functions
        self.button_add_product.clicked.connect(lambda: self.add_product_clicked(self.factory))
        self.button_delete_product.clicked.connect(lambda: self.delete_product_clicked(self.factory))
        self.button_close.clicked.connect(self.close)
        self.button_update.clicked.connect(self.update_table)

        # Adding to Layout
        self.hLayout1.addStretch(1)
        self.hLayout1.addWidget(self.button_update)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_description)
        self.vLayout1.addWidget(self.table_product_types)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addWidget(self.button_add_product)
        self.vLayout1.addWidget(self.button_delete_product)
        self.vLayout1.addWidget(self.button_close)
        self.setLayout(self.vLayout1)

    def add_product_clicked(self, factory: Factory):
        self.widget_add_product = WidgetAddProduct(factory, self.path_product_types_database, self.product_types_pd,
                                                   self.amount_of_product_types)
        self.widget_add_product.window_closed.connect(self.update_widget)
        self.widget_add_product.show()

    def delete_product_clicked(self, factory: Factory):
        if (self.table_product_types.cell_was_clicked() == '0' or self.table_product_types.cell_was_clicked() == '1' or
                self.table_product_types.cell_was_clicked() == '2' or
                self.table_product_types.cell_was_clicked() == '3'):
            print('Default products cannot be deleted!')
            self.dialog_delete = DialogDeleteDefaultProduct()
            self.dialog_delete.exec()
        else:
            self.dialog_delete = DialogDeleteProduct()
            row = self.table_product_types.cell_was_clicked()
            if self.dialog_delete.exec():
                self.delete_product(factory, row)
                self.update_widget()
            else:
                print('Definitely not!')

    def delete_product(self, factory: Factory, row):
        shutil.copyfile(f'data/Current_Factory/Product_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Product_Data/{}_Product_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        self.amount_of_product_types = len(self.product_types_pd.index)
        product_types_np = self.product_types_pd.to_numpy()
        product_types_list = self.product_types_pd.values.tolist()
        if int(row) > self.amount_of_product_types:
            # print('Deleting not possbile!')
            return None
        else:
            # print(product_types_np)
            # print(product_types_list)
            # print(product_types_list[int(row)])
            # print(product_types_list[int(row)][0])
            chosen_product_type = product_types_list[int(row)][0]
            # print(factory.product_types[chosen_product_type])
            factory.product_types.pop(chosen_product_type)
            product_types_np = np.delete(product_types_np, (int(row)), 0)
            self.product_types_pd = pd.DataFrame(product_types_np, columns=['Name', 'Length', 'Width', 'Weight'])
            product_types_list = self.product_types_pd.values.tolist()
            self.product_types_pd = pd.DataFrame(product_types_list)
            self.product_types_pd.columns = ['Name', 'Length', 'Width', 'Weight']
            self.product_types_pd.to_csv(self.path_product_types_database, sep=';')
            print(factory.product_types)
            print(self.product_types_pd)

    def update_widget(self):
        self.table_product_types.table_update()
        self.path_product_types_database = f'data/Current_Factory/Product_Data.csv'
        self.product_types_pd = pd.read_csv(self.path_product_types_database, sep=';', index_col=0)
        self.amount_of_product_types = len(self.product_types_pd.index)

    def update_table(self):
        self.product_types_pd = pd.DataFrame(self.dict_to_list())
        self.product_types_pd.columns = ['Name', 'Length (mm)', 'Width (mm)', 'Weight (kg)']
        self.product_types_pd.to_csv(self.path_product_types_database, sep=';')
        self.update_widget()

    def dict_to_list(self):
        product_types_list = []
        for key, value in self.factory.product_types.items():
            product_types_list.append([key, value['length'], value['width'], value['weight']])
            print(key)
            print(value)
        print(product_types_list)
        return product_types_list

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())


class TableProductTypesWidget(QTableWidget):
    def __init__(self, factory: Factory, path_product_types_database, product_types_pd, amount_of_product_types):
        super(TableProductTypesWidget, self).__init__()
        self.factory: Factory = factory
        self.setFont(QFont('Arial', 10))

        self.path_product_types_database = path_product_types_database
        self.product_types_pd = product_types_pd
        content = self.product_types_pd.values.tolist()
        self.amount_of_product_types = amount_of_product_types
        self.setColumnCount(4)
        self.setRowCount(self.amount_of_product_types)
        self.setHorizontalHeaderLabels(['Name', 'Length (mm)', 'Width (mm)', 'Weight (kg)'])

        for i in range(self.amount_of_product_types):
            for j in range(4):
                self.setItem(i, j, QTableWidgetItem(str(content[i][j])))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.selectionModel().selectionChanged.connect(self.cell_was_clicked)

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
        return str(row)


class WidgetAddProduct(QWidget):
    window_closed = Signal()

    def __init__(self, factory: Factory, path_product_types_database, product_types_pd, amount_of_product_types):
        super(WidgetAddProduct, self).__init__()
        self.factory: Factory = factory
        self.setFont(QFont('Arial', 10))
        self.setWindowModality(Qt.ApplicationModal)

        self.resize(300, 100)
        self.setMaximumSize(300, 100)
        self.setWindowTitle('ZellFTF - Define Products')
        self.center()

        self.path_product_types_database = path_product_types_database
        self.product_types_pd = product_types_pd
        # content = self.product_types_pd.values.tolist()
        self.amount_of_product_types = amount_of_product_types

        # print(f'{self.factory.name}')
        print(self.factory.product_types)
        print(self.factory.product_types['default_product_1'])

        # Create Layout
        self.vLayout1 = QVBoxLayout()
        self.gridLayout1 = QGridLayout()
        self.hLayout1 = QHBoxLayout()

        # Widgets

        self.label_note = QLabel('Enter the product properties:')

        self.label_product_name = QLabel('Name of the product:')
        self.lineEdit_product_name = QLineEdit(self)
        self.lineEdit_product_name.setAlignment(Qt.AlignCenter)
        self.label_length = QLabel('Length of product (mm):')
        self.lineEdit_length = QLineEdit(self)
        self.lineEdit_length.setAlignment(Qt.AlignCenter)
        self.lineEdit_length.setValidator(QIntValidator())
        self.label_width = QLabel('Width of product (mm):')
        self.lineEdit_width = QLineEdit(self)
        self.lineEdit_width.setAlignment(Qt.AlignCenter)
        self.lineEdit_width.setValidator(QIntValidator())
        self.label_weight = QLabel('Weight of product (kg):')
        self.lineEdit_weight = QLineEdit(self)
        self.lineEdit_weight.setAlignment(Qt.AlignCenter)
        self.lineEdit_weight.setValidator(QIntValidator())

        self.hLine1 = QFrame(self)
        self.hLine1.setFrameShape(QFrame.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setFrameShadow(QFrame.Sunken)
        self.button_add_product = QPushButton('Add product')
        self.button_cancel = QPushButton('Cancel')
        self.label_user_info = QLabel('Waiting for action...')
        self.label_user_info.setAlignment(Qt.AlignCenter)

        # Functions
        self.button_add_product.clicked.connect(self.add_product_clicked)
        self.button_cancel.clicked.connect(self.cancel_clicked)

        # Add to Layout
        self.gridLayout1.addWidget(self.label_product_name, 1, 0)
        self.gridLayout1.addWidget(self.lineEdit_product_name, 1, 1)
        self.gridLayout1.addWidget(self.label_length, 2, 0)
        self.gridLayout1.addWidget(self.lineEdit_length, 2, 1)
        self.gridLayout1.addWidget(self.label_width, 3, 0)
        self.gridLayout1.addWidget(self.lineEdit_width, 3, 1)
        self.gridLayout1.addWidget(self.label_weight, 4, 0)
        self.gridLayout1.addWidget(self.lineEdit_weight, 4, 1)

        self.hLayout1.addWidget(self.button_add_product)
        self.hLayout1.addWidget(self.button_cancel)

        self.vLayout1.addWidget(self.label_note)
        self.vLayout1.addLayout(self.gridLayout1)
        self.vLayout1.addWidget(self.hLine1)
        self.vLayout1.addLayout(self.hLayout1)
        self.vLayout1.addWidget(self.label_user_info)

        self.setLayout(self.vLayout1)

    def add_product_clicked(self):
        if (self.lineEdit_product_name.text() == '' or self.lineEdit_length.text() == ''
                or self.lineEdit_width.text() == '' or self.lineEdit_weight == ''):
            self.label_user_info.setText('<font color=red>Please enter correct product data...</font>')
        elif (self.lineEdit_product_name.text() == 'default_product_1' or
              self.lineEdit_product_name.text() == 'default_product_2' or
              self.lineEdit_product_name.text() == 'default_product_3' or
              self.lineEdit_product_name.text() == 'default_product_4'):
            self.label_user_info.setText('<font color=red>Default products cannot be overwritten...</font>')
        else:
            self.product_type.name = str(self.lineEdit_product_name.text())
            self.product_type.length = str(self.lineEdit_length.text())
            self.product_type.width = str(self.lineEdit_width.text())
            self.product_type.weight = str(self.lineEdit_weight.text())
            self.factory.add_product_types(self.product_type.create_list())
            self.add_to_csv()
            self.label_user_info.setText('Window closes automatically')
            self.update()
            self.close()
            # self.lineEdit_product_id.setText(str(
            #     self.product_types_pd.iloc[self.amount_of_product_types - 1]['ID'] + 1))

    def dict_to_list(self):
        product_types_list = []
        for key, value in self.factory.product_types.items():
            product_types_list.append([key, value['length'], value['width'], value['weight']])
            print(key)
            print(value)
        print(product_types_list)
        return product_types_list

    def cancel_clicked(self):
        self.close()

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def add_to_csv(self):
        shutil.copyfile(f'data/Current_Factory/Product_Data.csv',
                        'data/Saved_Factories/{}/Archiv/Product_Data/{}_Product_Data.csv'
                        .format(self.factory.name, datetime.now().strftime('%Y%m%d-%H%A%S')))
        name = str(self.lineEdit_product_name.text())
        length = int(self.lineEdit_length.text())
        width = int(self.lineEdit_width.text())
        weight = float(self.lineEdit_weight.text())
        self.factory.product_types[name] = dict(length=length, width=width, weight=weight)
        print(f'Product Types = {self.factory.product_types}')
        self.product_types_pd = pd.DataFrame(self.dict_to_list())
        self.product_types_pd.columns = ['Name', 'Length (mm)', 'Width (mm)', 'Weight (kg)']
        self.product_types_pd.to_csv(self.path_product_types_database, sep=';')

    def closeEvent(self, event):
        self.window_closed.emit()
        # print('WINDOW CLOSED')
        event.accept()


class DialogDeleteProduct(QDialog):
    def __init__(self):
        super(DialogDeleteProduct, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')

        print('opened!')

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        message = QLabel('Do you really want to delete the selected product?')
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)


class DialogDeleteDefaultProduct(QDialog):
    def __init__(self):
        super(DialogDeleteDefaultProduct, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        message = QLabel('It is not possible to delete default products!')
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)
