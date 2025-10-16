from os import path

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QModelIndex
import maya.cmds as cmds
from functools import partial

import CETools.functions.modelling as mdf
from CETools.windows.customWidgets import DraggableItemsView, DraggableItemsModel, UVGridTableModel
from CETools.windows.toolkitWindow import Toolkit, SimpleTool


def set_dir(self, text_field, file_path="/home", caption='', file_type=''):
    if file_type != '':
        file_directory = QtWidgets.QFileDialog.getOpenFileName(self, caption, file_path, file_type)[0]
    else:
        file_directory = QtWidgets.QFileDialog.getExistingDirectory(self, caption, file_path,
                                                                    QtWidgets.QFileDialog.ShowDirsOnly)

    if file_directory:
        text_field.setText(file_directory)


def set_text_field(target):
    sel = cmds.ls(sl=1, l=1) or ['']
    target.setText(sel[0])


def toggle_fields(checkbox, first_field, second_field):
    state = checkbox.isChecked()
    first_field.setEnabled(state)
    second_field.setEnabled(not state)


class CopyUV(SimpleTool):
    def __init__(self):
        super().__init__(name='Copy UV', icon_path='copy_uv.png',
                         tool_tip="Copies UVs from the first selection to\nall other selected geometry, if the meshes "
                                  "match.",
                         on_click_function=lambda: mdf.copy_uvs())


class BorderEdges(SimpleTool):
    def __init__(self):
        super().__init__(name='Select Holes',
                         tool_tip="Selects the edges around holes in a selected mesh.",
                         on_click_function=lambda: mdf.select_border_edges())


class MoveToPivot(SimpleTool):
    def __init__(self):
        super().__init__(name='Move To Pivot', tool_tip="Snap selection to the manipulator pivot.",
                         on_click_function=lambda: mdf.move_to_pivot())


class StampModel(Toolkit):
    def __init__(self):
        super().__init__(name='Stamp', icon_path='geo_stamp.png',
                         tool_tip="Stamp geometry on selected edges of other geometry.",
                         toolbox_function=self.StampModelWidget)

    class StampModelWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()

            stamp_input = QtWidgets.QLineEdit()
            stamp_input.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Stamp Geometry:"), 0, 0)
            top_layout.addWidget(stamp_input, 0, 1)

            number_layout = QtWidgets.QGridLayout()

            count = QtWidgets.QSpinBox()
            count.setValue(30)
            number_layout.addWidget(QtWidgets.QLabel("Stamp Count:"), 1, 0)
            number_layout.addWidget(count, 1, 1)

            density = QtWidgets.QSpinBox()
            density.setValue(1)
            density.setSuffix(' units')
            density.setMinimum(1)
            density.setMaximum(10000)
            number_layout.addWidget(QtWidgets.QLabel("Distance between stamps:"), 2, 0)
            number_layout.addWidget(density, 2, 1)

            clamp = QtWidgets.QSpinBox()
            clamp.setValue(0)
            number_layout.addWidget(QtWidgets.QLabel("Clamp:"), 3, 0)
            number_layout.addWidget(clamp, 3, 1)

            smooth_scale = QtWidgets.QSpinBox()
            smooth_scale.setValue(3)
            smooth_scale.setMaximum(1)
            smooth_scale.setMaximum(9)
            number_layout.addWidget(QtWidgets.QLabel("Smooth Scale:"), 4, 0)
            number_layout.addWidget(smooth_scale, 4, 1)

            options_layout = QtWidgets.QVBoxLayout()

            use_fixed_count_btn = QtWidgets.QCheckBox("Fixed Stamp Count?")
            options_layout.addWidget(use_fixed_count_btn)
            use_fixed_count_btn.setChecked(False)
            use_fixed_count_btn.clicked.connect(
                lambda: toggle_fields(checkbox=use_fixed_count_btn, first_field=count, second_field=density))
            toggle_fields(checkbox=use_fixed_count_btn, first_field=count, second_field=density)

            is_instance_bool = QtWidgets.QCheckBox("Create Instances?")
            options_layout.addWidget(is_instance_bool)
            is_instance_bool.setChecked(False)

            button_layout = QtWidgets.QVBoxLayout()

            stamp_on_geometry_btn = QtWidgets.QPushButton("Stamp on connected edges")
            stamp_on_geometry_btn.clicked.connect(
                lambda x: mdf.distribute_on_geometry(stamp=stamp_input.text(), count=count.value(),
                                                     density=density.value(),
                                                     clamp=clamp.value(), smooth_scale=smooth_scale.value(),
                                                     use_fixed=use_fixed_count_btn.isChecked(), offset=0,
                                                     is_instance=is_instance_bool.isChecked()))
            stamp_on_geometry_btn.setFixedHeight(25)
            button_layout.addWidget(stamp_on_geometry_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)
            self.tool_layout.addLayout(number_layout, 2, 0)
            self.tool_layout.addLayout(button_layout, 3, 0)


