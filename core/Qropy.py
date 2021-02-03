from typing import Optional, List
from PIL import Image, ImageQt
from PySide2.QtWidgets import QApplication, QWidget, QFrame
from PySide2.QtCore import Qt, QRect, QPoint, Signal, QSize
from PySide2.QtGui import QPainter, QPen, QImage
from PySide2.QtGui import QMouseEvent, QPaintEvent, QResizeEvent, QKeyEvent


class SelectoRect(QWidget):
    """ Selection Rect On Any Widget """

    HANDLE_SIZE = 15  # Constent;
    LINE_WIDTH = 1   # Constent;

    # Object Local Vars.
    __sRect = QRect(0, 0, 0, 0)  # Selection Rect;
    __image: Optional[QImage] = None  # Optional;
    __sRect_last_xy = QPoint(0, 0)
    __is_selection_enabled = False
    __is_resize_enable = False
    __is_move_enable = False
    __ratio = 0.0

    # Painter Objects;
    __pen: QPen = QPen(Qt.black, LINE_WIDTH, Qt.DashLine)
    __painter: QPainter = QPainter()

    # Signals;
    onDoubleClick_r = Signal(QRect)
    onDoubleClick_l = Signal(QRect)

    def init(self, parent: QWidget = None, ratio: float = 0, image: QImage = None):
        """ Init Before Use """
        if parent:
            self.setParent(parent)
        if image:
            self.__image = image
        self.__ratio = ratio
        self.setMouseTracking(True)

    @property
    def selection(self) -> QRect:
        """ Get Current Selection Area"""
        if self.__image:
            fx = self.__image.width() / self.width()  # type: ignore
            fy = self.__image.height() / self.height()  # type: ignore
            x = self.__sRect.x() * fx
            y = self.__sRect.y() * fy
            w = self.__sRect.width() * fx
            h = self.__sRect.height() * fy
            return QRect(x, y, w, h)  # type: ignore
        else:
            return self.__sRect

    @property
    def getMoveHandle(self) -> QRect:
        """ Get Selection Move Handle Rect  """
        point = self.__sRect.center()
        x = round(point.x() - (self.HANDLE_SIZE/2))
        y = round(point.y() - (self.HANDLE_SIZE/2))
        return QRect(x, y, self.HANDLE_SIZE, self.HANDLE_SIZE)

    @property
    def getResizeHandle(self) -> QRect:
        """ Get Selection Resize handle rect """
        point = self.__sRect.bottomRight()
        x = round(point.x() - (self.HANDLE_SIZE/2))
        y = round(point.y() - (self.HANDLE_SIZE/2))
        return QRect(x, y, self.HANDLE_SIZE, self.HANDLE_SIZE)

    def setImage(self, image: QImage):
        self.__image = image
        self.update()

    def adjustAspectRatio(self):
        """ Event: Don't Invoke This Method Manually """
        if self.__image:
            # -> Get Ratio Of Width;
            w = (self.__image.width() / self.__image.height()) * self.height()

            if w <= self.parentWidget().width():
                self.setFixedWidth(w)
                is_width_changed = True
            else:
                h = (self.__image.height() / self.__image.width()) * self.width()
                self.setFixedHeight(h)

            self.update()

    def resizeEvent(self, event: QResizeEvent):
        """ Event: Don't Invoke This Method Manually """
        self.__sRect.setRect(0, 0, 0, 0)

    def mousePressEvent(self, event: QMouseEvent):
        """ Event: Don't Invoke This Method Manually """
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.LeftButton:
            # -> Store Last Rect's X,Y Pos;
            self.__sRect_last_xy = self.__sRect.topLeft()
            """```````````````````````````````````````"""
            if self.getMoveHandle.contains(event.x(), event.y()):
                self.__is_move_enable = True
                # self.setCursor( Qt.SizeAllCursor )
            elif self.getResizeHandle.contains(event.x(), event.y()):
                self.__is_resize_enable = True
                # self.setCursor( Qt.SizeFDiagCursor )
            else:
                self.__is_selection_enabled = True
                self.__sRect.setTopLeft(event.pos())
                # self.setCursor( Qt.SizeFDiagCursor )

    def mouseReleaseEvent(self, event: QMouseEvent):
        """ Event: Don't Invoke This Method Manually """
        if event.button() == Qt.MouseButton.LeftButton:
            self.__is_selection_enabled = False
            self.__is_resize_enable = False
            self.__is_move_enable = False
            # -> Resotre Cursor;
            # self.setCursor( Qt.ArrowCursor )

            """`````````````````````````````````````"""
            mouse_moved_amount_x = self.__sRect.x() - event.x()
            mouse_moved_amount_y = self.__sRect.y() - event.y()
            if mouse_moved_amount_x == 0 or mouse_moved_amount_y == 0:
                # -> Restore sRect's X,Y Position;
                self.__sRect.setTopLeft(self.__sRect_last_xy)

    def mouseMoveEvent(self, event: QMouseEvent):
        """ Event: Don't Invoke This Method Manually """
        if self.__is_selection_enabled or self.__is_resize_enable:
            if not self.__ratio:
                # -> Set Selection Rect's End Position;
                self.__sRect.setBottomRight(event.pos())
            else:
                # -> Calclulate & Apply Ratio;
                #-----------[ Can Be Improve ]-----------#
                width_as_ratio = round(
                    self.__sRect.height() * self.__ratio)  # Ratio Appled;
                self.__sRect.setWidth(width_as_ratio)
                self.__sRect.setBottom(event.y())

        elif self.__is_move_enable:
            # -> Move Selection Rect;
            self.__sRect.moveCenter(event.pos())

        """``````````````````````````````````````````````````"""
        # -> Cursor Pointer Logic;
        if self.getResizeHandle.contains(event.x(), event.y()):
            self.setCursor(Qt.SizeFDiagCursor)
        elif self.getMoveHandle.contains(event.x(), event.y()):
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        # -> Update Widget;
        self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """ Event: Don't Invoke This Method Manually """
        if event.button() == Qt.MouseButton.LeftButton:
            self.onDoubleClick_l.emit(self.selection)  # type: ignore
        elif event.button() == Qt.MouseButton.RightButton:
            self.onDoubleClick_r.emit(self.selection)  # type: ignore

    def paintEvent(self, event: QPaintEvent):
        """ Event: Don't Invoke This Method Manually """
        self.__painter.begin(self)

        if self.__image:
            self.__painter.drawImage(
                self.rect(), self.__image, self.__image.rect())

        if self.__sRect.isValid():
            self.__painter.setPen(self.__pen)
            self.__painter.drawRect(self.__sRect)  # Draw Selection Rect;
            self.__painter.setPen(QPen(Qt.red, self.LINE_WIDTH, Qt.DashLine))
            self.__painter.drawRect(self.getMoveHandle)
            self.__painter.drawRect(self.getResizeHandle)

        self.__painter.end()  # Paint Must End To Avoid Memory Leack;


