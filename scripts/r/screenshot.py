import sys
from datetime import datetime

from PIL import ImageGrab
from PyQt5 import QtCore, QtGui, QtWidgets


class RegionSelector(QtWidgets.QGraphicsView):
    def __init__(self, image_path: str):
        super().__init__()
        self.setWindowTitle("Select Region")
        self.scene = QtWidgets.QGraphicsScene(self)
        self.pixmap = QtGui.QPixmap(image_path)
        self.pixmap_item = self.scene.addPixmap(self.pixmap)
        self.setScene(self.scene)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.selection_rect_item = self.scene.addRect(
            QtCore.QRectF(),
            QtGui.QPen(QtGui.QColor("red"), 1),
            QtGui.QBrush(QtCore.Qt.NoBrush),
        )
        self.selection_rect_item.setZValue(1)
        self.selection_rect_item.setVisible(False)
        self.size_text_item = self.scene.addSimpleText("")
        self.size_text_item.setBrush(QtGui.QBrush(QtGui.QColor("red")))
        self.size_text_item.setZValue(2)
        self.size_text_item.setVisible(False)
        self.origin_scene = QtCore.QPointF()
        self.selection = None
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.setRenderHint(QtGui.QPainter.Antialiasing, False)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        delta = event.angleDelta().y() / 1200
        if not delta:
            return
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + delta))
        if new_zoom == self.zoom:
            return
        factor = new_zoom / self.zoom
        self.zoom = new_zoom
        self.scale(factor, factor)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.origin_scene = self.mapToScene(event.pos())
            self.selection_rect_item.setRect(
                QtCore.QRectF(self.origin_scene, self.origin_scene)
            )
            self.selection_rect_item.setVisible(True)
            self.size_text_item.setText("0 x 0")
            self.size_text_item.setPos(self.origin_scene)
            self.size_text_item.setVisible(True)
        super().mousePressEvent(event)

    def leaveEvent(self, event: QtCore.QEvent):
        self.size_text_item.setVisible(False)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if (
            event.buttons() & QtCore.Qt.LeftButton
            and self.selection_rect_item.isVisible()
        ):
            current_scene_pos = self.mapToScene(event.pos())
            rect = QtCore.QRectF(self.origin_scene, current_scene_pos).normalized()
            self.selection_rect_item.setRect(rect)
            left = int(rect.left())
            top = int(rect.top())
            width = int(rect.width())
            height = int(rect.height())
            self.size_text_item.setText(f"({left}, {top}, {width}, {height})")
            self.size_text_item.setPos(rect.topLeft())
            self.size_text_item.setVisible(True)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if (
            event.button() == QtCore.Qt.LeftButton
            and self.selection_rect_item.isVisible()
        ):
            rect = self.selection_rect_item.rect()
            if rect.width() > 0 and rect.height() > 0:
                self.selection = (
                    int(rect.left()),
                    int(rect.top()),
                    int(rect.right()),
                    int(rect.bottom()),
                )
        super().mouseReleaseEvent(event)

    def run(self, app: QtWidgets.QApplication):
        self.show()
        app.exec_()
        return self.selection


def capture_screenshot(output_path: str | None = None) -> str:
    if output_path is None:
        output_path = datetime.now().strftime("screenshot-%Y%m%d-%H%M%S.png")
    image = ImageGrab.grab()
    image.save(output_path)
    return output_path


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    path = capture_screenshot()
    print(path)
    selector = RegionSelector(path)
    selection = selector.run(app)
    if selection:
        print(f"Selection: {selection}")


if __name__ == "__main__":
    main()
