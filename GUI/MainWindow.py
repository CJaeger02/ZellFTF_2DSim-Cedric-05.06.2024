# system packages
import sys
import os

# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# own GUI packages
from GUI.WidgetMainWindow import WidgetMainWindow


########################################################################################################################

# The MainWindow-Class (inheritance QMainWindow) is the main window for the GUI and contains the necessary widgets
# to display the elements GUI
# These are...
#       ...the Central Widget
#       ...a menubar
#       ...a statusbar

########################################################################################################################

class MainWindow(QMainWindow):
    # init MainWindow
    def __init__(self, app):
        super(MainWindow, self).__init__()

        working_directory = os.getcwd()
        if working_directory[-3:] == "GUI":
            os.chdir("..")

        self.mainWidget = WidgetMainWindow(app, self)
        self.setCentralWidget(self.mainWidget)

        self.setWindowTitle('ZellFTF - 2D Simulator')
        self.setMinimumSize(1920, 1000)
        self.menubar()
        self.statusbar()
        # self.showMaximized()

        if not os.path.exists('test'):
            os.makedirs('test')

        self.setMouseTracking(True)

    def menubar(self):
        # create menubar
        menubar = self.menuBar()

        # create menu 'File'
        self.button_fileNewLayout = QAction('&Create New Factory', self)
        self.button_fileNewLayout.setShortcut('Ctrl+N')
        self.button_fileLoadLayout = QAction('&Load Factory', self)
        self.button_fileLoadLayout.setShortcut('Ctrl+L')
        self.button_fileSaveLayout = QAction('&Save Factory', self)
        self.button_fileSaveLayout.setShortcut('Ctrl+S')
        self.button_fileExit = QAction('&Exit', self)
        self.button_fileExit.setShortcut('Ctrl+Q')
        self.button_fileExit.triggered.connect(self.close)

        self.file = menubar.addMenu('&File')
        self.file.addAction(self.button_fileNewLayout)
        self.file.addAction(self.button_fileLoadLayout)
        self.file.addAction(self.button_fileSaveLayout)
        self.file.addSeparator()
        self.file.addAction(self.button_fileExit)

        # create menu 'Factory Data'
        self.button_factoryData_Machine_Overview = QAction('Machine Data', self)
        self.button_factoryData_Warehouse_Overview = QAction('Warehouse Data', self)
        self.button_factoryData_Loading_Station_Overview = QAction('Loading Station Data', self)
        self.button_factoryData_Product_Types_Overview = QAction('Product Types Data', self)
        self.button_factoryData_Transportrelationships = QAction('Transportrelationships', self)

        self.factoryData = menubar.addMenu('&Factory Data')
        self.factoryData.addAction(self.button_factoryData_Machine_Overview)
        self.factoryData.addAction(self.button_factoryData_Warehouse_Overview)
        self.factoryData.addAction(self.button_factoryData_Loading_Station_Overview)
        self.factoryData.addSeparator()
        self.factoryData.addAction(self.button_factoryData_Product_Types_Overview)
        self.factoryData.addSeparator()
        self.factoryData.addAction(self.button_factoryData_Transportrelationships)

        # create menu 'Views'
        self.button_viewStandard = QAction('Standard View', self)
        self.button_viewTransportRelationships = QAction('Transport relationships', self)
        self.button_viewTransportRelationships.triggered.connect(self.button_views_transport_relationships_clicked)
        self.button_viewStandard.triggered.connect(self.button_views_standard_clicked)

        self.views = menubar.addMenu('&Views')
        self.views.addAction(self.button_viewStandard)
        self.views.addSeparator()
        self.views.addAction(self.button_viewTransportRelationships)

    def button_views_transport_relationships_clicked(self):
        self.centralWidget().factoryScene.draw_transport_routes()
        self.button_viewTransportRelationships.setEnabled(False)
        self.button_viewStandard.setEnabled(True)

    def button_views_standard_clicked(self):
        self.centralWidget().factoryScene.delete_transport_routes()
        self.button_viewTransportRelationships.setEnabled(True)

    def statusbar(self):
        statusbar = self.statusBar()
        statusbar.setFont(QFont('Arial', 7))
        self.text = QLabel('Zell FTF - 2D Simulation of cellular AGVs for optimizing transport')
        statusbar.addPermanentWidget(self.text)

    def center(self):
        geo = self.frameGeometry()
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo.moveCenter(center)
        self.move(geo.topLeft())


def main():
    # translator = QTranslator()
    app = QApplication(sys.argv)
    # app.installTranslator(translator)
    # ex = MouseTracker()
    main_window = MainWindow(app)
    main_window.showMaximized()
    # app.exec()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
