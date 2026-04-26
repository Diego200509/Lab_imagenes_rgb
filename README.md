# Laboratorio RGB

Aplicacion de escritorio en Python para cargar una imagen RGB, separar sus
canales rojo, verde y azul, ajustar la intensidad de cada matriz, reconstruir la
imagen final, reducirla y convertirla a blanco y negro.

## Funciones principales

1. Carga imagenes JPG, JPEG, PNG o BMP.
2. Muestra la imagen original y la imagen RGB reconstruida.
3. Separa la imagen en tres matrices: R, G y B.
4. Muestra cada canal separado en escala de grises.
5. Calcula histogramas por canal y permite ajustar cada intensidad.
6. Reconstruye la imagen con los canales ajustados.
7. Reduce la imagen reconstruida por porcentaje.
8. Convierte la imagen reducida a blanco y negro usando un umbral.
9. Guarda la version RGB modificada, la reducida o la B/N.

## Estructura

```text
main.py
img/
  gato.png
laboratorio_rgb/
  aplicacion.py                 # Arranque de la aplicacion y fuente
  nucleo/
    procesamiento_imagen.py     # Carga, guardado y operaciones con matrices
  interfaz/
    ventana_principal.py        # Ventana, pestanas y flujo principal
    componentes.py              # Tarjetas, histogramas y controles por canal
    estilos.py                  # Hoja de estilos de la interfaz
requirements.txt
```

## Ejecucion

```bash
python -m pip install -r requirements.txt
python main.py
```

## Idea tecnica

Una imagen RGB contiene tres matrices de intensidades:

```text
Imagen RGB = R + G + B
```

Cuando se separa un canal, queda una sola matriz con valores de 0 a 255. Por
eso el canal separado se muestra en escala de grises: los pixeles claros tienen
mayor intensidad de ese canal y los oscuros tienen menor intensidad.

El slider aplica un factor porcentual:

```text
canal_modificado = canal_original * (intensidad / 100)
```

Luego se limita el resultado al rango valido:

```text
0 <= valor <= 255
```

La imagen final vuelve a tener color cuando se apilan de nuevo las tres matrices:

```text
imagen_nueva = unir(R_modificado, G_modificado, B_modificado)
```

Para blanco y negro, primero se calcula luminancia:

```text
gris = 0.299R + 0.587G + 0.114B
```

Despues se aplica el umbral:

```text
si gris >= umbral => blanco
si gris < umbral  => negro
```
