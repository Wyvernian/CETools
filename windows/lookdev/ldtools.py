import os
from os import path

import json
from functools import partial
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QMimeData

import maya.cmds as cmds
from glob import glob

import CETools.functions.lookdev as ldf
from CETools.windows.toolkitWindow import Toolkit, SimpleTool
from CETools.windows.customWidgets import HDRIListModel, CurveSortFilterProxyModel, DragWidget, DragItem
from CETools.functions.commonFunctions import lock_attributes, get_object_type, UndoStack


def set_dir(self, text_field, file_path="/home", caption='', file_type=''):
    if file_type != '':
        file_directory = QtWidgets.QFileDialog.getOpenFileName(self, caption, file_path, file_type)[0]
    else:
        file_directory = QtWidgets.QFileDialog.getExistingDirectory(self, caption, file_path,
                                                                    QtWidgets.QFileDialog.ShowDirsOnly)

    if file_directory:
        text_field.setText(file_directory)


class WriteShaderConnections(SimpleTool):
    def __init__(self):
        super().__init__(name='Write Shader Connections', icon_path='export_material_link.png',
                         tool_tip='Export a .json file to copy over Arnold materials from Maya to Houdini',
                         on_click_function=lambda: ldf.write_shader_connections())


class CreateStandardMaterial(SimpleTool):
    def __init__(self):
        super().__init__(name='Create Standard Material', tool_tip='What the name says.',
                         on_click_function=lambda: ldf.create_ai_standard_surface())


class CreateRenderBalls(SimpleTool):
    def __init__(self):
        super().__init__(name='Create Render Balls', tool_tip='Create and attach matte ball, chrome ball\nand Macbeth '
                                                              'Chart to the selected camera.',
                         icon_path='lighting_balls.png',
                         on_click_function=lambda: ldf.create_render_balls(file_path=self.get_macbeth_path()))

    def get_macbeth_path(self):

        pass


