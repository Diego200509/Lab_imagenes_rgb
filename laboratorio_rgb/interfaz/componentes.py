from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..nucleo.procesamiento_imagen import AjusteCanal
from .iconos import icono_reiniciar_canal


DATOS_CANAL = {
    "R": {"nombre": "Rojo", "color": "#ef4444"},
    "G": {"nombre": "Verde", "color": "#22c55e"},
    "B": {"nombre": "Azul", "color": "#3b82f6"},
}


def arreglo_a_pixmap(imagen: np.ndarray) -> QPixmap:
    arreglo = np.ascontiguousarray(imagen)
    if arreglo.ndim == 2:
        alto, ancho = arreglo.shape
        imagen_qt = QImage(
            arreglo.data,
            ancho,
            alto,
            arreglo.strides[0],
            QImage.Format.Format_Grayscale8,
        )
        return QPixmap.fromImage(imagen_qt.copy())

    alto, ancho, _ = arreglo.shape
    imagen_qt = QImage(
        arreglo.data,
        ancho,
        alto,
        arreglo.strides[0],
        QImage.Format.Format_RGB888,
    )
    return QPixmap.fromImage(imagen_qt.copy())


class EtiquetaImagenProporcional(QLabel):
    def __init__(self, texto_vacio: str = "Sin imagen") -> None:
        super().__init__(texto_vacio)
        self._pixmap_original: QPixmap | None = None
        self._texto_vacio = texto_vacio
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(180)
        self.setObjectName("visorImagen")

    def fijar_pixmap(self, pixmap: QPixmap | None) -> None:
        self._pixmap_original = pixmap
        if pixmap is None:
            self.setText(self._texto_vacio)
            self.setPixmap(QPixmap())
            return

        self.setText("")
        self._aplicar_escala()

    def resizeEvent(self, evento) -> None:  # noqa: N802
        super().resizeEvent(evento)
        self._aplicar_escala()

    def _aplicar_escala(self) -> None:
        if self._pixmap_original is None:
            return

        if (
            self._pixmap_original.width() <= self.width()
            and self._pixmap_original.height() <= self.height()
        ):
            self.setPixmap(self._pixmap_original)
            return

        pixmap_escalado = self._pixmap_original.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.setPixmap(pixmap_escalado)


class TarjetaImagen(QFrame):
    def __init__(self, titulo: str, alto_minimo: int = 260) -> None:
        super().__init__()
        self.setObjectName("tarjeta")

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(16, 16, 16, 16)
        disposicion.setSpacing(10)

        self.etiqueta_titulo = QLabel(titulo)
        self.etiqueta_titulo.setObjectName("tituloTarjeta")
        disposicion.addWidget(self.etiqueta_titulo)

        self.etiqueta_imagen = EtiquetaImagenProporcional()
        self.etiqueta_imagen.setMinimumHeight(alto_minimo)
        disposicion.addWidget(self.etiqueta_imagen, 1)

        self.etiqueta_descripcion = QLabel("Esperando imagen")
        self.etiqueta_descripcion.setObjectName("textoSecundario")
        self.etiqueta_descripcion.setWordWrap(True)
        disposicion.addWidget(self.etiqueta_descripcion)

    def mostrar_imagen(self, imagen: np.ndarray | None, descripcion: str = "") -> None:
        pixmap = None if imagen is None else arreglo_a_pixmap(imagen)
        self.etiqueta_imagen.fijar_pixmap(pixmap)
        self.etiqueta_descripcion.setText(descripcion or " ")


