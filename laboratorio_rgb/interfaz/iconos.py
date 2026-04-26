from __future__ import annotations

from PySide6.QtWidgets import QStyle, QWidget


def icono_cargar(widget: QWidget):
    return widget.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)


def icono_reiniciar(widget: QWidget):
    return widget.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)


def icono_reiniciar_canal(widget: QWidget):
    return widget.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