class UVLayoutWidget(QtWidgets.QWidget):
    def __init__(self, parent, tool_layout=None, dir_path=''):
        super().__init__(parent)

        self.model = UVGridTableModel(50, 50)
        self.table_view = DraggableItemsView(self)
        self.text_line_edit = QtWidgets.QLineEdit(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.columns_spinbox = QtWidgets.QSpinBox(self)
        self.rows_spinbox = QtWidgets.QSpinBox(self)
        self.tool_layout = tool_layout
        self.dir_path = dir_path
        self.dir_input = []

        '''
        data = []
        headers = ['Name', 'Material']
        self.material_model = DraggableItemsModel(data, headers)
        self.table_model = DraggableItemsModel(data, headers)
        self.table_view = DraggableItemsView()
        self.table_view.setModel(self.table_model)
        '''
        self.build_ui()

    def get_materials(self):

        selected = cmds.ls(sl=1, l=1)
        shapes_in_sel = cmds.listRelatives(selected, s=1, f=1)
        shading_groups = cmds.listConnections(shapes_in_sel, type='shadingEngine')
        shaders = cmds.ls(cmds.listConnections(shading_groups), materials=1)

    def add_selected_objects(self):
        selected = cmds.ls(sl=1)

        for sel in selected:

            shape = cmds.listRelatives(sel, s=1, f=1)
            shader_group = cmds.listConnections(shape, type='shadingEngine')
            shader = cmds.ls(cmds.listConnections(shader_group), materials=1)
            if len(shader) > 1:
                cmds.warning(f'More than one material on {shape}, will assign to {shader}')

            new_name = f'Item {len(self.table_model._data) + 1}'
            new_material = shader[0]

            new_item = [new_name, new_material]
            self.table_model.addItem(new_item)

    def assign_material_to_grid(self):
        grid_layout = self.scroll_area.widget().sequencer_layout()
        if grid_layout is not None:
            self.grid_data[u][v][0] = material

    def update_grid(self):
        # Update the grid when spin box values change
        rows = self.rows_spinbox.value()
        columns = self.columns_spinbox.value()

        self.model.rows = rows
        self.model.columns = columns
        self.model.layoutChanged.emit()

    def update_button_text(self, new_text):
        # Update the text of the currently selected button in the table
        selected_index = self.table_view.currentIndex()
        if selected_index.isValid():
            print(selected_index, new_text)
            self.model.setData(selected_index, new_text, Qt.EditRole)

    def build_ui(self):
        top_layout = QtWidgets.QGridLayout()

        add_selected_btn = QtWidgets.QPushButton("Add Selected")
        add_selected_btn.clicked.connect(
            lambda x: self.add_selected_objects())
        add_selected_btn.setFixedHeight(25)
        top_layout.addWidget(add_selected_btn)

        rows_label = QtWidgets.QLabel('Rows:')
        columns_label = QtWidgets.QLabel('Columns:')

        self.columns_spinbox.setMinimum(1)
        self.columns_spinbox.setValue(10)
        self.rows_spinbox.setMinimum(1)
        self.rows_spinbox.setValue(10)

        self.rows_spinbox.valueChanged.connect(self.update_grid)
        self.columns_spinbox.valueChanged.connect(self.update_grid)

        self.text_line_edit.setPlaceholderText("Enter new text")
        self.text_line_edit.textChanged.connect(self.update_button_text)

        grid_layout = QtWidgets.QGridLayout()
        # widget = QtWidgets.QWidget()
        # widget.setLayout(grid_layout)

        self.table_view.setModel(self.model)
        self.table_view.verticalHeader().setDefaultSectionSize(25)
        self.table_view.horizontalHeader().setDefaultSectionSize(25)

        self.scroll_area.setFixedSize(250, 250)
        self.scroll_area.setAlignment(Qt.AlignVCenter)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.table_view)

        grid_layout.addWidget(self.text_line_edit)
        grid_layout.addWidget(self.rows_spinbox)
        grid_layout.addWidget(self.columns_spinbox)
        grid_layout.addWidget(self.scroll_area)

        # Add to tool box layout
        self.tool_layout.addLayout(top_layout, 0, 0)
        self.tool_layout.addLayout(grid_layout, 1, 0)