class VistaHistograma(QWidget):
    def __init__(self, color_acento: str) -> None:
        super().__init__()
        self.setMinimumHeight(210)
        self._color_acento = QColor(color_acento)
        self._histograma_base = np.zeros(256, dtype=np.float32)
        self._histograma_ajustado = np.zeros(256, dtype=np.float32)
        self._vista_minima = 0.0
        self._vista_maxima = 255.0
        self._conteo_minimo = 0.0
        self._conteo_maximo: float | None = None
        self._seleccion_inicio: QPointF | None = None
        self._seleccion_fin: QPointF | None = None
        self._arrastre_inicio: QPointF | None = None
        self._arrastre_minimo = 0.0
        self._arrastre_maximo = 255.0
        self._arrastre_conteo_minimo = 0.0
        self._arrastre_conteo_maximo = 1.0
        self.setMouseTracking(True)
        self.setToolTip(
            "Arrastra un rectangulo para ampliar. Rueda para zoom, boton derecho "
            "para mover y doble clic para reiniciar."
        )

    def fijar_histogramas(
        self,
        histograma_base: np.ndarray,
        histograma_ajustado: np.ndarray,
    ) -> None:
        self._histograma_base = histograma_base
        self._histograma_ajustado = histograma_ajustado
        self.update()

    def reiniciar_vista(self) -> None:
        self._vista_minima = 0.0
        self._vista_maxima = 255.0
        self._conteo_minimo = 0.0
        self._conteo_maximo = None
        self._seleccion_inicio = None
        self._seleccion_fin = None
        self.update()

    def paintEvent(self, evento) -> None:  # noqa: N802
        del evento
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)

        rectangulo_externo = self.rect().adjusted(4, 4, -4, -4)
        rectangulo_grafico = self._rectangulo_grafico()
        pintor.fillRect(rectangulo_externo, QColor("#111827"))

        conteo_minimo, conteo_maximo = self._rango_conteo_visible()
        self._dibujar_histograma(
            pintor,
            rectangulo_grafico,
            self._histograma_base,
            QColor("#9ca3af"),
            conteo_minimo,
            conteo_maximo,
            0.35,
        )
        self._dibujar_histograma(
            pintor,
            rectangulo_grafico,
            self._histograma_ajustado,
            self._color_acento,
            conteo_minimo,
            conteo_maximo,
            0.95,
        )
        self._dibujar_etiquetas_ejes(pintor, rectangulo_grafico, conteo_minimo, conteo_maximo)
        self._dibujar_seleccion(pintor, rectangulo_grafico)

    def mousePressEvent(self, evento) -> None:  # noqa: N802
        rectangulo_grafico = self._rectangulo_grafico()
        posicion = evento.position()
        if not rectangulo_grafico.contains(posicion):
            return

        if evento.button() == Qt.MouseButton.LeftButton:
            punto = self._punto_limitado(posicion, rectangulo_grafico)
            self._seleccion_inicio = punto
            self._seleccion_fin = punto
            self.update()
            return

        if evento.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            conteo_minimo, conteo_maximo = self._rango_conteo_visible()
            self._arrastre_inicio = posicion
            self._arrastre_minimo = self._vista_minima
            self._arrastre_maximo = self._vista_maxima
            self._arrastre_conteo_minimo = conteo_minimo
            self._arrastre_conteo_maximo = conteo_maximo

    def mouseMoveEvent(self, evento) -> None:  # noqa: N802
        rectangulo_grafico = self._rectangulo_grafico()

        if self._seleccion_inicio is not None:
            self._seleccion_fin = self._punto_limitado(evento.position(), rectangulo_grafico)
            self.update()
            return

        if self._arrastre_inicio is not None and evento.buttons() & (
            Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton
        ):
            rango_valores = self._arrastre_maximo - self._arrastre_minimo
            rango_conteo = self._arrastre_conteo_maximo - self._arrastre_conteo_minimo
            if rango_valores >= 255.0 and self._conteo_maximo is None:
                return
            delta_x = evento.position().x() - self._arrastre_inicio.x()
            delta_y = evento.position().y() - self._arrastre_inicio.y()
            delta_valor = delta_x / max(rectangulo_grafico.width(), 1.0) * rango_valores
            delta_conteo = delta_y / max(rectangulo_grafico.height(), 1.0) * rango_conteo
            self._fijar_rango_visible(
                self._arrastre_minimo - delta_valor,
                self._arrastre_maximo - delta_valor,
                self._arrastre_conteo_minimo + delta_conteo,
                self._arrastre_conteo_maximo + delta_conteo,
            )

    def mouseReleaseEvent(self, evento) -> None:  # noqa: N802
        if evento.button() == Qt.MouseButton.LeftButton and self._seleccion_inicio is not None:
            rectangulo_grafico = self._rectangulo_grafico()
            seleccion = self._rectangulo_seleccion(rectangulo_grafico)
            self._seleccion_inicio = None
            self._seleccion_fin = None

            if seleccion.width() >= 6.0 and seleccion.height() >= 6.0:
                valor_inicio = self._x_a_valor(seleccion.left(), rectangulo_grafico)
                valor_fin = self._x_a_valor(seleccion.right(), rectangulo_grafico)
                conteo_minimo = self._y_a_conteo(seleccion.bottom(), rectangulo_grafico)
                conteo_maximo = self._y_a_conteo(seleccion.top(), rectangulo_grafico)
                self._fijar_rango_visible(valor_inicio, valor_fin, conteo_minimo, conteo_maximo)
            else:
                self.update()
            return

        if evento.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._arrastre_inicio = None

    def mouseDoubleClickEvent(self, evento) -> None:  # noqa: N802
        if self._rectangulo_grafico().contains(evento.position()):
            self.reiniciar_vista()

    def wheelEvent(self, evento) -> None:  # noqa: N802
        rectangulo_grafico = self._rectangulo_grafico()
        if not rectangulo_grafico.contains(evento.position()):
            return

        delta = evento.angleDelta().y()
        if delta == 0:
            return

        factor = 0.82 if delta > 0 else 1.22
        centro = self._x_a_valor(evento.position().x(), rectangulo_grafico)
        centro_conteo = self._y_a_conteo(evento.position().y(), rectangulo_grafico)
        conteo_minimo, conteo_maximo = self._rango_conteo_visible()
        nuevo_minimo = centro - (centro - self._vista_minima) * factor
        nuevo_maximo = centro + (self._vista_maxima - centro) * factor
        nuevo_conteo_minimo = centro_conteo - (centro_conteo - conteo_minimo) * factor
        nuevo_conteo_maximo = centro_conteo + (conteo_maximo - centro_conteo) * factor
        self._fijar_rango_visible(
            nuevo_minimo,
            nuevo_maximo,
            nuevo_conteo_minimo,
            nuevo_conteo_maximo,
        )
        evento.accept()

    def _dibujar_histograma(
        self,
        pintor: QPainter,
        rectangulo_grafico: QRectF,
        histograma: np.ndarray,
        color: QColor,
        conteo_minimo: float,
        conteo_maximo: float,
        opacidad: float,
    ) -> None:
        pintor.save()
        pintor.setClipRect(rectangulo_grafico)
        color = QColor(color)
        color.setAlphaF(opacidad)
        pintor.setPen(QPen(color, 1.6))

        camino = QPainterPath()
        camino.moveTo(rectangulo_grafico.bottomLeft())
        primer_valor = max(0, int(np.floor(self._vista_minima)))
        ultimo_valor = min(255, int(np.ceil(self._vista_maxima)))
        for valor in range(primer_valor, ultimo_valor + 1):
            x = self._valor_a_x(valor, rectangulo_grafico)
            x = float(np.clip(x, rectangulo_grafico.left(), rectangulo_grafico.right()))
            y = self._conteo_a_y(float(histograma[valor]), rectangulo_grafico, conteo_minimo, conteo_maximo)
            y = float(np.clip(y, rectangulo_grafico.top(), rectangulo_grafico.bottom()))
            camino.lineTo(QPointF(x, y))
        camino.lineTo(rectangulo_grafico.bottomRight())
        camino.closeSubpath()

        relleno = QColor(color)
        relleno.setAlphaF(opacidad * 0.3)
        pintor.fillPath(camino, relleno)
        pintor.drawPath(camino)
        pintor.restore()

    def _dibujar_etiquetas_ejes(
        self,
        pintor: QPainter,
        rectangulo_grafico: QRectF,
        conteo_minimo: float,
        conteo_maximo: float,
    ) -> None:
        pintor.setPen(QColor("#f9fafb"))
        pintor.drawText(
            QRectF(rectangulo_grafico.left(), rectangulo_grafico.bottom() + 2, 24, 16),
            Qt.AlignLeft,
            str(int(round(self._vista_minima))),
        )
        pintor.drawText(
            QRectF(rectangulo_grafico.right() - 24, rectangulo_grafico.bottom() + 2, 24, 16),
            Qt.AlignRight,
            str(int(round(self._vista_maxima))),
        )
        pintor.drawText(
            QRectF(rectangulo_grafico.left(), rectangulo_grafico.top() - 2, 72, 16),
            Qt.AlignLeft | Qt.AlignTop,
            str(int(round(conteo_maximo))),
        )
        if conteo_minimo > 0.0:
            pintor.drawText(
                QRectF(rectangulo_grafico.right() - 72, rectangulo_grafico.top() - 2, 72, 16),
                Qt.AlignRight | Qt.AlignTop,
                str(int(round(conteo_minimo))),
            )

    def _dibujar_seleccion(self, pintor: QPainter, rectangulo_grafico: QRectF) -> None:
        if self._seleccion_inicio is None or self._seleccion_fin is None:
            return

        seleccion = self._rectangulo_seleccion(rectangulo_grafico)
        pintor.fillRect(seleccion, QColor(249, 250, 251, 58))
        pintor.setPen(QPen(QColor("#f9fafb"), 1))
        pintor.drawRect(seleccion)

    def _valor_a_x(self, valor: float, rectangulo_grafico: QRectF) -> float:
        rango = max(self._vista_maxima - self._vista_minima, 1.0)
        return rectangulo_grafico.left() + (
            rectangulo_grafico.width() * (valor - self._vista_minima) / rango
        )

    def _x_a_valor(self, posicion_x: float, rectangulo_grafico: QRectF) -> float:
        proporcion = (posicion_x - rectangulo_grafico.left()) / max(rectangulo_grafico.width(), 1.0)
        return self._vista_minima + float(np.clip(proporcion, 0.0, 1.0)) * (
            self._vista_maxima - self._vista_minima
        )

    def _conteo_a_y(
        self,
        conteo: float,
        rectangulo_grafico: QRectF,
        conteo_minimo: float,
        conteo_maximo: float,
    ) -> float:
        rango = max(conteo_maximo - conteo_minimo, 1.0)
        return rectangulo_grafico.bottom() - (
            rectangulo_grafico.height() * (conteo - conteo_minimo) / rango
        )

    def _y_a_conteo(self, posicion_y: float, rectangulo_grafico: QRectF) -> float:
        conteo_minimo, conteo_maximo = self._rango_conteo_visible()
        proporcion = (rectangulo_grafico.bottom() - posicion_y) / max(rectangulo_grafico.height(), 1.0)
        return conteo_minimo + float(np.clip(proporcion, 0.0, 1.0)) * (
            conteo_maximo - conteo_minimo
        )

    def _fijar_rango_visible(
        self,
        valor_minimo: float,
        valor_maximo: float,
        conteo_minimo: float,
        conteo_maximo: float,
    ) -> None:
        valor_minimo, valor_maximo = sorted((float(valor_minimo), float(valor_maximo)))
        rango_valores = valor_maximo - valor_minimo

        conteo_total_maximo = self._conteo_maximo_histograma(valor_minimo, valor_maximo)
        conteo_minimo, conteo_maximo = sorted((float(conteo_minimo), float(conteo_maximo)))
        rango_conteo = conteo_maximo - conteo_minimo

        if rango_valores >= 255.0 and conteo_minimo <= 0.0 and conteo_maximo >= conteo_total_maximo:
            self.reiniciar_vista()
            return

        rango_minimo = 3.0
        if rango_valores < rango_minimo:
            centro = (valor_minimo + valor_maximo) / 2.0
            valor_minimo = centro - (rango_minimo / 2.0)
            valor_maximo = centro + (rango_minimo / 2.0)
            rango_valores = rango_minimo

        if valor_minimo < 0.0:
            valor_minimo = 0.0
            valor_maximo = rango_valores
        if valor_maximo > 255.0:
            valor_maximo = 255.0
            valor_minimo = 255.0 - rango_valores

        rango_conteo = conteo_maximo - conteo_minimo
        rango_conteo_minimo = max(1.0, conteo_total_maximo * 0.02)
        if rango_conteo < rango_conteo_minimo:
            centro = (conteo_minimo + conteo_maximo) / 2.0
            conteo_minimo = centro - (rango_conteo_minimo / 2.0)
            conteo_maximo = centro + (rango_conteo_minimo / 2.0)
            rango_conteo = rango_conteo_minimo

        if conteo_minimo < 0.0:
            conteo_maximo -= conteo_minimo
            conteo_minimo = 0.0
        if conteo_maximo > conteo_total_maximo:
            conteo_minimo -= conteo_maximo - conteo_total_maximo
            conteo_maximo = conteo_total_maximo
        if rango_conteo >= conteo_total_maximo:
            conteo_minimo = 0.0
            conteo_maximo = conteo_total_maximo
        else:
            conteo_minimo = max(0.0, conteo_minimo)
            conteo_maximo = min(conteo_total_maximo, conteo_maximo)

        self._vista_minima = max(0.0, valor_minimo)
        self._vista_maxima = min(255.0, valor_maximo)
        self._conteo_minimo = conteo_minimo
        self._conteo_maximo = conteo_maximo
        self.update()

    def _rectangulo_seleccion(self, rectangulo_grafico: QRectF) -> QRectF:
        if self._seleccion_inicio is None:
            return QRectF()

        fin = self._seleccion_fin or self._seleccion_inicio
        inicio = self._punto_limitado(self._seleccion_inicio, rectangulo_grafico)
        fin = self._punto_limitado(fin, rectangulo_grafico)
        return QRectF(inicio, fin).normalized()

    @staticmethod
    def _punto_limitado(punto: QPointF, rectangulo_grafico: QRectF) -> QPointF:
        return QPointF(
            float(np.clip(punto.x(), rectangulo_grafico.left(), rectangulo_grafico.right())),
            float(np.clip(punto.y(), rectangulo_grafico.top(), rectangulo_grafico.bottom())),
        )

    def _rango_conteo_visible(self) -> tuple[float, float]:
        return self._conteo_minimo, self._conteo_maximo or self._conteo_visible_maximo()

    def _conteo_visible_maximo(self) -> float:
        return self._conteo_maximo_histograma(self._vista_minima, self._vista_maxima)

    def _conteo_maximo_histograma(self, valor_minimo: float, valor_maximo: float) -> float:
        primer_valor = max(0, int(np.floor(valor_minimo)))
        ultimo_valor = min(255, int(np.ceil(valor_maximo))) + 1
        base_visible = self._histograma_base[primer_valor:ultimo_valor]
        ajustado_visible = self._histograma_ajustado[primer_valor:ultimo_valor]
        return max(
            float(base_visible.max()) if base_visible.size else 0.0,
            float(ajustado_visible.max()) if ajustado_visible.size else 0.0,
            1.0,
        )

    def _rectangulo_grafico(self) -> QRectF:
        rectangulo_externo = QRectF(self.rect().adjusted(4, 4, -4, -4))
        return rectangulo_externo.adjusted(10, 10, -10, -18)