class TextureLink(Toolkit):

    def __init__(self):
        super().__init__(name='Texture Link', icon_path='texture_link.png',
                         tool_tip='Automatically assign textures from a folder to a material',
                         toolbox_function=self.TextureLinkWidget)

    class TextureLinkWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()

            texture_dir = QtWidgets.QLineEdit(self.dir_path)
            self.dir_input.append(texture_dir)
            texture_dir.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Texture Folder:"), 0, 0)
            top_layout.addWidget(texture_dir, 0, 1)

            options_layout = QtWidgets.QVBoxLayout()

            diffuse_btn = QtWidgets.QCheckBox("Diffuse")
            options_layout.addWidget(diffuse_btn)
            diffuse_btn.setChecked(True)

            specular_btn = QtWidgets.QCheckBox("Specular")
            options_layout.addWidget(specular_btn)
            specular_btn.setChecked(True)

            metalness_btn = QtWidgets.QCheckBox("Metalness")
            options_layout.addWidget(metalness_btn)
            metalness_btn.setChecked(True)

            normals_btn = QtWidgets.QCheckBox("Normals")
            options_layout.addWidget(normals_btn)
            normals_btn.setChecked(True)

            displacement_btn = QtWidgets.QCheckBox("Displacement")
            options_layout.addWidget(displacement_btn)
            displacement_btn.setChecked(False)

            assign_textures_btn = QtWidgets.QPushButton("Assign Textures")
            assign_textures_btn.clicked.connect(
                lambda x: ldf.connect_textures(folder_path=texture_dir.text(), diffuse=diffuse_btn.isChecked(),
                                               specular=specular_btn.isChecked(), metalness=metalness_btn.isChecked(),
                                               normals=normals_btn.isChecked(),
                                               displacement=displacement_btn.isChecked()))
            assign_textures_btn.setFixedHeight(25)
            options_layout.addWidget(assign_textures_btn)

            retime_select = QtWidgets.QPushButton()
            retime_select.setFixedSize(20, 20)
            retime_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon))
            retime_select.clicked.connect(
                lambda x: set_dir(self, file_path=texture_dir.text() or self.dir_path or '', text_field=texture_dir,
                                  caption='Select Texture Folder'))
            retime_select.setToolTip("Select File")
            top_layout.addWidget(retime_select, 0, 2)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class AssignByName(Toolkit):

    def __init__(self):
        super().__init__(name='Assign By Name',
                         tool_tip='Assign materials to objects or override other materials by name',
                         toolbox_function=self.AssignByNameWidget)

    class AssignByNameWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()

            shader_btn = QtWidgets.QLineEdit('lambert1')
            shader_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Shader:"), 0, 0)
            top_layout.addWidget(shader_btn, 0, 1)

            matching_string_btn = QtWidgets.QLineEdit('Sphere 1 p')
            matching_string_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Matching Text:"), 1, 0)
            top_layout.addWidget(matching_string_btn, 1, 1)

            options_layout = QtWidgets.QVBoxLayout()

            object_radio_btn = QtWidgets.QRadioButton("Target Objects")
            options_layout.addWidget(object_radio_btn)
            object_radio_btn.setChecked(True)

            material_radio_btn = QtWidgets.QRadioButton("Target Materials")
            options_layout.addWidget(material_radio_btn)
            material_radio_btn.setChecked(False)

            all_terms_btn = QtWidgets.QCheckBox("Match all terms (ON) | Match any term (OFF)")
            options_layout.addWidget(all_terms_btn)
            all_terms_btn.setChecked(True)

            match_path_btn = QtWidgets.QCheckBox("Include object path while matching")
            options_layout.addWidget(match_path_btn)
            match_path_btn.setChecked(False)

            assign_textures_btn = QtWidgets.QPushButton("Assign Material")
            assign_textures_btn.clicked.connect(
                lambda x: ldf.assign_material_by_name(new_shader=shader_btn.text(),
                                                      matching_string=matching_string_btn.text(),
                                                      all_terms=all_terms_btn.isChecked(),
                                                      match_path=match_path_btn.isChecked(),
                                                      use_material=material_radio_btn.isChecked()))
            assign_textures_btn.setFixedHeight(25)
            options_layout.addWidget(assign_textures_btn)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class HDRICreator(Toolkit):

    def __init__(self):
        super().__init__(name='HDRI Creator',
                         tool_tip='Load HDRIs from CE prod directories.',
                         toolbox_function=self.HDRICreatorWidget)

    class HDRICreatorWidget(QtWidgets.QWidget):
        # Based off of the custom curve list model

        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.search_field = QtWidgets.QLineEdit()
            self.favourite_btn = QtWidgets.QPushButton('★')
            self.save_btn = QtWidgets.QPushButton('+')
            self.delete_btn = QtWidgets.QPushButton('✖')
            self.rename_btn = QtWidgets.QPushButton('Rename')
            self.image_label = QtWidgets.QLabel()
            self.image_index = 0  # Keep track of the currently displayed image
            self.images = []
            self.list_view = QtWidgets.QListView()
            self.default_path = os.path.join('Z:', '_neatHDRIcollection')
            self.default_sub_path = os.path.join('library', 'publish', 'texture', 'pub', 'v001')
            self.custom_path = ''
            self.dir_input = []
            self.source_model = HDRIListModel(self)
            self.proxy_model = CurveSortFilterProxyModel(self)
            self.proxy_model.setDynamicSortFilter(True)
            self.proxy_model.sort(0, QtCore.Qt.AscendingOrder)
            self.proxy_model.setFilterRole(0)
            self.proxy_model.setSourceModel(self.source_model)
            self.list_view.setModel(self.proxy_model)
            self.list_view.selectionModel().selectionChanged.connect(lambda: self.enable_edits())
            self.build_ui()

        def search_item(self):
            syntax = QtCore.QRegExp.RegExp
            case_sensitivity = (False and Qt.CaseSensitive or Qt.CaseInsensitive)
            reg_exp = QtCore.QRegExp(self.search_field.text(), case_sensitivity, syntax)
            self.proxy_model.setFilterRegExp(reg_exp)
            index = self.proxy_model.index(0, 0)
            self.list_view.selectionModel().setCurrentIndex(index, QtCore.QItemSelectionModel.ClearAndSelect)

        def save_hdri_data(self, favourite, hdri_path, hdri_name, option_name='CE_hdri_library_data'):
            # Serialize the dictionary to JSON string
            pack = [favourite, hdri_path, hdri_name]
            json_str = json.dumps(pack)

            # Store the JSON string in optionVar
            existing_data = cmds.optionVar(q=option_name)
            if existing_data:
                for i, json_pack in enumerate(existing_data):
                    hdri_data = json.loads(json_pack)
                    # If name/path of existing data matches new saved data, remove existing and add new data
                    if hdri_path in hdri_data[1]:
                        cmds.optionVar(rfa=(option_name, i))
            cmds.optionVar(sva=(option_name, json_str))

        def get_hdri_data(self, option_name):
            # Retrieve the JSON string from optionVar
            json_str = cmds.optionVar(q=option_name)

            # Deserialize JSON string to dictionary
            if json_str:
                return json.loads(json_str)
            else:
                return None

        def enable_edits(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, hdri_path, name = self.source_model.items[row]

                # Enable delete and edit buttons
                self.rename_btn.setEnabled(True)

        def rename_hdri(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, hdri_path, name = self.source_model.items[row]
                naming = cmds.promptDialog(
                    title='Nickname HDRI',
                    message='Enter Name:',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')

                if naming == 'OK':
                    new_name = cmds.promptDialog(query=True, text=True)
                    if new_name == "":
                        new_name = os.path.basename(hdri_path).split('.')[0]
                else:
                    return

                self.save_hdri_data(favourite, hdri_path, new_name)
                self.source_model.items[row] = (favourite, hdri_path, new_name)
                self.source_model.dataChanged.emit(index, index)

        def toggle_favourite(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, hdri_path, name = self.source_model.items[row]
                self.save_hdri_data(not favourite, hdri_path, name)
                self.source_model.items[row] = (not favourite, hdri_path, name)
                self.source_model.dataChanged.emit(index, index)

        def build_hdri(self):
            indexes = self.list_view.selectedIndexes()
            if indexes:
                index = self.proxy_model.mapToSource(indexes[0])
                row = index.row()
                favourite, hdri_path, hdri_name = self.source_model.items[row]
                print(hdri_path, hdri_name)

                ldf.build_hdri(hdri_path=os.path.join(self.default_path, hdri_path), name=hdri_name)

        def load_data(self):
            if os.path.exists(self.default_path):
                option_name = 'CE_hdri_library_data'
                existing_data = cmds.optionVar(q=option_name)
                items = []

                for hdri_path in glob(f'{self.default_path}/*.exr', recursive=True):
                    # Remove files from 'library/publish', as it causes duplicates and other issues
                    # if os.path.join('library', 'publish') in hdri_path:
                    #    continue
                    hdri_name = os.path.basename(hdri_path).split('.')[0]
                    favourite = False
                    if existing_data:
                        for i, json_pack in enumerate(existing_data):
                            hdri_data = json.loads(json_pack)
                            if hdri_path == hdri_data[1]:
                                favourite, _, hdri_name = hdri_data
                    items.append((favourite, hdri_path, hdri_name))
                '''
                custom_curves = os.listdir(self.custom_path)
                for hdri_path in custom_curves:
                    hdri_name = hdri_path.split('.crv')[0]
                    favourite = False
                    if favourite_list:
                        if hdri_name in favourite_list:
                            favourite = True
                    items.append((favourite, True, hdri_name))
                '''
                self.source_model.items = items

            else:
                cmds.warning(f"Could not find HDRI path to load from at: {self.default_path}")

        def build_ui(self):
            search_layout = QtWidgets.QGridLayout()

            self.search_field.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.search_field.textChanged.connect(lambda: self.search_item())
            self.search_field.returnPressed.connect(lambda: self.build_hdri())
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
            self.save_btn.setStyleSheet("font-size: 20pt;")
            options_layout.addWidget(self.save_btn, 0, 1)

            self.delete_btn.setEnabled(False)
            self.delete_btn.setStyleSheet("font-size: 20pt;")
            self.delete_btn.setFixedSize(btn_width, btn_height)
            options_layout.addWidget(self.delete_btn, 1, 0)

            self.rename_btn.setEnabled(False)
            self.rename_btn.clicked.connect(lambda: self.rename_hdri())
            self.rename_btn.setFixedSize(btn_width, btn_height)
            options_layout.addWidget(self.rename_btn, 1, 1)

            sidebar_layout.addLayout(image_layout)
            sidebar_layout.addLayout(options_layout)

            main_layout.addWidget(sidebar_container, 0, 0)
            main_layout.addWidget(self.list_view, 0, 1)

            self.source_model.layoutChanged.emit()

            button_layout = QtWidgets.QGridLayout()

            create_curve_btn = QtWidgets.QPushButton('Create/Update HDRI')
            create_curve_btn.clicked.connect(
                lambda: self.build_hdri())
            create_curve_btn.setFixedHeight(25)
            button_layout.addWidget(create_curve_btn, 0, 0)

            # Add to tool box layout
            self.tool_layout.addLayout(search_layout, 0, 0)
            self.tool_layout.addLayout(main_layout, 1, 0)
            self.tool_layout.addLayout(button_layout, 2, 0)

            self.load_data()


class Turntable(Toolkit):

    def __init__(self):
        super().__init__(name='Turntable', tool_tip='Create turntables',
                         toolbox_function=self.TurntableWidget)

    class TurntableWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.preset_options = QtWidgets.QComboBox()
            self.presets = {
                'Default': ([0, 'Y', 0], [2, 'Y', 0]),
                'Default 2.0': ([0, 'Y', 0], [1, 'Y', 1], [2, 'Y', 0]),
                'All Angles': ([0, 'Y', 0], [0, 'X', 0], [0, 'Z', 0], [1, 'Y', 1], [2, 'Y', 0]),
                'SSSPPPIIIIIIINNNNNNNNN': (
                    [0, 'Y', 0], [0, 'Y', 0], [0, 'Y', 0], [0, 'Y', 0], [0, 'Y', 0], [0, 'Y', 0], [0, 'Y', 0],
                    [0, 'Y', 0]),
            }
            self.rotate_options = ('TURNTABLE', 'CAMERA', 'SKYDOME')
            self.rotation_axes = {'X': ['+X', '-X'], 'Y': ['+Y', '-Y'], 'Z': ['+Z', '-Z']}
            self.input_fields = []
            self.input_data = {}
            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.buttons = []
            self.sequencer_data = {}
            self.sequencer_layout = QtWidgets.QHBoxLayout()
            self.drag = DragWidget(orientation=Qt.Orientation.Horizontal)
            self.build_ui()

        def update_sequencer_data(self, target, axis, direction, color, name):
            # sequence_length = self.sequencer_layout.count()
            # btn = DraggableButton(f"T{sequence_length}", self)
            # self.sequencer_layout.addWidget(btn)
            item = DragItem(name)
            data = json.dumps((target, axis, direction))
            item.set_data(data)
            item.setStyleSheet(f"background-color: rgb({color[0]},{color[1]},{color[2]});  border: 1px solid white;")
            self.drag.add_item(item)

        def load_custom_presets(self, option_name='CE_turntable_preset_data'):
            # Retrieve the JSON string from optionVar
            existing_data = cmds.optionVar(q=option_name)
            if existing_data:
                for i, json_pack in enumerate(existing_data):
                    preset_data = json.loads(json_pack)
                    if preset_data[0] in self.presets:
                        continue
                    self.presets[preset_data[0]] = preset_data[1]

        def save_preset(self, option_name='CE_turntable_preset_data'):
            turntable_data = self.drag.get_item_data()
            if turntable_data:
                naming = cmds.promptDialog(
                    title='Assign Name To Preset',
                    message='Enter Name:',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')

                if naming == 'OK':
                    preset_name = cmds.promptDialog(query=True, text=True)
                    # If name is None or name exists in existing default or custom presets
                    if preset_name == "" or preset_name in self.presets.keys():
                        cmds.warning('Name is invalid. Save aborted.')
                        return
                    unpacked_turntable_data = tuple(json.loads(x) for x in turntable_data)
                    self.presets[preset_name] = unpacked_turntable_data
                    self.preset_options.addItem(preset_name)

                    # Serialize the dictionary to JSON string
                    pack = [preset_name, unpacked_turntable_data]
                    json_str = json.dumps(pack)

                    # Get existing data, insert data, store the JSON string in optionVar
                    existing_data = cmds.optionVar(q=option_name)
                    if existing_data:
                        for i, json_pack in enumerate(existing_data):
                            preset_data = json.loads(json_pack)
                            # If name/path of existing data matches new saved data, remove existing and add new data
                            if preset_name in preset_data[0]:
                                cmds.optionVar(rfa=(option_name, i))
                    cmds.optionVar(sva=(option_name, json_str))
                    self.preset_options.setCurrentIndex(self.preset_options.count() - 1)
                else:
                    return

        def load_preset_in_sequencer(self, preset_steps):
            # Delete all contents of drag
            self.drag.clear_items()

            for step in preset_steps:
                color = [0, 0, 0]
                key = list(self.rotation_axes.keys()).index(step[1])
                color[key] = 50
                self.update_sequencer_data(target=step[0], axis=step[1], direction=step[2], color=color,
                                           name=f'{self.rotate_options[step[0]][0]}{self.rotation_axes[step[1]][step[2]]}')

        def delete_preset(self, preset, option_name='CE_turntable_preset_data'):
            existing_data = cmds.optionVar(q=option_name)
            if not existing_data:
                return
            preset_names = [json.loads(x)[0] for x in existing_data]
            if preset in preset_names:
                confirm = cmds.confirmDialog(title='Delete Preset',
                                             message=f"Are you sure you want to delete turntable preset: {preset}?",
                                             button=['Yes', 'No'],
                                             defaultButton='Yes', cancelButton='No', dismissString='No')

                if confirm == 'Yes':
                    for i, json_pack in enumerate(existing_data):
                        preset_data = json.loads(json_pack)
                        if preset_data[0] == preset:
                            # remove from optionVar data in Maya
                            cmds.optionVar(rfa=(option_name, i))
                            # remove from QComboBox
                            for x, option in enumerate(self.presets):
                                if option == preset:
                                    self.preset_options.removeItem(x)
                                    del self.presets[preset]

                                    return

        # https: // www.pythonguis.com / faq / pyside2 - drag - drop - widgets /
        def dragEnterEvent(self, event):
            if event.mimeData().hasText():
                event.accept()
            else:
                event.ignore()

        def dropEvent(self, event):
            mime_data = event.mimeData()
            if mime_data.hasText():
                text = mime_data.text()
                index = self.sequencer_layout.indexOf(event.target())
                source_index = self.buttons.index(self.sender())
                self.sequencer_layout.takeAt(index)
                self.sequencer_layout.insertWidget(index, self.buttons.pop(source_index))
                event.setDropAction(Qt.MoveAction)
                event.accept()
            else:
                event.ignore()

        def create_offset_groups(self):
            with UndoStack('create_offset_groups'):
                selected = cmds.ls(sl=1, l=1)
                for i, option in enumerate(self.rotate_options):
                    if not cmds.objExists(f'CE_{option}_OFFSET'):
                        color = [0.5, 0.5, 0.5]
                        color[i] = 1
                        grp = cmds.group(n=f'CE_{option}_OFFSET', em=1)
                        cmds.setAttr(f'{grp}.useOutlinerColor', 1)
                        cmds.setAttr(f'{grp}.outlinerColor', color[0], color[1], color[2], type='float3')
                        cmds.lockNode(grp, l=0, ln=1, ic=1)
                        lock_attributes([grp], ['translateX', 'translateY', 'translateZ'])

                # Lists to hold the split
                dome_list = []
                camera_list = []
                other_list = []

                # Loop through each string in the main list and check for substrings
                for item in selected:
                    item_type = get_object_type(item).lower()
                    # Don't nest CE groups, lol
                    if 'CE_' and '_OFFSET' in item:
                        continue
                    if 'dome' in item_type:
                        dome_list.append(item)
                    elif 'camera' in item_type:
                        camera_list.append(item)
                    else:
                        other_list.append(item)

                if dome_list:
                    cmds.parent(dome_list, f'CE_SKYDOME_OFFSET')
                if camera_list:
                    cmds.parent(camera_list, f'CE_CAMERA_OFFSET')
                if other_list:
                    cmds.parent(other_list, f'CE_TURNTABLE_OFFSET')

        def build_ui(self):

            top_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QVBoxLayout()

            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setStyleSheet("QScrollBar:horizontal {height: 10px;}")
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.verticalScrollBar().setEnabled(False)
            scroll_area.setFixedHeight(50)
            scroll_area.setWidgetResizable(True)  # Make the scroll area resizable
            scroll_area.setWidget(self.drag)  # Set the DragWidget as the scroll area's widget

            self.sequencer_layout.addWidget(scroll_area)

            # Add mirror options efficiently

            prepare_btn = QtWidgets.QPushButton('Setup Turntable Groups')
            prepare_btn.setFixedHeight(25)
            prepare_btn.clicked.connect(lambda: self.create_offset_groups())
            options_layout.addWidget(prepare_btn)

            main_layout = QtWidgets.QGridLayout()
            layout_index = 0
            for option_index, option in enumerate(self.rotate_options):

                # Create segmented btn layout
                btn_layout = QtWidgets.QGridLayout()
                label_layout = QtWidgets.QVBoxLayout()

                label_layout.addWidget(QtWidgets.QLabel(option))

                main_layout.addLayout(label_layout, layout_index, 0)
                layout_index += 1

                col_index = 0

                for axis_index, axis in enumerate(self.rotation_axes.keys()):
                    for direction_index, direction in enumerate(self.rotation_axes[axis]):
                        btn = QtWidgets.QPushButton(direction)

                        color = [0, 0, 0]
                        color[axis_index] = 50

                        btn.clicked.connect(
                            partial(self.update_sequencer_data, target=option_index, axis=axis,
                                    direction=direction_index, color=color, name=f'{option[0]}{direction}'))
                        btn.setFixedSize(25, 20)

                        btn.setStyleSheet(f"background-color: rgb({color[0]},{color[1]},{color[2]});")

                        btn_layout.addWidget(btn, 1, col_index)
                        col_index += 1

                main_layout.addLayout(btn_layout, layout_index, 0)
                layout_index += 1

            # Add default/custom presets
            self.load_custom_presets()
            self.preset_options.activated.connect(
                lambda: self.load_preset_in_sequencer(self.presets[self.preset_options.currentText()]))
            for preset in self.presets.keys():
                self.preset_options.addItem(preset)
            top_layout.addWidget(self.preset_options, 0, 0)

            save_btn = QtWidgets.QPushButton('+')
            save_btn.setFixedSize(25, 25)
            save_btn.setToolTip("Save Custom Turntable Preset")
            save_btn.clicked.connect(lambda: self.save_preset())
            top_layout.addWidget(save_btn, 0, 1)

            delete_btn = QtWidgets.QPushButton('-')
            delete_btn.setFixedSize(25, 25)
            delete_btn.setToolTip("Delete Custom Turntable Preset")
            delete_btn.clicked.connect(lambda: self.delete_preset(preset=self.preset_options.currentText()))
            top_layout.addWidget(delete_btn, 0, 2)

            create_turntable_btn = QtWidgets.QPushButton("Update Turntable Animation")
            create_turntable_btn.clicked.connect(
                lambda x: ldf.setup_turntable(anim_steps=self.drag.get_item_data()))
            create_turntable_btn.setFixedHeight(25)
            options_layout.addWidget(create_turntable_btn)

            # Show default turntable at start-up
            self.load_preset_in_sequencer(self.presets[self.preset_options.currentText()])

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)
            self.tool_layout.addLayout(main_layout, 2, 0)
            self.tool_layout.addLayout(self.sequencer_layout, 3, 0)