HOJA_ESTILOS = """
QWidget {
    background: #f6f7f9;
    color: #1f2933;
    font-size: 10.5pt;
}

QMainWindow {
    background: #f6f7f9;
}

#barraSuperior {
    background: #243447;
    border: 1px solid #243447;
    border-radius: 6px;
}

#tarjeta, #bandaControles {
    background: #ffffff;
    border: 1px solid #d9e0e8;
    border-radius: 6px;
}

#tituloAplicacion {
    background: transparent;
    font-size: 20pt;
    font-weight: 800;
    color: #ffffff;
}

#tituloTarjeta {
    background: transparent;
    font-size: 12pt;
    font-weight: 700;
    color: #111827;
}

#textoDiscreto {
    background: transparent;
    color: #bfd0df;
}

#textoSecundario, #textoInformacion {
    background: transparent;
    color: #667085;
}

#lineaEstado {
    background: #edf7f4;
    border-left: 4px solid #1f9d8a;
    border-top: 1px solid #cdebe4;
    border-right: 1px solid #cdebe4;
    border-bottom: 1px solid #cdebe4;
    border-radius: 4px;
    color: #155e52;
    padding: 10px 12px;
}

#pastillaEstado {
    background: #314459;
    border: 1px solid #456179;
    border-radius: 4px;
    color: #e6eef5;
    padding: 8px 10px;
}

#visorImagen {
    background: #f9fafb;
    border: 1px solid #e4e7ec;
    border-radius: 4px;
    color: #6b7280;
    padding: 10px;
}

#botonPrincipal, #botonSecundario, #botonLigero {
    min-height: 38px;
    border-radius: 4px;
    padding: 0 16px;
    font-weight: 800;
}

#botonPrincipal {
    background: #fffbeb;
    color: #854d0e;
    border: 1px solid #f5c451;
}

#botonPrincipal:hover {
    background: #fef3c7;
    border-color: #eab308;
}

#botonPrincipal:pressed {
    background: #fde68a;
}

#botonSecundario {
    background: #f1f5f9;
    color: #243447;
    border: 1px solid #cbd5e1;
}

#botonSecundario:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
}

#botonSecundario:pressed {
    background: #cbd5e1;
}

#botonLigero {
    background: transparent;
    color: #dbe7f2;
    border: 1px solid #60788e;
}

#botonLigero:hover {
    background: #314459;
    border-color: #8da7bc;
}

#botonLigero:pressed {
    background: #1b2b3c;
}

#botonIcono {
    background: #f4f6f8;
    color: #344054;
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    padding: 0;
}

#botonIcono:hover {
    background: #e9eef3;
    border-color: #98a2b3;
}

#botonIcono:pressed {
    background: #d9e0e8;
}

#etiquetaControl {
    background: transparent;
    min-width: 92px;
    color: #344054;
    font-weight: 800;
}

#pastillaValor {
    background: #fef3c7;
    border: 1px solid #f5c451;
    border-radius: 4px;
    color: #7c2d12;
    font-weight: 800;
    padding: 4px 8px;
}

QTabWidget::pane {
    border: 1px solid #d9e0e8;
    border-radius: 6px;
    background: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background: #e7ebf0;
    border: 1px solid #d0d7df;
    padding: 9px 22px;
    margin-right: 2px;
    color: #475467;
    font-weight: 800;
}

QTabBar::tab:first {
    border-top-left-radius: 6px;
}

QTabBar::tab:last {
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #243447;
    color: #ffffff;
    border-color: #243447;
}

QTabBar::tab:hover:!selected {
    background: #f3f5f7;
    color: #1f2933;
}

QSlider::groove:horizontal {
    height: 8px;
    border-radius: 0px;
    background: #dde3ea;
}

QSlider::sub-page:horizontal {
    background: #1f9d8a;
    border-radius: 0px;
}

QSlider::handle:horizontal {
    width: 12px;
    margin: -7px 0;
    border-radius: 2px;
    background: #243447;
    border: 2px solid #ffffff;
}

QSlider::handle:horizontal:hover {
    background: #f59e0b;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #edf0f4;
    width: 14px;
    margin: 0;
    border: none;
}

QScrollBar::handle:vertical {
    background: #9aa8b7;
    min-height: 32px;
    border: 3px solid #edf0f4;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #667085;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: #edf0f4;
    height: 14px;
    margin: 0;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #9aa8b7;
    min-width: 32px;
    border: 3px solid #edf0f4;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background: #667085;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}
"""
