from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from .interfaz.ventana_principal import VentanaLaboratorioRGB


def iniciar() -> int:
    aplicacion = QApplication.instance() or QApplication([])
    configurar_fuente(aplicacion)
    ventana = VentanaLaboratorioRGB()
    ventana.show()
    return aplicacion.exec()


def configurar_fuente(aplicacion: QApplication) -> None:
    ruta_fuente = Path(__file__).resolve().parents[1] / "Onest" / "Onest-VariableFont_wght.ttf"
    if ruta_fuente.exists():
        identificador_fuente = QFontDatabase.addApplicationFont(str(ruta_fuente))
        if identificador_fuente != -1:
            familias = QFontDatabase.applicationFontFamilies(identificador_fuente)
            if familias:
                aplicacion.setFont(QFont(familias[0], 10))
                return
    aplicacion.setFont(QFont("Arial", 10))
