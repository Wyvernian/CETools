import os.path

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QMimeData, Signal
from PySide2.QtGui import QDrag, QPixmap

class CheckboxGroup(QtWidgets.QWidget):
    def __init__(self, name="CheckboxTitle"):
        super().__init__()

        self.button = None
        self.box = None
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setSpacing(10)
        self.options = {}
        self.boxes = []
        self.setLayout(self.layout)
        self.build_button(name)

    def build_button(self, name):
        self.button = QtWidgets.QPushButton(name)
        self.button.setFixedHeight(25)
        self.layout.addWidget(self.button)

    def add_options(self, new_options):
        self.options.update(new_options)

        for opt in self.options:
            v = self.options.get(opt)[0]
            n = self.options.get(opt)[1]
            box = QtWidgets.QCheckBox(n)
            box.setChecked(v)
            self.boxes.append(box)
            self.layout.addWidget(box)


def toggle_visibility(layout, button, widget):
    if button.isChecked():
        layout.removeWidget(widget)
        button.setEnabled(False)
        widget.hide()

    else:
        layout.addWidget(widget)
        button.setEnabled(True)
        widget.show()


def scale_buttons(layout, factor=0):
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if isinstance(widget, QtWidgets.QPushButton):
            size = str(widget.iconSize())
            size = size.split("(")[-1]
            size = int(size.split(",")[0])
            new_size = size + factor * 2
            if 50 <= new_size <= 100:
                widget.setIconSize(QtCore.QSize(new_size, new_size))


class DraggableButton(QtWidgets.QPushButton):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == 1:  # Left mouse button
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text())
        drag.setMimeData(mime_data)

        drag.exec_(Qt.MoveAction)


