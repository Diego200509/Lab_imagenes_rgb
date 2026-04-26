from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


CANALES_RGB = ("R", "G", "B")
INDICE_CANAL = {"R": 0, "G": 1, "B": 2}
PESOS_LUMINANCIA = np.array([0.299, 0.587, 0.114], dtype=np.float32)
NIVELES_INTENSIDAD = np.linspace(0.0, 1.0, 256, dtype=np.float32)


@dataclass(slots=True)
class AjusteCanal:
    """Porcentaje de contraste tonal aplicado a una matriz de canal RGB."""

    porcentaje_intensidad: int = 100


@dataclass(slots=True)
class AjusteReduccion:
    """Porcentaje usado para crear la imagen reducida."""

    porcentaje_escala: int = 50


def cargar_imagen_rgb(ruta: str | Path) -> np.ndarray:
    import cv2

    archivo = Path(ruta)
    datos = np.fromfile(str(archivo), dtype=np.uint8)
    imagen_bgr = cv2.imdecode(datos, cv2.IMREAD_COLOR)
    if imagen_bgr is None:
        raise ValueError(f"No se pudo abrir la imagen: {archivo}")
    return imagen_bgr[:, :, [2, 1, 0]].copy()


def guardar_imagen(ruta: str | Path, imagen: np.ndarray) -> None:
    import cv2

    archivo = Path(ruta)
    extension = archivo.suffix.lower() or ".png"
    if extension not in {".png", ".jpg", ".jpeg", ".bmp"}:
        raise ValueError("Formato de salida no soportado.")

    salida = imagen
    if imagen.ndim == 3:
        salida = imagen[:, :, [2, 1, 0]]

    correcto, codificada = cv2.imencode(extension, salida)
    if not correcto:
        raise ValueError(f"No se pudo guardar la imagen en {archivo}")
    codificada.tofile(str(archivo))


def separar_canales_rgb(imagen_rgb: np.ndarray) -> dict[str, np.ndarray]:
    return {
        nombre: imagen_rgb[:, :, indice].copy()
        for nombre, indice in INDICE_CANAL.items()
    }


def calcular_histograma(canal: np.ndarray) -> np.ndarray:
    histograma = np.bincount(canal.ravel(), minlength=256)
    return histograma.astype(np.float32)


def aplicar_intensidad_canal(canal: np.ndarray, ajuste: AjusteCanal) -> np.ndarray:
    tabla = tabla_ajuste_tonal(ajuste)
    return tabla[canal]


def tabla_ajuste_tonal(ajuste: AjusteCanal) -> np.ndarray:
    porcentaje = int(np.clip(ajuste.porcentaje_intensidad, 0, 200))
    if porcentaje == 100:
        return np.arange(256, dtype=np.uint8)

    fuerza = (porcentaje - 100) / 100.0
    niveles = NIVELES_INTENSIDAD

    if fuerza < 0.0:
        factor = 1.0 + fuerza
        salida = 0.5 + (niveles - 0.5) * factor
    else:
        curvatura = 6.0 * fuerza
        salida = 0.5 + np.tanh(curvatura * (niveles - 0.5)) / (
            2.0 * np.tanh(curvatura / 2.0)
        )

    return np.rint(np.clip(salida, 0.0, 1.0) * 255.0).astype(np.uint8)


def unir_canales_rgb(canales: dict[str, np.ndarray]) -> np.ndarray:
    return np.dstack([canales["R"], canales["G"], canales["B"]]).astype(np.uint8)


def reducir_imagen_porcentaje(
    imagen: np.ndarray,
    ajuste: AjusteReduccion,
) -> np.ndarray:
    escala = int(np.clip(ajuste.porcentaje_escala, 10, 100)) / 100.0
    alto, ancho = imagen.shape[:2]
    nuevo_ancho = max(1, int(round(ancho * escala)))
    nuevo_alto = max(1, int(round(alto * escala)))
    if nuevo_alto == alto and nuevo_ancho == ancho:
        return imagen.copy()
    return redimensionar_bilineal(imagen, nuevo_alto, nuevo_ancho)


def redimensionar_bilineal(
    imagen: np.ndarray,
    nuevo_alto: int,
    nuevo_ancho: int,
) -> np.ndarray:
    alto, ancho = imagen.shape[:2]
    posiciones_y = np.linspace(0, alto - 1, nuevo_alto, dtype=np.float32)
    posiciones_x = np.linspace(0, ancho - 1, nuevo_ancho, dtype=np.float32)

    y0 = np.floor(posiciones_y).astype(np.int32)
    x0 = np.floor(posiciones_x).astype(np.int32)
    y1 = np.minimum(y0 + 1, alto - 1)
    x1 = np.minimum(x0 + 1, ancho - 1)

    peso_y = (posiciones_y - y0).astype(np.float32)
    peso_x = (posiciones_x - x0).astype(np.float32)

    if imagen.ndim == 2:
        arriba = (
            imagen[y0[:, None], x0[None, :]] * (1.0 - peso_x)[None, :]
            + imagen[y0[:, None], x1[None, :]] * peso_x[None, :]
        )
        abajo = (
            imagen[y1[:, None], x0[None, :]] * (1.0 - peso_x)[None, :]
            + imagen[y1[:, None], x1[None, :]] * peso_x[None, :]
        )
        redimensionada = arriba * (1.0 - peso_y)[:, None] + abajo * peso_y[:, None]
    else:
        peso_x_3d = peso_x[None, :, None]
        peso_y_3d = peso_y[:, None, None]
        arriba = (
            imagen[y0[:, None], x0[None, :], :] * (1.0 - peso_x_3d)
            + imagen[y0[:, None], x1[None, :], :] * peso_x_3d
        )
        abajo = (
            imagen[y1[:, None], x0[None, :], :] * (1.0 - peso_x_3d)
            + imagen[y1[:, None], x1[None, :], :] * peso_x_3d
        )
        redimensionada = arriba * (1.0 - peso_y_3d) + abajo * peso_y_3d

    return np.rint(np.clip(redimensionada, 0.0, 255.0)).astype(np.uint8)


def convertir_a_grises_luminancia(imagen_rgb: np.ndarray) -> np.ndarray:
    grises = imagen_rgb.astype(np.float32) @ PESOS_LUMINANCIA
    return np.clip(grises, 0.0, 255.0).astype(np.uint8)


def convertir_a_blanco_negro(imagen_rgb: np.ndarray, umbral: int) -> np.ndarray:
    grises = convertir_a_grises_luminancia(imagen_rgb)
    umbral_limitado = int(np.clip(umbral, 0, 255))
    return np.where(grises >= umbral_limitado, 255, 0).astype(np.uint8)
