# API Gráfica — Visualización dinámica de datos desde una API

Componente de software que consume una API externa y genera
visualizaciones estadísticas (barras, líneas, pastel, dispersión,
histograma, boxplot) a partir del payload y los metadatos de
configuración recibidos, sin depender de una estructura de datos fija.

## Descripción

El proyecto está compuesto por dos clases principales:

- **`PrepararDatos`** (`fuente_datos.py`): se encarga de consumir el
  endpoint de la API (o un payload ya obtenido), validar la respuesta,
  convertirla en un `DataFrame` de `pandas` y exponer su estado de
  carga (`INACTIVO`, `CARGANDO`, `EXITO`, `ERROR`).
- **`Vizualizador`** (`visualizador.py`): toma los datos y los
  metadatos de configuración de `PrepararDatos` y genera la gráfica
  correspondiente usando `matplotlib` y `seaborn`. El tipo de gráfico,
  las columnas, los filtros, el orden y las etiquetas se determinan
  dinámicamente a partir de la respuesta de la API.

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd API_grafica
   ```

2. (Opcional, recomendado) Crear un entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux / macOS
   ```

3. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso básico

```python
from fuente_datos import PrepararDatos
from visualizador import Vizualizador

fuente = PrepararDatos()
fuente.cargar_desde_endpoints("https://api.ejemplo.com/ventas")

if fuente.esta_en_exito():
    viz = Vizualizador(fuente)
    viz.graficar(mostrar=True, guardar=True, nombre_archivo="grafica.png")
else:
    print(fuente.error)
```

También se puede cargar un payload ya obtenido (útil para pruebas o
datos en caché), sin hacer ninguna petición de red:

```python
fuente.cargar_desde_payload(payload)
```

### Estructura esperada del payload de la API

```json
{
  "data": [
    {"region": "Norte", "producto": "A", "ventas": "120"},
    {"region": "Sur", "producto": "B", "ventas": "150"}
  ],
  "config": {
    "tipo_grafico": "barras_agrupadas",
    "columna_x": "region",
    "columna_y": "ventas",
    "columna_grupo": "producto",
    "columnas_numericas": ["ventas"],
    "titulo": "Ventas por región"
  }
}
```

## Tipos de gráfico soportados

| `tipo_grafico` | Parámetros principales |
|---|---|
| `barras_agrupadas` | `columna_x`, `columna_y`, `columna_grupo` |
| `lineas` | `columna_x`, `columna_y`, `columna_grupo`, `rango_y` |
| `pastel` | `columna_categoria`, `columna_valor`, `agregacion` |
| `dispersion` | `columna_x`, `columna_y`, `columna_grupo` |
| `histograma` | `columna_x`, `columna_grupo`, `bins`, `kde` |
| `boxplot` | `columna_x`, `columna_y`, `columna_grupo` |

Todos los tipos soportan además `filtros`, `ordenar_por`, `titulo`,
`etiqueta_x`, `etiqueta_y`, `figsize` y `paleta`, definidos desde la
configuración de la API.

## Pruebas

Las pruebas de integración simulan la respuesta de la API mediante
`unittest.mock`, sin depender de un servidor real. Cubren carga
exitosa, errores de conexión, errores HTTP, JSON inválido, payloads
vacíos o mal formados, y la generación de al menos dos tipos distintos
de visualización (barras agrupadas y pastel).

Para ejecutarlas:

```bash
python -m pytest tests/test_integracion.py -v
```
