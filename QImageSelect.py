from typing import Optional, Union

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRubberBand,
    QVBoxLayout,
    QWidget,
)


class QImageSelect(QDialog):
    """Image Cropper Dialog.

    Parameters
    ----------
    title : str
        Dialog title
    image : Union[str, QPixmap]
        Image path or qpixmap
    maximum_size : QSize
        Maximum dialog size
    parent : QWidget, optional
        Parent widget, by default None

    Returns
    -------
    QPixmap
        Cropped qpixmap
    """

    ROTATE_BTN_MAX_WIDTH = 35

    @classmethod
    def spawn(
        cls,
        title: str,
        image: Union[str, QPixmap],
        maximum_size: QSize,
        parent: Optional[QWidget] = None,
        keep_original_size: bool = True,
    ) -> Optional[QPixmap]:
        """Create instance of QImageSelect, execute it and return cropped qpixmap

        Parameters
        ----------
        title : str
            Dialog title.
        image : Union[str, QPixmap]
            Image path or qpixmap.
        maximum_size : QSize
            Maximum dialog size.
        parent : QWidget, optional
            Parent widget, by default None.
        keep_original_size : bool
            Whether to keep original image resolution, defaults true.

        Returns
        -------
        QPixmap
            Cropped qpixmap
        """

        dialog = cls(title=title, image=image, maximum_size=maximum_size, parent=parent)
        if not dialog.exec():
            return None
        selection = dialog.selection
        ratio = dialog.ratio if keep_original_size else 1.0
        return dialog.pixmap.copy(
            QRect(selection.topLeft() * ratio, selection.bottomRight() * ratio)
        )

    @property
    def transform(self) -> QTransform:
        return QTransform().rotate(self._angle)

    @property
    def selection(self) -> QRect:
        return self.view.selected_rect or self.view.rect()

    @property
    def ratio(self) -> float:
        return self.pixmap.width() / self.view.width()

    @property
    def pixmap(self) -> QPixmap:
        return self._pixmap.transformed(self.transform)

    def __init__(
        self,
        title: str,
        image: Union[str, QPixmap],
        maximum_size: QSize,
        parent: Optional[QWidget] = None,
    ):
        """Create instance of QImageSelect."""

        self._max_size = maximum_size
        self._pixmap = QPixmap(image)
        self._angle = 0
        super(QImageSelect, self).__init__(parent)
        self.initUI(title)

    def initUI(self, title: str):
        """Initialize UI."""

        self.setWindowTitle(title)

        self.bg_layout = QVBoxLayout(self)
        self.bg_layout.setContentsMargins(0, 0, 0, 0)
        self.view = self.QImageLabel(self)
        self.btn_container = QWidget(self)
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_ok = QPushButton("OK", self.btn_container)
        self.btn_rotate = QPushButton("↻", self.btn_container)
        self.btn_rotate.setMaximumWidth(self.ROTATE_BTN_MAX_WIDTH)
        self.btn_layout.addWidget(self.btn_rotate)
        self.btn_layout.addWidget(self.btn_ok)
        self.bg_layout.addWidget(self.btn_container)
        self.bg_layout.addWidget(self.view)

        self.adjust_image(0)

        self.setMouseTracking(True)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_rotate.clicked.connect(lambda: self.adjust_image())

    def adjust_image(self, rotate_degree: int = 90):
        """Rotate image and resize dialog."""

        self._angle += rotate_degree
        pixmap = self._pixmap.scaled(
            self._max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ).transformed(self.transform, Qt.TransformationMode.SmoothTransformation)
        width = pixmap.width()
        hight = pixmap.height()
        self.setFixedSize(width, hight + 45)
        self.view.setPixmap(pixmap)

    class QImageLabel(QLabel):
        """Customized QLabel with rubberband support.

        Parameters
        ----------
        parent : QWidget
            Parent widget
        """

        def __init__(self, parent: QWidget):
            """Create instance of QImageLabel."""

            super().__init__(parent=parent)
            self.rubberband = QRubberBand(QRubberBand.Shape.Rectangle, self)
            self.selected_rect = QRect()

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.origin = event.pos()
                self.rubberband.setGeometry(QRect(self.origin, QSize()))
                self.rubberband.show()

        def mouseMoveEvent(self, event):
            if self.rubberband.isVisible():
                self.rubberband.setGeometry(
                    QRect(self.origin, event.pos()).normalized() & self.rect()
                )

        def mouseReleaseEvent(self, event):
            if (
                self.rubberband.isVisible()
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self.selected_rect = self.rubberband.geometry().normalized()
