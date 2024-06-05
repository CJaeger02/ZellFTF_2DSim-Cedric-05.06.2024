# PySide6 packages
from PySide6.QtWidgets import *
from PySide6.QtGui import *


########################################################################################################################

# The DialogLoadFactory-Class (inheritance QDialog) is a Sub_QWidget for the WidgetMainWindow.
# It pops up, when the user wants to load a factory.

########################################################################################################################

class DialogLoadFactory(QDialog):
    def __init__(self):
        super(DialogLoadFactory, self).__init__()
        self.setFont(QFont('Arial', 10))
        self.setWindowTitle('ZellFTF - Notice!')

        # Create Layout
        self.vLayout1 = QVBoxLayout()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        message = QLabel("Do you want to load a factory?")
        message_2 = QLabel("<b>Make sure you have saved your old factory!<b>")
        self.vLayout1.addWidget(message)
        self.vLayout1.addWidget(message_2)
        self.vLayout1.addWidget(self.buttonBox)
        self.setLayout(self.vLayout1)