class ImageCropperQt(QFrame):
    """ Pil Image Cropper """
    __image: Optional[Image.Image]
    __history: List[QRect]
    __render_image: QImage
    __tool: SelectoRect

    result = Signal(Image.Image)

    def __init__(self, image: Image.Image, min_height=360):
        super().__init__()  # Requred;
        """^^^^^^^^^^^^^^^^^^^^^^^"""
        self.__image = image
        self.__history = []
        self.__render_image = ImageQt.ImageQt(self.__image)
        self.__tool = SelectoRect()
        self.__tool.init(self, ratio=3/3.73)
        # Setup
        self.setMinimumHeight(min_height)
        self.setFocus(Qt.MouseFocusReason)
        self.__tool.setImage(self.__render_image)
        self.__tool.onDoubleClick_r.connect(self._crop)  # type: ignore
        self.__tool.onDoubleClick_l.connect(self._finalCrop)  # type: ignore

    def _crop(self, rect: QRect):
        """ Crop View Selection Area """
        if rect.isValid():
            self.__history.append(rect)
            self.__render_image = self.__render_image.copy(rect)
            self.__tool.setImage(self.__render_image)
            self.adjustAspectRatio()

    def _finalCrop(self, rect: QRect):
        """ Crop Selection Area """
        if self.__image:
            image = self.__image
            if self.__history:
                for r in self.__history:
                    image = image.crop(r.getCoords())

            if rect.isValid():
                self.__history.append(rect)
                image = image.crop(rect.getCoords())

            self.__history = []
            self.__image = image
            self.__render_image = ImageQt.ImageQt(self.__image)
            self.__tool.setImage(self.__render_image)
            self.result.emit(image)  # type: ignore

    def undo(self):
        """ Undo Crop View """
        if self.__image and self.__history:
            # Get Original Pil to Qt Image;
            image = ImageQt.ImageQt(self.__image)
            self.__history.pop()
            if self.__history:
                for r in self.__history:
                    image = image.copy(r)

            self.__render_image = image
            self.__tool.setImage(self.__render_image)
            self.adjustAspectRatio()

    def adjustAspectRatio(self):
        """ Adjust Window's Aspect Ratio As Image , Height Will Be Constent """
        screen_size = QApplication.desktop().screenGeometry()
        w = round((self.__render_image.width() /
                   self.__render_image.height()) * self.height())
        if w < screen_size.width():
            self.setFixedWidth(w)
        else:
            h = round((self.__render_image.height() /
                       self.__render_image.width()) * self.width())
            self.setMinimumHeight(h)

        self.__tool.setFixedSize(self.size())
        self.update()

    def resizeEvent(self, e):
        """ Event: Don't Invoke This Method Manually """
        self.adjustAspectRatio()

    def keyPressEvent(self, e: QKeyEvent):
        """ Event: Don't Invoke This Method Manually """
        if e.key() == Qt.Key_Backspace:
            self.undo()

    def closeEvent(self, e):
        """ Event: Don't Invoke This Method Manually """
        self.result.emit(self.__image)  # type: ignore


# Test Run.
if __name__ == '__main__':
    TEST_IMAGE_PATH = 'C:\\Users\\jahid\\Documents\\IMG_20210130_160115.jpg'
    from PySide2.QtWidgets import QApplication
    app = QApplication()

    res = input('1. Test SelectoRect \n2. Test ImageCropperQt \n>>> ')
    if res == '1':
        window = SelectoRect()
        window.init()
        window.setImage(QImage(TEST_IMAGE_PATH))
        window.show()
    elif res == '2':
        window = ImageCropperQt(Image.open(TEST_IMAGE_PATH))
        window.show()

    app.exec_()