@dataclass(slots=True)
class FilaDeslizador:
    etiqueta: QLabel
    deslizador: QSlider
    valor: QLabel


class TarjetaControlCanal(QFrame):
    ajustesCambiados = Signal(str, object)

    def __init__(self, clave_canal: str) -> None:
        super().__init__()
        self.clave_canal = clave_canal
        datos_canal = DATOS_CANAL[clave_canal]
        self.setObjectName("tarjeta")
        self._intensidad_inicial = 100

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(14, 14, 14, 14)
        disposicion.setSpacing(9)

        fila_titulo = QHBoxLayout()
        fila_titulo.setContentsMargins(0, 0, 0, 0)
        fila_titulo.setSpacing(8)

        titulo = QLabel(f"Histograma {datos_canal['nombre']}")
        titulo.setObjectName("tituloTarjeta")
        fila_titulo.addWidget(titulo, 1)

        self.boton_reiniciar = QPushButton()
        self.boton_reiniciar.setObjectName("botonIcono")
        self.boton_reiniciar.setIcon(icono_reiniciar_canal(self))
        self.boton_reiniciar.setIconSize(QSize(17, 17))
        self.boton_reiniciar.setFixedSize(QSize(30, 30))
        self.boton_reiniciar.setToolTip("Reiniciar canal al 100 %")
        self.boton_reiniciar.clicked.connect(lambda: self.reiniciar_valores())
        fila_titulo.addWidget(self.boton_reiniciar)
        disposicion.addLayout(fila_titulo)

        self.vista_histograma = VistaHistograma(datos_canal["color"])
        disposicion.addWidget(self.vista_histograma, 1)

        self.fila_intensidad = self._crear_fila_deslizador("Contraste tonal", 0, 200, 100)
        disposicion.addLayout(self._disposicion_fila(self.fila_intensidad))

        self.etiqueta_informacion = QLabel(
            "0 % comprime rangos, 100 % conserva el canal y 200 % expande contrastes."
        )
        self.etiqueta_informacion.setObjectName("textoSecundario")
        self.etiqueta_informacion.setWordWrap(True)
        disposicion.addWidget(self.etiqueta_informacion)

        self.fila_intensidad.deslizador.valueChanged.connect(self._al_cambiar_intensidad)
        self._actualizar_etiquetas()

    def fijar_histogramas(
        self,
        histograma_base: np.ndarray,
        histograma_ajustado: np.ndarray,
    ) -> None:
        self.vista_histograma.fijar_histogramas(histograma_base, histograma_ajustado)

    def reiniciar_valores(self, emitir_cambio: bool = True) -> None:
        self.fila_intensidad.deslizador.blockSignals(True)
        self.fila_intensidad.deslizador.setValue(self._intensidad_inicial)
        self.fila_intensidad.deslizador.blockSignals(False)
        self._actualizar_etiquetas()
        self.vista_histograma.reiniciar_vista()
        if emitir_cambio:
            self._emitir_ajustes_cambiados()

    def ajustes_actuales(self) -> AjusteCanal:
        return AjusteCanal(
            porcentaje_intensidad=self.fila_intensidad.deslizador.value(),
        )

    def fijar_informacion_intensidad(
        self,
        minimo_original: int,
        maximo_original: int,
        porcentaje_intensidad: int,
        minimo_salida: int,
        maximo_salida: int,
    ) -> None:
        self.etiqueta_informacion.setText(
            f"Original: {minimo_original}-{maximo_original} | "
            f"Contraste tonal: {porcentaje_intensidad}% | "
            f"Salida: {minimo_salida}-{maximo_salida}"
        )

    def _al_cambiar_intensidad(self, valor: int) -> None:
        del valor
        self._actualizar_etiquetas()
        self._emitir_ajustes_cambiados()

    def _emitir_ajustes_cambiados(self) -> None:
        self.ajustesCambiados.emit(self.clave_canal, self.ajustes_actuales())

    def _actualizar_etiquetas(self) -> None:
        self.fila_intensidad.valor.setText(f"{self.fila_intensidad.deslizador.value()}%")

    @staticmethod
    def _crear_fila_deslizador(
        texto_etiqueta: str,
        minimo: int,
        maximo: int,
        valor: int,
    ) -> FilaDeslizador:
        etiqueta = QLabel(texto_etiqueta)
        etiqueta.setObjectName("etiquetaControl")
        deslizador = QSlider(Qt.Horizontal)
        deslizador.setRange(minimo, maximo)
        deslizador.setValue(valor)
        deslizador.setSingleStep(1)
        etiqueta_valor = QLabel(f"{valor}%")
        etiqueta_valor.setObjectName("pastillaValor")
        etiqueta_valor.setAlignment(Qt.AlignCenter)
        etiqueta_valor.setMinimumWidth(52)
        return FilaDeslizador(etiqueta=etiqueta, deslizador=deslizador, valor=etiqueta_valor)

    @staticmethod
    def _disposicion_fila(fila: FilaDeslizador) -> QHBoxLayout:
        disposicion = QHBoxLayout()
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(10)
        disposicion.addWidget(fila.etiqueta)
        disposicion.addWidget(fila.deslizador, 1)
        disposicion.addWidget(fila.valor)
        return disposicion
