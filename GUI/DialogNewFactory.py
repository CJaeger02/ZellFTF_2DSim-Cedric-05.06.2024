# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *


########################################################################################################################

# The DialogNewFactory-Class (inheritance QDialog) is a Sub_QWidget for the WidgetMainWindow.
# It pops up, when the user wants to create a new factory.

########################################################################################################################

class DialogNewFactory(QDialog):
    def __init__(self):
        super(DialogNewFactory, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')

        print('opened!')

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        message = QLabel('Do you really want to create a new factory?')
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)


class DialogOverwriteDefaultFactory(QDialog):
    def __init__(self):
        super(DialogOverwriteDefaultFactory, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        message = QLabel('It is not possible to overwrite the default/test factory!')
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)
