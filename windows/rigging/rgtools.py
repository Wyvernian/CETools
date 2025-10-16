import os
from functools import partial
import re
import unicodedata

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
import maya.cmds as cmds

import CETools.functions.rigging as rgf

from CETools.windows.customWidgets import CurveListModel, CurveSortFilterProxyModel, CheckboxGroup
from CETools.functions.commonFunctions import find_closest_folder
from CETools.windows.toolkitWindow import SimpleTool, Toolkit


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


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def toggle_fields(checkbox, first_field, second_field):
    state = checkbox.isChecked()
    first_field.setEnabled(state)
    second_field.setEnabled(not state)


class AiColorAttribute(Toolkit):
    def __init__(self):
        super().__init__(name='Write Shader Connections', icon_path='color_attribute.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.AiColorAttributeWidget)

    class AiColorAttributeWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()

            material_input = QtWidgets.QLineEdit()
            material_input.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Material:"), 0, 0)
            top_layout.addWidget(material_input, 0, 1)

            ctrl_input = QtWidgets.QLineEdit()
            ctrl_input.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Control:"), 1, 0)
            top_layout.addWidget(ctrl_input, 1, 1)

            options_layout = QtWidgets.QVBoxLayout()

            button_layout = QtWidgets.QVBoxLayout()

            stamp_on_geometry_btn = QtWidgets.QPushButton("Link material control to selected geometry")
            stamp_on_geometry_btn.clicked.connect(
                lambda x: rgf.arnold_color_attribute(shader=material_input.text(), ctrl=ctrl_input.text()))
            stamp_on_geometry_btn.setFixedHeight(25)
            button_layout.addWidget(stamp_on_geometry_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)
            self.tool_layout.addLayout(button_layout, 2, 0)


class Palette(Toolkit):
    def __init__(self):
        super().__init__(name='Palette', icon_path='color_palette.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.PaletteWidget)

    class PaletteWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.in_outliner_checkbox = QtWidgets.QCheckBox("Set colour in Outliner?")
            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def set_color(self, index):
            rgf.set_index_color(index=index, selection=None, in_outliner=self.in_outliner_checkbox.isChecked())

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QGridLayout()

            options_layout.addWidget(self.in_outliner_checkbox)
            self.in_outliner_checkbox.setChecked(False)

            row, col = 0, 0
            k = 255
            for i in range(1, 32):
                # Add widgets to the layout
                if col == 8:
                    col = 0
                    row += 1
                color_index = cmds.colorIndex(i, q=True)
                color = [round(x * k) for x in color_index]
                btn = QtWidgets.QPushButton()
                btn.clicked.connect(partial(self.set_color, index=i))
                btn.setStyleSheet("background-color: rgb{};".format(tuple(color)))
                btn.setFixedSize(20, 20)
                top_layout.addWidget(btn, row, col)
                col += 1

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class JointTools(Toolkit):
    def __init__(self):
        super().__init__(name='Joint Tools', icon_path='joint_tools.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.JointToolsWidget)

    class JointToolsWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            ro_layout = QtWidgets.QGridLayout()
            button_layout = QtWidgets.QVBoxLayout()
            options_layout = QtWidgets.QGridLayout()

            rotation_order_options = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']

            for i, ro in enumerate(rotation_order_options):
                btn = QtWidgets.QPushButton(ro)
                btn.clicked.connect(partial(rgf.set_rotate_order, ro=i))
                btn.setFixedSize(30, 20)
                ro_layout.addWidget(btn, 0, i)

            options_layout.addWidget(QtWidgets.QLabel("Toggle Rotation Axes Visibility:"), 0, 0)

            rot_axes_toggle_btn = QtWidgets.QPushButton("ON")
            rot_axes_toggle_btn.clicked.connect(
                lambda x: rgf.toggle_local_rot_axes(state=True))
            rot_axes_toggle_btn.setFixedHeight(25)
            options_layout.addWidget(rot_axes_toggle_btn, 0, 1)

            rot_axes_toggle_btn = QtWidgets.QPushButton("OFF")
            rot_axes_toggle_btn.clicked.connect(
                lambda x: rgf.toggle_local_rot_axes(state=False))
            rot_axes_toggle_btn.setFixedHeight(25)
            options_layout.addWidget(rot_axes_toggle_btn, 0, 2)

            align_end_joint_btn = QtWidgets.QPushButton("Align End Joints In Hierarchy")
            align_end_joint_btn.clicked.connect(
                lambda x: rgf.align_end_joint())
            align_end_joint_btn.setFixedHeight(25)
            button_layout.addWidget(align_end_joint_btn)

            deselect_ends_btn = QtWidgets.QPushButton("Deselect End Joints")
            deselect_ends_btn.clicked.connect(
                lambda x: rgf.deselect_ends())
            deselect_ends_btn.setFixedHeight(25)
            button_layout.addWidget(deselect_ends_btn)

            spline_ik_btn = QtWidgets.QPushButton("SplineIK from Joints")
            spline_ik_btn.clicked.connect(
                lambda x: rgf.spline_ik(div=3))
            spline_ik_btn.setFixedHeight(25)
            button_layout.addWidget(spline_ik_btn)

            segment_joints_layout = QtWidgets.QHBoxLayout()

            segment_joints_input = QtWidgets.QSpinBox()
            segment_joints_input.setMaximum(20)
            segment_joints_input.setValue(3)
            segment_joints_input.setSuffix(' joints')

            segment_joints_btn = QtWidgets.QPushButton("Insert Joints")
            segment_joints_btn.clicked.connect(
                lambda x: rgf.segment_selected(val=segment_joints_input.value() + 1))
            segment_joints_btn.setFixedHeight(25)
            segment_joints_layout.addWidget(segment_joints_input)
            segment_joints_layout.addWidget(segment_joints_btn)

            button_layout.addLayout(segment_joints_layout)

            # Add to tool box layout
            self.tool_layout.addLayout(ro_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)
            self.tool_layout.addLayout(button_layout, 2, 0)


class CurveCreator(Toolkit):
    def __init__(self):
        super().__init__(name='Curve Creator', icon_path='curve_creator.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.CurveCreatorWidget)

    class CurveCreatorWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.search_field = QtWidgets.QLineEdit()
            self.image_label = QtWidgets.QLabel()
            self.image_index = 0  # Keep track of the currently displayed image
            self.images = []
            self.favourite_btn = QtWidgets.QPushButton('★')
            self.save_btn = QtWidgets.QPushButton('+')
            self.delete_btn = QtWidgets.QPushButton('✖')
            self.rename_btn = QtWidgets.QPushButton('Rename')
            self.list_view = QtWidgets.QListView()
            self.default_path = os.path.join(find_closest_folder(__file__, 'CETools'), 'data', 'curves',
                                             'default')  # '/syd_home/bmurphie/maya/2022/scripts/CETools/data/curves/default/'
            self.custom_path = os.path.join(find_closest_folder(__file__, 'CETools'), 'data', 'curves', 'custom')
            self.dir_input = []
            self.source_model = CurveListModel(self)
            self.proxy_model = CurveSortFilterProxyModel(self)
            self.proxy_model.setDynamicSortFilter(True)
            self.proxy_model.sort(0, QtCore.Qt.AscendingOrder)
            self.proxy_model.setFilterRole(0)
            self.proxy_model.setSourceModel(self.source_model)
            self.list_view.setModel(self.proxy_model)
            self.list_view.selectionModel().selectionChanged.connect(lambda: self.enable_edits())
            self.build_ui()

        def save_snapshot(self, name):
            # Create new viewport, isolate curve, focus camera on curve, run playblast, save as jpeg, close window

            selected = cmds.ls(sl=1, l=1)
            for shape in cmds.listRelatives(selected, s=1):
                line_width = cmds.getAttr(f'{shape}.lineWidth')
                cmds.setAttr(f'{shape}.lineWidth', 2)

            image_path = os.path.join(self.custom_path, name)
            first_frame = cmds.currentTime(q=1)
            playblast_options = {
                "filename": image_path,
                "format": "image",  # Specify that you want an image sequence
                "forceOverwrite": True,
                "sequenceTime": 0,  # Specify the current frame
                "width": 200,
                "height": 200,
                "startTime": first_frame,
                "endTime": first_frame,
                "viewer": False,  # Set to True if you want to playblast with Maya's built-in viewer
                "compression": "jpg",  # Set the image format to JPEG
                "quality": 100,  # JPEG quality (0-100)
                "framePadding": 0,  # Specify padding for the file sequence
                "offScreen": True,  # Playblast offscreen
            }

            panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
            state = cmds.isolateSelect(panel, q=True, state=True)

            cmds.isolateSelect(panel, state=True)
            cmds.select(selected, r=1)
            cmds.isolateSelect(panel, addSelected=True)

            # new_cam = cmds.duplicate('persp')[0]
            cmds.select(selected, r=1)
            cmds.viewFit('persp', f=1)
            cmds.select(cl=1)
            cmds.refresh(f=True)

            cmds.modelEditor(panel, e=1, grid=0, hud=0)

            cmds.playblast(**playblast_options)
            cmds.isolateSelect(panel, state=state)
            # cmds.delete(new_cam)

            new_file = image_path + '.1.jpg'

            self.images.append(QtGui.QPixmap(new_file))

            for shape in cmds.listRelatives(selected, s=1):
                cmds.setAttr(f'{shape}.lineWidth', line_width)

            return new_file

        def save_curve(self):
            saved_curve = rgf.save_custom_curve(self.custom_path)

            if saved_curve:

                # CONFIRM AND NAME DIALOG
                naming = cmds.promptDialog(
                    title='Custom Curve',
                    message='Enter Name:',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')

                if naming == 'OK':
                    new_curve_name = cmds.promptDialog(query=True, text=True)
                    new_curve_name = slugify(new_curve_name, allow_unicode=False)
                    if new_curve_name == "":
                        cmds.warning("Please enter a name into the field.")
                        return

                    with open(os.path.join(self.custom_path, new_curve_name + '.crv'), "w") as newFile:
                        newFile.write(saved_curve)

                    image_path = self.save_snapshot(new_curve_name)
                    self.source_model.items.append((False, True, new_curve_name, image_path))
                    self.proxy_model.invalidate()
                    self.list_view.clearSelection()

                if naming == 'Cancel':
                    return

        def search_item(self):
            syntax = QtCore.QRegExp.RegExp
            case_sensitivity = (False and Qt.CaseSensitive or Qt.CaseInsensitive)
            reg_exp = QtCore.QRegExp(self.search_field.text(), case_sensitivity, syntax)
            self.proxy_model.setFilterRegExp(reg_exp)
            index = self.proxy_model.index(0, 0)
            self.list_view.selectionModel().setCurrentIndex(index, QtCore.QItemSelectionModel.ClearAndSelect)

        def enable_edits(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, custom, name, image_path = self.source_model.items[row]

                # Enable delete and edit buttons
                self.delete_btn.setEnabled(custom)
                self.rename_btn.setEnabled(custom)
                self.load_image()

        def rename_curve(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, custom, name, image_path = self.source_model.items[row]
                if custom:
                    naming = cmds.promptDialog(
                        title='Rename Curve',
                        message='Enter Name:',
                        button=['OK', 'Cancel'],
                        defaultButton='OK',
                        cancelButton='Cancel',
                        dismissString='Cancel')

                    if naming == 'OK':
                        new_name = cmds.promptDialog(query=True, text=True)
                        if new_name == "":
                            cmds.warning("Please enter a name into the field.")
                            return
                    else:
                        return

                    new_name = slugify(new_name, allow_unicode=False)
                    old_curve = os.path.join(self.custom_path, name + '.crv')
                    new_curve = os.path.join(self.custom_path, new_name + '.crv')
                    os.rename(old_curve, new_curve)
                    self.source_model.items[row] = (favourite, True, new_name, image_path)
                    self.source_model.dataChanged.emit(index, index)

        def toggle_favourite(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, custom, name, image_path = self.source_model.items[row]
                self.source_model.items[row] = (not favourite, custom, name, image_path)
                self.source_model.dataChanged.emit(index, index)

                if not favourite:
                    cmds.optionVar(sva=('curve_favourites', name))
                else:
                    favourite_list = cmds.optionVar(q='curve_favourites')
                    for i, curve in enumerate(favourite_list):
                        if name == curve:
                            cmds.optionVar(rfa=('curve_favourites', i))

        def delete_curve(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                _, custom, name, image_path = self.source_model.items[row]

                if custom:
                    confirm = cmds.confirmDialog(title='Delete Curve', message='Are you sure?', button=['Yes', 'No'],
                                                 defaultButton='Yes', cancelButton='No', dismissString='No')

                    if confirm == 'Yes':

                        del self.source_model.items[index.row()]
                        curve_path = os.path.join(self.custom_path, name + '.crv')
                        if os.path.exists(curve_path):
                            os.remove(curve_path)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        self.proxy_model.invalidate()
                        self.list_view.clearSelection()

        def load_image(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                _, _, name, image_path = self.source_model.items[row]
                if image_path:
                    self.image_label.setPixmap(image_path)
                else:
                    return None

        def build_curve(self, replace=False):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                _, custom, name, _ = self.source_model.items[row]

                if custom:
                    rgf.build_custom_curve(dir_path=self.custom_path, curve_name=name, replace=replace)
                else:
                    rgf.build_custom_curve(dir_path=self.default_path, curve_name=name, replace=replace)

        def load_data(self):
            image_paths = []
            if os.path.exists(self.default_path):
                favourite_list = cmds.optionVar(q='curve_favourites')
                items = []
                default_curves = os.listdir(self.default_path)
                for curve in default_curves:
                    if '.crv' not in curve:
                        continue

                    curve_name = curve.split('.crv')[0]
                    favourite = False
                    if favourite_list:
                        if curve_name in favourite_list:
                            favourite = True

                    # Curve image search
                    image_path = os.path.join(self.default_path, curve_name + '.1.jpg')
                    if os.path.isfile(image_path):
                        image_paths.append(image_path)

                    items.append((favourite, False, curve_name, image_path))

                custom_curves = os.listdir(self.custom_path)
                for curve in custom_curves:
                    if '.crv' not in curve:
                        continue
                    curve_name = curve.split('.crv')[0]
                    favourite = False
                    if favourite_list:
                        if curve_name in favourite_list:
                            favourite = True

                    image_path = os.path.join(self.custom_path, curve_name + '.1.jpg')
                    if os.path.isfile(image_path):
                        image_paths.append(image_path)

                    items.append((favourite, True, curve_name, image_path))

                self.source_model.items = items

                # PIXMAP DISPLAY
                self.images = [QtGui.QPixmap(path) for path in image_paths]  # Preload images
                if self.images:  # Ensure there's at least one image
                    self.image_label.setPixmap(self.images[0])

            else:
                cmds.warning(f'Could not find curve data to load at {self.default_path}')

        def build_ui(self):
            search_layout = QtWidgets.QGridLayout()

            self.search_field.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.search_field.textChanged.connect(lambda: self.search_item())
            self.search_field.returnPressed.connect(lambda: self.build_curve())
            search_layout.addWidget(QtWidgets.QLabel("Filter by:"), 0, 0)
            search_layout.addWidget(self.search_field, 0, 1)

            main_layout = QtWidgets.QGridLayout()

            options_layout = QtWidgets.QGridLayout()
            sidebar_container = QtWidgets.QWidget()
            sidebar_layout = QtWidgets.QVBoxLayout()
            sidebar_container.setLayout(sidebar_layout)

            image_layout = QtWidgets.QVBoxLayout()
            image_layout.addWidget(self.image_label)
            self.image_label.setFixedSize(100, 100)

            self.list_view.setUniformItemSizes(True)
            self.list_view.setSpacing(2)
            self.list_view.setFixedWidth(120)

            # OPTIONS BUTTONS

            btn_width = 45
            btn_height = 35

            self.favourite_btn.setFixedSize(btn_width, btn_height)
            self.favourite_btn.clicked.connect(lambda: self.toggle_favourite())
            self.favourite_btn.setStyleSheet("font-size: 20pt;")
            options_layout.addWidget(self.favourite_btn, 0, 0)

            self.save_btn.setFixedSize(btn_width, btn_height)
            self.save_btn.clicked.connect(lambda: self.save_curve())
            self.save_btn.setStyleSheet("font-size: 20pt;")
            options_layout.addWidget(self.save_btn, 0, 1)

            self.delete_btn.setEnabled(False)
            self.delete_btn.clicked.connect(lambda: self.delete_curve())
            self.delete_btn.setStyleSheet("font-size: 20pt;")
            self.delete_btn.setFixedSize(btn_width, btn_height)
            options_layout.addWidget(self.delete_btn, 1, 0)

            self.rename_btn.setEnabled(False)
            self.rename_btn.clicked.connect(lambda: self.rename_curve())
            self.rename_btn.setFixedSize(btn_width, btn_height)
            options_layout.addWidget(self.rename_btn, 1, 1)

            sidebar_layout.addLayout(image_layout)
            sidebar_layout.addLayout(options_layout)

            main_layout.addWidget(sidebar_container, 0, 0)
            main_layout.addWidget(self.list_view, 0, 1)

            self.source_model.layoutChanged.emit()

            button_layout = QtWidgets.QGridLayout()

            create_curve_btn = QtWidgets.QPushButton('Create Curve')
            create_curve_btn.clicked.connect(
                lambda: self.build_curve())
            create_curve_btn.setFixedHeight(25)
            button_layout.addWidget(create_curve_btn, 0, 0)

            replace_curve_btn = QtWidgets.QPushButton('Replace Curve')
            replace_curve_btn.clicked.connect(
                lambda: self.build_curve(replace=True))
            replace_curve_btn.setFixedHeight(25)
            button_layout.addWidget(replace_curve_btn, 0, 1)

            # Add to tool box layout
            self.tool_layout.addLayout(search_layout, 0, 0)
            self.tool_layout.addLayout(main_layout, 1, 0)
            self.tool_layout.addLayout(button_layout, 2, 0)

            # self.proxy_model.sortBy(0)

            self.load_data()


class MatrixRigging(Toolkit):
    def __init__(self):
        super().__init__(name='Matrix Rigging Tools', icon_path='matrix_tools.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.MatrixRiggingWidget)

    class MatrixRiggingWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            options_layout = QtWidgets.QGridLayout()

            button_layout = QtWidgets.QVBoxLayout()

            space_switch_btn = QtWidgets.QPushButton('Space Switch')
            space_switch_btn.clicked.connect(
                lambda: rgf.space_switch())
            space_switch_btn.setFixedHeight(25)
            button_layout.addWidget(space_switch_btn)

            negate_xform = CheckboxGroup(name="Negate Transforms")
            negate_xform.add_options({
                "t": [True, "Tr"],
                "r": [False, "Ro"],
                "s": [False, "Sc"],
            })
            negate_xform.button.clicked.connect(
                lambda: rgf.negate_transforms(translation=negate_xform.boxes[0].isChecked(),
                                              rotation=negate_xform.boxes[1].isChecked(),
                                              scale=negate_xform.boxes[2].isChecked()))
            button_layout.addWidget(negate_xform)

            freeze_offset = CheckboxGroup(name="Freeze Offset Matrix")
            freeze_offset.add_options({
                "lock": [False, "Lock"]
            })
            freeze_offset.button.clicked.connect(lambda: rgf.offset_matrix(lock=freeze_offset.boxes[0].isChecked()))
            button_layout.addWidget(freeze_offset)

            # Add to tool box layout
            self.tool_layout.addLayout(options_layout, 0, 0)
            self.tool_layout.addLayout(button_layout, 1, 0)


class RigPreset(Toolkit):
    def __init__(self):
        super().__init__(name='Rigging Presets', icon_path='rig_presets.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.RigPresetWidget)

    class RigPresetWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def use_preset(self, preset):
            if preset == 'Vehicle':
                rgf.create_vehicle_rig()
            elif preset == 'Rope/Cable':
                rgf.create_rope_rig()
            elif preset == 'Tyre':
                rgf.create_tyre_rig()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QGridLayout()

            name_input = QtWidgets.QLineEdit()
            name_input.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Rig Name:"), 0, 0)
            top_layout.addWidget(name_input, 0, 1)

            presets = ['Vehicle', 'Rope/Cable', 'Tyre']
            preset_options = QtWidgets.QComboBox()
            preset_options.activated.connect(lambda: self.use_preset(presets[preset_options.currentText()]))
            for preset in presets:
                preset_options.addItem(preset)
            top_layout.addWidget(preset_options, 1, 0)

            button_layout = QtWidgets.QVBoxLayout()

            create_rig_btn = QtWidgets.QPushButton('Build Rig')
            create_rig_btn.clicked.connect(
                lambda: rgf.create_vehicle_rig(name=name_input.text()))
            create_rig_btn.setFixedHeight(25)
            button_layout.addWidget(create_rig_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)
            self.tool_layout.addLayout(button_layout, 2, 0)


class OptimiseRig(Toolkit):
    def __init__(self):
        super().__init__(name='Optimise Rig', icon_path='optimise_rig.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.OptimiseWidget)

    class OptimiseWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            options_layout = QtWidgets.QGridLayout()

            button_layout = QtWidgets.QVBoxLayout()

            pole_vector_btn = QtWidgets.QPushButton('Align pole vector')
            pole_vector_btn.clicked.connect(
                lambda: rgf.align_pole_vector())
            pole_vector_btn.setFixedHeight(25)
            button_layout.addWidget(pole_vector_btn)

            retarget_con_btn = QtWidgets.QPushButton('Retarget constraints')
            retarget_con_btn.clicked.connect(
                lambda: rgf.retarget_constraints())
            retarget_con_btn.setFixedHeight(25)
            button_layout.addWidget(retarget_con_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(options_layout, 0, 0)
            self.tool_layout.addLayout(button_layout, 1, 0)


class ClusterTools(Toolkit):
    def __init__(self):
        super().__init__(name='Cluster Tools',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         toolbox_function=self.ClusterToolsWidget)

    class ClusterToolsWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            options_layout = QtWidgets.QGridLayout()

            button_layout = QtWidgets.QVBoxLayout()

            cluster_btn = QtWidgets.QPushButton('Cluster each in selected')
            cluster_btn.clicked.connect(
                lambda: rgf.clusters_on_selected())
            cluster_btn.setFixedHeight(25)
            button_layout.addWidget(cluster_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(options_layout, 0, 0)
            self.tool_layout.addLayout(button_layout, 1, 0)