class QuickMirror(Toolkit):
    def __init__(self):
        super().__init__(name='Quick Mirror', icon_path='quick_mirror.png',
                         tool_tip="Mirror in many intuitive ways without Maya's trash defaults!",
                         toolbox_function=self.QuickMirrorWidget)

    class QuickMirrorWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.cut_mesh_toggle = QtWidgets.QCheckBox('Cut and Merge Mesh')
            self.instance_toggle = QtWidgets.QCheckBox('Instance')
            self.interactive_toggle = QtWidgets.QCheckBox('Interactive Mirror')
            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def run_simple_mirror(self, axis, direction, mirror_axis):
            mdf.advanced_mirror(axis=axis, direction=direction, mirror_axis=mirror_axis,
                                cut_mesh=self.cut_mesh_toggle.isChecked(),
                                instance=self.instance_toggle.isChecked(),
                                interactive=self.interactive_toggle.isChecked())

        def build_ui(self):
            mirror_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QGridLayout()

            options_layout.addWidget(self.cut_mesh_toggle)
            self.cut_mesh_toggle.setChecked(False)

            options_layout.addWidget(self.instance_toggle)
            self.cut_mesh_toggle.setChecked(False)

            options_layout.addWidget(self.interactive_toggle)
            self.cut_mesh_toggle.setChecked(False)

            # Add mirror options efficiently
            mirror_options = ('BOUNDING BOX', 'OBJECT', 'WORLD')
            mirror_axes = {'X': ['+X', '-X'], 'Y': ['+Y', '-Y'], 'Z': ['+Z', '-Z']}

            layout_index = 0
            for option_index, option in enumerate(mirror_options):
                btn_layout = QtWidgets.QGridLayout()
                label_layout = QtWidgets.QVBoxLayout()

                label_layout.addWidget(QtWidgets.QLabel(option))

                self.tool_layout.addLayout(label_layout, layout_index, 0)
                layout_index += 1

                row_index = 0

                for axis_index, axis in enumerate(mirror_axes.keys()):
                    for i, direction in enumerate(mirror_axes[axis]):
                        btn = QtWidgets.QPushButton(direction)
                        btn.clicked.connect(
                            partial(self.run_simple_mirror, axis=axis_index, direction=i, mirror_axis=option_index))
                        btn.setFixedSize(25, 20)
                        if axis_index == 0:
                            btn.setStyleSheet(f"background-color: rgb(50, 0, 0);")
                        elif axis_index == 1:
                            btn.setStyleSheet(f"background-color: rgb(0, 50, 0);")
                        elif axis_index == 2:
                            btn.setStyleSheet(f"background-color: rgb(0, 0, 50);")

                        btn_layout.addWidget(btn, 1, row_index)
                        row_index += 1

                self.tool_layout.addLayout(btn_layout, layout_index, 0)
                layout_index += 1

            self.tool_layout.addLayout(options_layout, layout_index, 0)


