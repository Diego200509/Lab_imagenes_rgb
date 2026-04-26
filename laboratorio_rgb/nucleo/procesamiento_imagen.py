from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


CANALES_RGB = ("R", "G", "B")
INDICE_CANAL = {"R": 0, "G": 1, "B": 2}
PESOS_LUMINANCIA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


@dataclass(slots=True)
class AjusteCanal:
    """Porcentaje de intensidad aplicado a una matriz de canal RGB."""

    porcentaje_intensidad: int = 100


@dataclass(slots=True)
class AjusteReduccion:
    """Porcentaje usado para crear la imagen reducida."""

    porcentaje_escala: int = 50


def cargar_imagen_rgb(ruta: str | Path) -> np.ndarray:
    archivo = Path(ruta)
    datos = np.fromfile(str(archivo), dtype=np.uint8)
    imagen_bgr = cv2.imdecode(datos, cv2.IMREAD_COLOR)
    if imagen_bgr is None:
        raise ValueError(f"No se pudo abrir la imagen: {archivo}")
    return cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)


def guardar_imagen(ruta: str | Path, imagen: np.ndarray) -> None:
    archivo = Path(ruta)
    extension = archivo.suffix.lower() or ".png"
    if extension not in {".png", ".jpg", ".jpeg", ".bmp"}:
        raise ValueError("Formato de salida no soportado.")

    salida = imagen
    if imagen.ndim == 3:
        salida = cv2.cvtColor(imagen, cv2.COLOR_RGB2BGR)

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
    intensidad = int(np.clip(ajuste.porcentaje_intensidad, 0, 200))
    factor = intensidad / 100.0
    canal_ajustado = canal.astype(np.float32) * factor
    return np.clip(canal_ajustado, 0.0, 255.0).astype(np.uint8)


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
    interpolacion = cv2.INTER_AREA if escala < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(imagen, (nuevo_ancho, nuevo_alto), interpolation=interpolacion)


def convertir_a_grises_luminancia(imagen_rgb: np.ndarray) -> np.ndarray:
    grises = imagen_rgb.astype(np.float32) @ PESOS_LUMINANCIA
    return np.clip(grises, 0.0, 255.0).astype(np.uint8)


def convertir_a_blanco_negro(imagen_rgb: np.ndarray, umbral: int) -> np.ndarray:
    grises = convertir_a_grises_luminancia(imagen_rgb)
    _, binaria = cv2.threshold(
        grises,
        int(np.clip(umbral, 0, 255)),
        255,
        cv2.THRESH_BINARY,
    )
    return binaria
