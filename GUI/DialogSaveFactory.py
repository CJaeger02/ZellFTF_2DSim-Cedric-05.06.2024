# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *


########################################################################################################################

# The DialogSaveFactory-Class (inheritance QDialog) is a Sub_QWidget for the WidgetMainWindow.
# It pops up, when the user wants to save a factory.

########################################################################################################################

class DialogSaveFactory(QDialog):
    def __init__(self):
        super(DialogSaveFactory, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')

        print('opened saving!')

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        message = QLabel("Do you want to save the current factory?")
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)