class MeshClean(Toolkit):
    def __init__(self):
        super().__init__(name='Mesh Clean', icon_path='mesh_cleanup.png',
                         tool_tip="Clean lamina faces and other stuff that I am yet to add",
                         toolbox_function=self.MeshCleanWidget)

    class MeshCleanWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            options_layout = QtWidgets.QGridLayout()

            lamina_clean_layout = QtWidgets.QGridLayout()

            lamina_label_layout = QtWidgets.QVBoxLayout()
            lamina_label = QtWidgets.QLabel('Clean Overlapping Duplicates'.upper())
            lamina_label.setStyleSheet("font-weight: bold;")
            lamina_label_layout.addWidget(lamina_label)

            options_layout.addLayout(lamina_label_layout, 0, 0)
            options_layout.addLayout(lamina_clean_layout, 1, 0)

            distance_input = QtWidgets.QDoubleSpinBox()
            distance_input.setValue(0.0)
            distance_input.setSuffix(' units')
            distance_input.setMinimum(0.0)
            distance_input.setMaximum(1)
            distance_input.setSingleStep(0.01)
            lamina_clean_layout.addWidget(QtWidgets.QLabel("Vert Merge Distance:"), 0, 0)
            lamina_clean_layout.addWidget(distance_input, 0, 1)

            pole_vector_btn = QtWidgets.QPushButton('Clean')
            pole_vector_btn.clicked.connect(
                lambda: mdf.clean_double_faces(distance=distance_input.value()))
            pole_vector_btn.setFixedHeight(25)
            lamina_clean_layout.addWidget(pole_vector_btn, 0, 2)

            # Add to tool box layout
            self.tool_layout.addLayout(options_layout, 0, 0)


class Rotate(Toolkit):
    def __init__(self):
        super().__init__(name='Rotate',
                         tool_tip="Rotate with more precision! This really should be in Maya already!",
                         toolbox_function=self.RotateWidget)

    class RotateWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.rotate_input = QtWidgets.QDoubleSpinBox()
            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def run_rotate(self, axis, direction):
            # This seems scuffed, but it works, so...
            rotate_axes = [0, 0, 0]
            rotation_value = self.rotate_input.value()
            direction_mult = 1
            if direction == 1:
                direction_mult = -1

            rotate_axes[axis] = rotation_value * direction_mult

            cmds.xform(cmds.ls(sl=1), ro=rotate_axes, os=1, r=1)

        def build_ui(self):
            rotation_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QGridLayout()

            self.rotate_input.setValue(45.0)
            self.rotate_input.setSuffix(' degrees')
            self.rotate_input.setMinimum(0.0)
            self.rotate_input.setMaximum(360)
            self.rotate_input.setSingleStep(15.0)
            rotation_layout.addWidget(QtWidgets.QLabel("Rotation: "), 0, 0)
            rotation_layout.addWidget(self.rotate_input, 0, 1)

            # Add mirror options efficiently
            rotation_axes = {'X': ['+X', '-X'], 'Y': ['+Y', '-Y'], 'Z': ['+Z', '-Z']}

            btn_layout = QtWidgets.QGridLayout()

            row_index = 0

            for axis_index, axis in enumerate(rotation_axes.keys()):
                for i, direction in enumerate(rotation_axes[axis]):
                    btn = QtWidgets.QPushButton(direction)
                    btn.clicked.connect(
                        partial(self.run_rotate, axis=axis_index, direction=i))
                    btn.setFixedSize(25, 20)
                    if axis_index == 0:
                        btn.setStyleSheet(f"background-color: rgb(50, 0, 0);")
                    elif axis_index == 1:
                        btn.setStyleSheet(f"background-color: rgb(0, 50, 0);")
                    elif axis_index == 2:
                        btn.setStyleSheet(f"background-color: rgb(0, 0, 50);")

                    btn_layout.addWidget(btn, 1, row_index)
                    row_index += 1

            self.tool_layout.addLayout(rotation_layout, 0, 0)
            self.tool_layout.addLayout(btn_layout, 1, 0)
