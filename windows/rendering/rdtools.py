from os import path
from subprocess import Popen

from PySide2 import QtCore, QtGui, QtWidgets
import maya.cmds as cmds

import CETools.functions.rendering as rdf
from CETools.windows.toolkitWindow import Toolkit


def set_dir(self, filepath="/home", text_field=None, text='', file_type="EXR files (*.exr)"):
    file_directory = QtWidgets.QFileDialog.getOpenFileName(self, text, filepath, file_type)[0]
    if file_directory:
        text_field.setText(file_directory)
        print(file_directory)


def set_text_field(target):
    sel = cmds.ls(sl=1, l=1) or ['']
    target.setText(sel[0])


class Overscan(Toolkit):
    def __init__(self):
        super().__init__(name='Overscan',
                         tool_tip="Add overscan to a render based on a percentage and a camera's image plane size.",
                         toolbox_function=self.OverscanWidget)

    class OverscanWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            options_layout = QtWidgets.QGridLayout()

            overscan_input = QtWidgets.QDoubleSpinBox()
            overscan_input.setValue(5.0)
            overscan_input.setSuffix('%')
            overscan_input.setMinimum(0.0)
            overscan_input.setMaximum(100)
            overscan_input.setSingleStep(5.0)
            options_layout.addWidget(QtWidgets.QLabel("Overscan: "), 0, 0)
            options_layout.addWidget(overscan_input, 0, 1)

            button_layout = QtWidgets.QVBoxLayout()

            pole_vector_btn = QtWidgets.QPushButton('Set Overscan')
            pole_vector_btn.clicked.connect(
                lambda: rdf.set_overscan(overscan_value=overscan_input.value()))
            pole_vector_btn.setFixedHeight(25)
            button_layout.addWidget(pole_vector_btn)


            # Add to tool box layout
            self.tool_layout.addLayout(options_layout, 0, 0)
            self.tool_layout.addLayout(button_layout, 1, 0)
