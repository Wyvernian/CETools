import os
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
import maya.cmds as cmds

import CETools.functions.animation as anf
from CETools.functions.commonFunctions import get_node_details


def set_text_field(target):
    sel = cmds.ls(sl=1, l=1) or ['']
    target.setText(sel[0])


class ToolWindow(QtWidgets.QWidget):

    def __init__(self, parent, tool=None, window=False, layout=None, height=200, width=250):
        super().__init__(parent)

        self.fileName = os.path.basename(__file__)
        self.filePath = os.path.dirname(__file__)
        self.layout = layout
        self.parent = parent
        self.window = window
        self.height = height
        self.width = width
        self.tool = tool
        self.build_win()

    def move_ui(self):
        pos = QtGui.QCursor.pos()
        self.move(pos.x() + 20, pos.y() + 15)

    def build_win(self):
        if self.window:
            self.setWindowFlags(QtCore.Qt.Tool)
            self.setFixedSize(self.width, self.height)
            container = QtWidgets.QWidget(self)
            tool_layout = QtWidgets.QGridLayout(container)
        else:
            tool_layout = self.layout

        scene_file = cmds.file(q=1, loc=1, un=0)
        if '/tasks' in scene_file:
            dir_path = scene_file.split('/tasks')[0] + '/tasks'
        else:
            dir_path = '/'.join(scene_file.split('/')[:-1])

        if self.tool == "CopyAnim":
            CopyAnimWidget(parent=self, tool_layout=tool_layout, dir_path=dir_path)
            self.setWindowTitle("Copy Anim")
        elif self.tool == "BookmarkTools":
            BookmarkToolsWidget(parent=self, tool_layout=tool_layout, dir_path=dir_path)
            self.setWindowTitle("Bookmark Tools")
        else:
            self.deleteLater()

        if self.window:
            self.move_ui()

        self.show()


class CopyAnimWidget(QtWidgets.QWidget):
    def __init__(self, parent, tool_layout=None, dir_path=''):
        super().__init__(parent)

        self.tool_layout = tool_layout
        self.dir_path = dir_path
        self.dir_input = []
        self.build_ui()

    def load_objects(self, category):
        objects = get_node_details(cmds.ls(sl=1, ad=1))
        for obj in objects:
            pass
        if category == 'source':
            pass
        elif category == 'target':
            pass
        else:
            cmds.error('Invalid category for load command')

    def build_ui(self):
        top_layout = QtWidgets.QGridLayout()
        z_host = QtWidgets.QLineEdit()
        z_host.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        top_layout.addWidget(QtWidgets.QLabel("Camera: "), 0, 0)
        top_layout.addWidget(z_host, 0, 1)

        z_target = QtWidgets.QLineEdit()
        z_target.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        top_layout.addWidget(QtWidgets.QLabel("Target Object: "), 1, 0)
        top_layout.addWidget(z_target, 1, 1)

        options_layout = QtWidgets.QGridLayout()

        load_left_btn = QtWidgets.QPushButton("Load Sources")
        load_left_btn.clicked.connect(lambda x: self.load_objects(category='source'))
        load_left_btn.setFixedHeight(25)
        options_layout.addWidget(load_left_btn, 0, 0)

        load_right_btn = QtWidgets.QPushButton("Load Targets")
        load_right_btn.clicked.connect(lambda x: self.load_objects(category='target'))
        load_right_btn.setFixedHeight(25)
        options_layout.addWidget(load_right_btn, 0, 1)

        update_cam_btn = QtWidgets.QPushButton()
        update_cam_btn.clicked.connect(lambda x: set_text_field(target=z_host))
        update_cam_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        update_cam_btn.setFixedSize(20, 20)
        update_cam_btn.setToolTip("Update camera selection")
        top_layout.addWidget(update_cam_btn, 0, 2)

        update_object_btn = QtWidgets.QPushButton()
        update_object_btn.clicked.connect(lambda x: set_text_field(target=z_target))
        update_object_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        update_object_btn.setFixedSize(20, 20)
        update_object_btn.setToolTip("Update target selection")
        top_layout.addWidget(update_object_btn, 1, 2)

        # Add to tool box layout
        self.tool_layout.addLayout(top_layout, 0, 0)
        self.tool_layout.addLayout(options_layout, 1, 0)


class BookmarkToolsWidget(QtWidgets.QWidget):
    def __init__(self, parent, tool_layout=None, dir_path=''):
        super().__init__(parent)

        self.tool_layout = tool_layout
        self.dir_path = dir_path
        self.dir_input = []
        self.build_ui()

    def build_ui(self):
        top_layout = QtWidgets.QGridLayout()
        z_host = QtWidgets.QLineEdit()
        z_host.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        top_layout.addWidget(QtWidgets.QLabel("Camera: "), 0, 0)
        top_layout.addWidget(z_host, 0, 1)

        z_target = QtWidgets.QLineEdit()
        z_target.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        top_layout.addWidget(QtWidgets.QLabel("Target Object: "), 1, 0)
        top_layout.addWidget(z_target, 1, 1)

        options_layout = QtWidgets.QGridLayout()

        load_left_btn = QtWidgets.QPushButton("Load Sources")
        load_left_btn.clicked.connect(lambda x: self.load_objects(category='source'))
        load_left_btn.setFixedHeight(25)
        options_layout.addWidget(load_left_btn, 0, 0)

        load_right_btn = QtWidgets.QPushButton("Load Targets")
        load_right_btn.clicked.connect(lambda x: self.load_objects(category='target'))
        load_right_btn.setFixedHeight(25)
        options_layout.addWidget(load_right_btn, 0, 1)

        update_cam_btn = QtWidgets.QPushButton()
        update_cam_btn.clicked.connect(lambda x: set_text_field(target=z_host))
        update_cam_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        update_cam_btn.setFixedSize(20, 20)
        update_cam_btn.setToolTip("Update camera selection")
        top_layout.addWidget(update_cam_btn, 0, 2)

        update_object_btn = QtWidgets.QPushButton()
        update_object_btn.clicked.connect(lambda x: set_text_field(target=z_target))
        update_object_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        update_object_btn.setFixedSize(20, 20)
        update_object_btn.setToolTip("Update target selection")
        top_layout.addWidget(update_object_btn, 1, 2)

        # Add to tool box layout
        self.tool_layout.addLayout(top_layout, 0, 0)
        self.tool_layout.addLayout(options_layout, 1, 0)