class DragItem(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(2, 2, 2, 2)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
        # Store data separately from display label, but use label for default.
        self.data = self.text()

    def set_data(self, data):
        self.data = data

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.deleteLater()


class DragWidget(QtWidgets.QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QtWidgets.QVBoxLayout()
        else:
            self.blayout = QtWidgets.QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()
        self.blayout.removeWidget(widget)

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                break

        else:
            # We aren't on the left hand/upper side of any widget,
            # so we're at the end. Increment 1 to insert after.
            n += 1

        self.blayout.insertWidget(n, widget)
        self.orderChanged.emit(self.get_item_data())

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data

    def clear_items(self):
        while self.blayout.count():
            item = self.blayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ToolButton(QtWidgets.QPushButton):
    right_clicked = QtCore.Signal()

    def __init__(self, name=None, tool_tip=None, icon_path=None):
        super().__init__()
        self.icon_path = icon_path
        self.name = name
        self.tool_tip = tool_tip
        self.build_ui()

    def build_ui(self):
        self.setDisabled(True)
        if self.icon_path is not None and os.path.exists(self.icon_path):
            self.setIcon(QtGui.QIcon(self.icon_path))
            self.setIconSize(QtCore.QSize(75, 75))
        else:
            label = QtWidgets.QLabel(self.name, self)
            label.setWordWrap(True)

            layout = QtWidgets.QHBoxLayout(self)
            layout.addWidget(label, 0, Qt.AlignCenter)
            self.setFixedSize(75, 75)

        if self.tool_tip:
            self.setToolTip(self.tool_tip)

    def enterEvent(self, event):
        self.setEnabled(True)

    def leaveEvent(self, event):
        self.setDisabled(True)


class ToolkitButton(ToolButton):
    right_clicked = QtCore.Signal()
    left_clicked = QtCore.Signal()
    double_clicked = QtCore.Signal()

    def __init__(self, name=None, tool_tip=None, icon_path=None):
        super().__init__(name, tool_tip, icon_path)

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.timeout)

        self.setCheckable(True)
        self.setChecked(False)
        self.is_double = False
        self.is_left_click = True

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if not self.timer.isActive():
                self.timer.start()

            self.is_left_click = False
            if event.button() == QtCore.Qt.LeftButton:
                self.is_left_click = True

            return True

        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.is_double = True
            return True

        return False

    def timeout(self):
        if self.is_double:
            self.double_clicked.emit()
        else:
            if self.is_left_click:
                self.left_clicked.emit()
                self.setChecked(not self.isChecked())
            else:
                self.right_clicked.emit()

        self.is_double = False

    def leaveEvent(self, event):
        if not self.isChecked():
            self.setDisabled(True)



class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class GroupBox(QtWidgets.QWidget):

    def __init__(self, name="dropdownName", is_open=False, vbox=None, container=None, layout=None, groupbox=None):
        super().__init__()
        self.name = name
        self.groupbox = groupbox
        self.layout = layout
        self.container = container
        self.is_open = is_open
        self.vbox = vbox
        self.build_ui()

    def build_ui(self):
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.groupbox = QtWidgets.QGroupBox(self.name)
        self.groupbox.setCheckable(True)
        self.groupbox.setFixedSize(265, 25)
        self.layout.addWidget(self.groupbox, 0, 0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.container = QtWidgets.QFrame(self.groupbox)
        self.layout.addWidget(self.container)

        self.vbox = QtWidgets.QVBoxLayout(self.container)
        self.layout.setSpacing(0)

        self.container.setLayout(self.vbox)

        self.groupbox.toggled.connect(self.container.setVisible)
        self.groupbox.setChecked(self.is_open)


class CurveListModel(QtCore.QAbstractListModel):
    FavouriteRole = Qt.UserRole + 1
    CustomRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3
    ImageRole = Qt.UserRole + 4

    def __init__(self, *args, items=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items or []
        self.star = QtGui.QColor('yellow')

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            _, _, text, _ = self.items[row]
            return text

        if role == CurveListModel.FavouriteRole:
            favourite, _, _, _ = self.items[row]
            return favourite

        if role == Qt.DecorationRole:
            favourite, custom, _, _ = self.items[row]
            if favourite:
                return self.star

        if role == Qt.ToolTipRole:
            favourite, custom, text, _ = self.items[row]
            if isinstance(custom, str):
                return custom

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)


class HDRIListModel(QtCore.QAbstractListModel):
    FavouriteRole = Qt.UserRole + 1
    CustomRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3

    def __init__(self, *args, items=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items or []
        self.star = QtGui.QColor('yellow')

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            _, _, text = self.items[row]
            return text

        if role == CurveListModel.FavouriteRole:
            favourite, _, _ = self.items[row]
            return favourite

        if role == Qt.DecorationRole:
            favourite, custom, _ = self.items[row]
            if favourite:
                return self.star

        if role == Qt.ToolTipRole:
            favourite, custom, text = self.items[row]
            if isinstance(custom, str):
                return custom

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)


class CurveSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__sortBy = None
        self.show_default = True
        self.show_custom = True

    def sortData(self, role_name, order):
        if order == Qt.InitialSortOrderRole:
            self.setSortRole(order)
            self.invalidate()
        else:
            roles = [key for key, value in self.roleNames().items() if value == role_name.encode()]
            if len(roles) > 0:
                self.setSortRole(roles[0])
                self.sort(0, order)

    def sortBy(self, attr):
        self.__sortBy = attr
        self.invalidate()  # invalidate helps
        self.sort(0, Qt.AscendingOrder)

    def lessThan(self, left, right):
        left_data = self.sourceModel().items[left.row()]
        right_data = self.sourceModel().items[right.row()]
        return (not left_data[0], left_data[2].lower()) < (not right_data[0], right_data[2].lower())
        # return QtCore.QString.localeAwareCompare(str(left_data), str(right_data)) > 0


class DraggableItemsModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super(DraggableItemsModel, self).__init__(parent)
        self._data = data
        self._headers = headers

    def addItem(self, item):
        self.beginInsertRows(self.index(0, 0), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self._headers[section])
        return QtCore.QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def sort(self, column, order=Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._data = sorted(self._data, key=lambda x: x[column], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()


class DraggableItemsView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(DraggableItemsView, self).__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dropEvent(self, event):
        if event.source() == self:
            super(DraggableItemsView, self).dropEvent(event)
        else:
            event.ignore()

    def headerClicked(self, logicalIndex):
        current_order = self.horizontalHeader().sortIndicatorOrder()
        self.model().sort(logicalIndex, current_order)
        self.horizontalHeader().setSortIndicator(logicalIndex, current_order)


class UVGridTableModel(QtCore.QAbstractTableModel):
    def __init__(self, rows, columns, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.columns = columns
        self._data = [['' for _ in range(self.rows)] for _ in range(self.columns)]

    def rowCount(self, parent=QModelIndex()):
        return self.rows

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.BackgroundRole:
            # Set background color based on the value in the model
            value = hash(self._data[index.row()][index.column()])
            color = QtGui.QColor(value % 256, (value // 256) % 256, (value // 256 // 256) % 256)
            return QtGui.QBrush(color)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(section)
            elif orientation == Qt.Vertical:
                # Display row numbers from bottom to top
                return str(section)
        return None
