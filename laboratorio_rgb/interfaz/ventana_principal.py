from __future__ import annotations

from pathlib import Path
from time import perf_counter

import numpy as np
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..nucleo.procesamiento_imagen import (
    AjusteCanal,
    AjusteReduccion,
    aplicar_intensidad_canal,
    calcular_histograma,
    cargar_imagen_rgb,
    convertir_a_blanco_negro,
    guardar_imagen,
    reducir_imagen_porcentaje,
    separar_canales_rgb,
    unir_canales_rgb,
)
from .componentes import (
    DATOS_CANAL,
    TarjetaControlCanal,
    TarjetaImagen,
    VentanaHistogramasAmpliados,
)
from .estilos import HOJA_ESTILOS
from .iconos import icono_cargar, icono_reiniciar


class VentanaLaboratorioRGB(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Laboratorio RGB")
        self.resize(1200, 820)

        self.ruta_cargada: Path | None = None
        self.imagen_original: np.ndarray | None = None
        self.canales_originales: dict[str, np.ndarray] = {}
        self.histogramas_originales: dict[str, np.ndarray] = {}
        self.histogramas_modificados: dict[str, np.ndarray] = {}
        self.canales_modificados: dict[str, np.ndarray] = {}
        self.imagen_reconstruida: np.ndarray | None = None
        self.imagen_reducida: np.ndarray | None = None
        self.imagen_binaria: np.ndarray | None = None
        self.ventana_histogramas_ampliados: VentanaHistogramasAmpliados | None = None
        self._procesamiento_suspendido = False

        self.temporizador_procesamiento = QTimer(self)
        self.temporizador_procesamiento.setInterval(30)
        self.temporizador_procesamiento.setSingleShot(True)
        self.temporizador_procesamiento.timeout.connect(self.procesar_flujo)

        self._construir_interfaz()
        self._reiniciar_controles_procesamiento()
        self.setStyleSheet(HOJA_ESTILOS)
        self._habilitar_interfaz(False)

    def _construir_interfaz(self) -> None:
        raiz = QWidget()
        disposicion_raiz = QVBoxLayout(raiz)
        disposicion_raiz.setContentsMargins(18, 18, 18, 18)
        disposicion_raiz.setSpacing(14)
        self.setCentralWidget(raiz)

        disposicion_raiz.addWidget(self._construir_barra_superior())

        self.pestanas = QTabWidget()
        self.pestanas.addTab(self._construir_pestana_resumen(), "Vista RGB")
        self.pestanas.addTab(self._construir_pestana_canales(), "Canales")
        self.pestanas.addTab(self._construir_pestana_salida(), "Salida")
        disposicion_raiz.addWidget(self.pestanas, 1)

    def _construir_barra_superior(self) -> QFrame:
        barra = QFrame()
        barra.setObjectName("barraSuperior")
        disposicion = QHBoxLayout(barra)
        disposicion.setContentsMargins(18, 16, 18, 16)
        disposicion.setSpacing(14)

        columna_titulo = QVBoxLayout()
        columna_titulo.setSpacing(3)
        titulo = QLabel("Laboratorio RGB")
        titulo.setObjectName("tituloAplicacion")
        subtitulo = QLabel("Separacion, ajuste y reconstruccion de canales")
        subtitulo.setObjectName("textoDiscreto")
        columna_titulo.addWidget(titulo)
        columna_titulo.addWidget(subtitulo)
        disposicion.addLayout(columna_titulo, 1)

        self.etiqueta_archivo = QLabel("Archivo: sin cargar")
        self.etiqueta_archivo.setObjectName("pastillaEstado")
        self.etiqueta_dimensiones = QLabel("Original: -")
        self.etiqueta_dimensiones.setObjectName("pastillaEstado")
        self.etiqueta_dimensiones_nuevas = QLabel("Nueva: -")
        self.etiqueta_dimensiones_nuevas.setObjectName("pastillaEstado")
        disposicion.addWidget(self.etiqueta_archivo)
        disposicion.addWidget(self.etiqueta_dimensiones)
        disposicion.addWidget(self.etiqueta_dimensiones_nuevas)

        self.boton_cargar = QPushButton("Cargar")
        self.boton_cargar.setObjectName("botonPrincipal")
        self.boton_cargar.setIcon(icono_cargar(self))
        self.boton_cargar.clicked.connect(self.cargar_imagen)
        disposicion.addWidget(self.boton_cargar)

        self.boton_reiniciar = QPushButton("Reiniciar")
        self.boton_reiniciar.setObjectName("botonLigero")
        self.boton_reiniciar.setIcon(icono_reiniciar(self))
        self.boton_reiniciar.clicked.connect(self.reiniciar_procesamiento)
        disposicion.addWidget(self.boton_reiniciar)

        self.boton_histogramas_ampliados = QPushButton("Ver histogramas ampliados")
        self.boton_histogramas_ampliados.setObjectName("botonSecundario")
        self.boton_histogramas_ampliados.clicked.connect(self.mostrar_histogramas_ampliados)
        disposicion.addWidget(self.boton_histogramas_ampliados)

        return barra

    def _construir_pestana_resumen(self) -> QWidget:
        pagina, disposicion = self._pagina_con_desplazamiento()

        cuadricula = QGridLayout()
        cuadricula.setContentsMargins(0, 0, 0, 0)
        cuadricula.setHorizontalSpacing(14)
        cuadricula.setVerticalSpacing(14)

        self.tarjeta_original = TarjetaImagen("Imagen original", alto_minimo=360)
        self.tarjeta_reconstruida = TarjetaImagen("RGB reconstruida", alto_minimo=360)
        cuadricula.addWidget(self.tarjeta_original, 0, 0)
        cuadricula.addWidget(self.tarjeta_reconstruida, 0, 1)
        disposicion.addLayout(cuadricula)

        self.etiqueta_estado = QLabel("Carga una imagen para iniciar el laboratorio.")
        self.etiqueta_estado.setObjectName("lineaEstado")
        self.etiqueta_estado.setWordWrap(True)
        disposicion.addWidget(self.etiqueta_estado)
        disposicion.addStretch(1)
        return pagina

    def _construir_pestana_canales(self) -> QWidget:
        pagina, disposicion = self._pagina_con_desplazamiento()

        self.tarjetas_canales_originales: dict[str, TarjetaImagen] = {}
        self.tarjetas_canales_modificados: dict[str, TarjetaImagen] = {}
        self.controles_canales: dict[str, TarjetaControlCanal] = {}

        for fila, clave_canal in enumerate(("R", "G", "B")):
            nombre_canal = DATOS_CANAL[clave_canal]["nombre"]
            tarjeta_original = TarjetaImagen(f"{nombre_canal} original", alto_minimo=180)
            tarjeta_control = TarjetaControlCanal(clave_canal)
            tarjeta_modificada = TarjetaImagen(f"{nombre_canal} ajustado", alto_minimo=180)

            tarjeta_control.ajustesCambiados.connect(self._al_cambiar_ajuste_canal)
            self.tarjetas_canales_originales[clave_canal] = tarjeta_original
            self.controles_canales[clave_canal] = tarjeta_control
            self.tarjetas_canales_modificados[clave_canal] = tarjeta_modificada

            fila_canal = QGridLayout()
            fila_canal.setContentsMargins(0, 0, 0, 0)
            fila_canal.setHorizontalSpacing(14)
            fila_canal.setVerticalSpacing(14)
            fila_canal.addWidget(tarjeta_original, 0, 0)
            fila_canal.addWidget(tarjeta_control, 0, 1)
            fila_canal.addWidget(tarjeta_modificada, 0, 2)
            fila_canal.setColumnStretch(0, 1)
            fila_canal.setColumnStretch(1, 2)
            fila_canal.setColumnStretch(2, 1)
            disposicion.addLayout(fila_canal)

            if fila < 2:
                disposicion.addSpacing(4)

        disposicion.addStretch(1)
        return pagina

    def _construir_pestana_salida(self) -> QWidget:
        pagina, disposicion = self._pagina_con_desplazamiento()

        banda = QFrame()
        banda.setObjectName("bandaControles")
        controles = QGridLayout(banda)
        controles.setContentsMargins(16, 14, 16, 14)
        controles.setHorizontalSpacing(16)
        controles.setVerticalSpacing(12)

        self.deslizador_reduccion, self.valor_reduccion = self._crear_fila_deslizador_salida(
            controles,
            0,
            "Reducir",
            10,
            100,
            50,
            self._al_cambiar_reduccion,
            sufijo="%",
        )
        self.deslizador_umbral, self.valor_umbral = self._crear_fila_deslizador_salida(
            controles,
            1,
            "Umbral B/N",
            0,
            255,
            128,
            self._al_cambiar_umbral,
        )

        fila_guardado = QHBoxLayout()
        fila_guardado.setSpacing(10)
        self.boton_guardar_color = QPushButton("Guardar RGB")
        self.boton_guardar_color.setObjectName("botonSecundario")
        self.boton_guardar_color.clicked.connect(lambda: self.guardar_variante("color"))
        self.boton_guardar_reducida = QPushButton("Guardar reducida")
        self.boton_guardar_reducida.setObjectName("botonSecundario")
        self.boton_guardar_reducida.clicked.connect(lambda: self.guardar_variante("reducida"))
        self.boton_guardar_binaria = QPushButton("Guardar B/N")
        self.boton_guardar_binaria.setObjectName("botonSecundario")
        self.boton_guardar_binaria.clicked.connect(lambda: self.guardar_variante("binaria"))
        fila_guardado.addWidget(self.boton_guardar_color)
        fila_guardado.addWidget(self.boton_guardar_reducida)
        fila_guardado.addWidget(self.boton_guardar_binaria)
        controles.addLayout(fila_guardado, 0, 3, 2, 1)
        disposicion.addWidget(banda)

        cuadricula_salida = QGridLayout()
        cuadricula_salida.setContentsMargins(0, 0, 0, 0)
        cuadricula_salida.setHorizontalSpacing(14)
        cuadricula_salida.setVerticalSpacing(14)
        self.tarjeta_reducida = TarjetaImagen("Imagen reducida", alto_minimo=340)
        self.tarjeta_binaria = TarjetaImagen("Blanco y negro", alto_minimo=340)
        cuadricula_salida.addWidget(self.tarjeta_reducida, 0, 0)
        cuadricula_salida.addWidget(self.tarjeta_binaria, 0, 1)
        disposicion.addLayout(cuadricula_salida)
        disposicion.addStretch(1)
        return pagina

    @staticmethod
    def _pagina_con_desplazamiento() -> tuple[QWidget, QVBoxLayout]:
        desplazamiento = QScrollArea()
        desplazamiento.setWidgetResizable(True)
        desplazamiento.setFrameShape(QFrame.NoFrame)

        contenido = QWidget()
        disposicion = QVBoxLayout(contenido)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(14)
        desplazamiento.setWidget(contenido)
        return desplazamiento, disposicion

    def _habilitar_interfaz(self, habilitada: bool) -> None:
        for elemento in (
            self.boton_reiniciar,
            self.boton_guardar_color,
            self.boton_guardar_reducida,
            self.boton_guardar_binaria,
            self.deslizador_umbral,
            self.deslizador_reduccion,
            self.boton_histogramas_ampliados,
        ):
            elemento.setEnabled(habilitada)

        for tarjeta_control in self.controles_canales.values():
            tarjeta_control.setEnabled(habilitada)

    def _al_cambiar_ajuste_canal(self, clave_canal: str, ajuste: AjusteCanal) -> None:
        del clave_canal, ajuste
        self.programar_procesamiento("Actualizando canales RGB...")

    def _al_cambiar_umbral(self, valor: int) -> None:
        del valor
        self.valor_umbral.setText(str(self.deslizador_umbral.value()))
        self.programar_procesamiento("Actualizando blanco y negro...")

    def _al_cambiar_reduccion(self, valor: int) -> None:
        del valor
        self.valor_reduccion.setText(f"{self.deslizador_reduccion.value()}%")
        self.programar_procesamiento("Actualizando reduccion...")

    def cargar_imagen(self) -> None:
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecciona una imagen",
            str(self.ruta_cargada.parent if self.ruta_cargada else Path.cwd()),
            "Imagenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if not ruta_archivo:
            return

        try:
            imagen = cargar_imagen_rgb(ruta_archivo)
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Error al cargar", str(error))
            return

        self.ruta_cargada = Path(ruta_archivo)
        self.imagen_original = imagen
        self.canales_originales = separar_canales_rgb(imagen)
        self.histogramas_originales = {
            clave_canal: calcular_histograma(canal)
            for clave_canal, canal in self.canales_originales.items()
        }
        self.histogramas_modificados = dict(self.histogramas_originales)

        self._procesamiento_suspendido = True
        for tarjeta_control in self.controles_canales.values():
            tarjeta_control.reiniciar_valores(emitir_cambio=False)
        self._reiniciar_controles_procesamiento()
        self._procesamiento_suspendido = False

        self._habilitar_interfaz(True)
        self.etiqueta_archivo.setText(f"Archivo: {self.ruta_cargada.name}")
        self.etiqueta_dimensiones.setText(f"Original: {imagen.shape[1]} x {imagen.shape[0]} px")
        self.tarjeta_original.mostrar_imagen(
            imagen,
            f"RGB original | {imagen.shape[1]} x {imagen.shape[0]} px",
        )

        for clave_canal, canal in self.canales_originales.items():
            self.tarjetas_canales_originales[clave_canal].mostrar_imagen(
                canal,
                f"Matriz {DATOS_CANAL[clave_canal]['nombre'].lower()} en escala de grises",
            )
            self.controles_canales[clave_canal].fijar_histogramas(
                self.histogramas_originales[clave_canal],
                self.histogramas_originales[clave_canal],
            )

        self.procesar_flujo()

    def reiniciar_procesamiento(self) -> None:
        if self.imagen_original is None:
            return

        self._procesamiento_suspendido = True
        for tarjeta_control in self.controles_canales.values():
            tarjeta_control.reiniciar_valores(emitir_cambio=False)
        self._reiniciar_controles_procesamiento()
        self._procesamiento_suspendido = False
        self.etiqueta_estado.setText("Ajustes reiniciados. Recalculando...")
        self.procesar_flujo()

    def programar_procesamiento(self, mensaje_estado: str) -> None:
        if self._procesamiento_suspendido or self.imagen_original is None:
            return
        self.etiqueta_estado.setText(mensaje_estado)
        self.temporizador_procesamiento.start()

    def procesar_flujo(self) -> None:
        if self.imagen_original is None:
            return

        inicio = perf_counter()
        self.canales_modificados = {}
        self.histogramas_modificados = {}

        for clave_canal, canal in self.canales_originales.items():
            ajuste = self.controles_canales[clave_canal].ajustes_actuales()
            canal_ajustado = aplicar_intensidad_canal(canal, ajuste)
            self.canales_modificados[clave_canal] = canal_ajustado

            histograma_ajustado = calcular_histograma(canal_ajustado)
            self.histogramas_modificados[clave_canal] = histograma_ajustado
            self.controles_canales[clave_canal].fijar_histogramas(
                self.histogramas_originales[clave_canal],
                histograma_ajustado,
            )
            self.controles_canales[clave_canal].fijar_informacion_intensidad(
                int(canal.min()),
                int(canal.max()),
                ajuste.porcentaje_intensidad,
                int(canal_ajustado.min()),
                int(canal_ajustado.max()),
            )
            self.tarjetas_canales_modificados[clave_canal].mostrar_imagen(
                canal_ajustado,
                self._descripcion_canal(canal, canal_ajustado, ajuste),
            )

        self.imagen_reconstruida = unir_canales_rgb(self.canales_modificados)
        self.imagen_reducida = reducir_imagen_porcentaje(
            self.imagen_reconstruida,
            self.ajuste_reduccion_actual(),
        )
        self.imagen_binaria = convertir_a_blanco_negro(
            self.imagen_reducida,
            self.deslizador_umbral.value(),
        )

        self.tarjeta_reconstruida.mostrar_imagen(
            self.imagen_reconstruida,
            "Canales R, G y B unidos despues de ajustar rangos tonales.",
        )
        self.tarjeta_reducida.mostrar_imagen(self.imagen_reducida, self._descripcion_reduccion())
        self.tarjeta_binaria.mostrar_imagen(
            self.imagen_binaria,
            f"Umbral = {self.deslizador_umbral.value()}",
        )

        if self.imagen_reducida is not None:
            self.etiqueta_dimensiones_nuevas.setText(
                f"Nueva: {self.imagen_reducida.shape[1]} x {self.imagen_reducida.shape[0]} px"
            )

        milisegundos = (perf_counter() - inicio) * 1000.0
        self.etiqueta_estado.setText(f"Pipeline actualizado en {milisegundos:.1f} ms.")
        self._actualizar_histogramas_ampliados()

    def mostrar_histogramas_ampliados(self) -> None:
        if self.imagen_original is None:
            QMessageBox.warning(self, "Sin datos", "Primero carga una imagen.")
            return

        if self.ventana_histogramas_ampliados is None:
            self.ventana_histogramas_ampliados = VentanaHistogramasAmpliados(self)

        self._actualizar_histogramas_ampliados()
        self.ventana_histogramas_ampliados.show()
        self.ventana_histogramas_ampliados.raise_()
        self.ventana_histogramas_ampliados.activateWindow()

    def _actualizar_histogramas_ampliados(self) -> None:
        if self.ventana_histogramas_ampliados is None or self.imagen_original is None:
            return
        self.ventana_histogramas_ampliados.actualizar_histogramas(
            self.histogramas_originales,
            self.histogramas_modificados or self.histogramas_originales,
            self._resumenes_histogramas_ampliados(),
        )

    def _resumenes_histogramas_ampliados(self) -> dict[str, tuple[int, int, int, int, int]]:
        resumenes: dict[str, tuple[int, int, int, int, int]] = {}
        for clave_canal, canal in self.canales_originales.items():
            canal_ajustado = self.canales_modificados.get(clave_canal, canal)
            ajuste = self.controles_canales[clave_canal].ajustes_actuales()
            resumenes[clave_canal] = (
                int(canal.min()),
                int(canal.max()),
                ajuste.porcentaje_intensidad,
                int(canal_ajustado.min()),
                int(canal_ajustado.max()),
            )
        return resumenes

    def guardar_variante(self, variante: str) -> None:
        imagenes = {
            "color": self.imagen_reconstruida,
            "reducida": self.imagen_reducida,
            "binaria": self.imagen_binaria,
        }
        imagen = imagenes[variante]
        if imagen is None:
            QMessageBox.warning(self, "Sin datos", "Primero carga una imagen.")
            return

        nombre_sugerido = self._nombre_guardado(variante)
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar resultado",
            str(nombre_sugerido),
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)",
        )
        if not ruta_archivo:
            return

        try:
            guardar_imagen(ruta_archivo, imagen)
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Error al guardar", str(error))
            return

        self.etiqueta_estado.setText(f"Imagen guardada en {Path(ruta_archivo).name}")

    def ajuste_reduccion_actual(self) -> AjusteReduccion:
        return AjusteReduccion(porcentaje_escala=self.deslizador_reduccion.value())

    def _reiniciar_controles_procesamiento(self) -> None:
        self.deslizador_umbral.blockSignals(True)
        self.deslizador_umbral.setValue(128)
        self.deslizador_umbral.blockSignals(False)
        self.valor_umbral.setText("128")

        self.deslizador_reduccion.blockSignals(True)
        self.deslizador_reduccion.setValue(50)
        self.deslizador_reduccion.blockSignals(False)
        self.valor_reduccion.setText("50%")
        self.etiqueta_dimensiones_nuevas.setText("Nueva: -")

    def _nombre_guardado(self, variante: str) -> Path:
        base = self.ruta_cargada.stem if self.ruta_cargada else "resultado"
        sufijo = {
            "color": "_rgb_modificada.png",
            "reducida": "_rgb_reducida.png",
            "binaria": "_bn_reducida.png",
        }[variante]
        carpeta = self.ruta_cargada.parent if self.ruta_cargada else Path.cwd()
        return carpeta / f"{base}{sufijo}"

    @staticmethod
    def _descripcion_canal(
        canal: np.ndarray,
        canal_ajustado: np.ndarray,
        ajuste: AjusteCanal,
    ) -> str:
        return (
            f"Contraste tonal {ajuste.porcentaje_intensidad}% | "
            f"Entrada {int(canal.min())}-{int(canal.max())} | "
            f"Salida {int(canal_ajustado.min())}-{int(canal_ajustado.max())}"
        )

    def _descripcion_reduccion(self) -> str:
        if self.imagen_reducida is None or self.imagen_reconstruida is None:
            return "Imagen reducida"
        return (
            f"{self.deslizador_reduccion.value()}% | "
            f"{self.imagen_reconstruida.shape[1]}x{self.imagen_reconstruida.shape[0]} px a "
            f"{self.imagen_reducida.shape[1]}x{self.imagen_reducida.shape[0]} px"
        )

    @staticmethod
    def _crear_fila_deslizador_salida(
        disposicion: QGridLayout,
        fila: int,
        texto_etiqueta: str,
        minimo: int,
        maximo: int,
        valor: int,
        funcion_cambio,
        sufijo: str = "",
    ) -> tuple[QSlider, QLabel]:
        etiqueta = QLabel(texto_etiqueta)
        etiqueta.setObjectName("etiquetaControl")
        deslizador = QSlider(Qt.Horizontal)
        deslizador.setRange(minimo, maximo)
        deslizador.setValue(valor)
        deslizador.valueChanged.connect(funcion_cambio)

        etiqueta_valor = QLabel(f"{valor}{sufijo}")
        etiqueta_valor.setObjectName("pastillaValor")
        etiqueta_valor.setAlignment(Qt.AlignCenter)
        etiqueta_valor.setMinimumWidth(58)

        disposicion.addWidget(etiqueta, fila, 0)
        disposicion.addWidget(deslizador, fila, 1)
        disposicion.addWidget(etiqueta_valor, fila, 2)
        return deslizador, etiqueta_valor
