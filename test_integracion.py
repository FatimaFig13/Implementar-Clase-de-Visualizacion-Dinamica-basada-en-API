
import matplotlib
matplotlib.use("Agg")  # backend sin pantalla, necesario antes de importar pyplot

import requests
from unittest.mock import patch, Mock

from fuente_datos import PrepararDatos, EstadoCarga
from visualizador import Vizualizador


# ---------------------------------------------------------------------------
# Mocks de payloads que "la API" devolvería
# ---------------------------------------------------------------------------

PAYLOAD_BARRAS = {
    "data": [
        {"region": "Norte", "producto": "A", "ventas": "120"},
        {"region": "Norte", "producto": "B", "ventas": "80"},
        {"region": "Sur", "producto": "A", "ventas": "200"},
        {"region": "Sur", "producto": "B", "ventas": "150"},
    ],
    "config": {
        "tipo_grafico": "barras_agrupadas",
        "columna_x": "region",
        "columna_y": "ventas",
        "columna_grupo": "producto",
        "columnas_numericas": ["ventas"],
        "titulo": "Ventas por región",
        "figsize": (10, 5),
    },
}

PAYLOAD_PASTEL = {
    "data": [
        {"categoria": "Electrónica", "monto": "500"},
        {"categoria": "Ropa", "monto": "300"},
        {"categoria": "Hogar", "monto": "200"},
    ],
    "config": {
        "tipo_grafico": "pastel",
        "columna_categoria": "categoria",
        "columna_valor": "monto",
        "columnas_numericas": ["monto"],
        "titulo": "Distribución de ventas",
    },
}

PAYLOAD_SIN_DATA = {"config": {"tipo_grafico": "lineas"}}
PAYLOAD_DATA_VACIA = {"data": [], "config": {}}


def _mock_response(json_data, status_ok=True):
    
    resp = Mock()
    if status_ok:
        resp.raise_for_status.return_value = None
    else:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
    resp.json.return_value = json_data
    return resp


# ---------------------------------------------------------------------------
# 1. Integración y consumo de la API (mockeando requests.get)
# ---------------------------------------------------------------------------

@patch("fuente_datos.requests.get")
def test_carga_exitosa_desde_endpoint(mock_get):
    mock_get.return_value = _mock_response(PAYLOAD_BARRAS)

    fuente = PrepararDatos()
    ok = fuente.cargar_desde_endpoints("https://api.falsa.com/ventas")

    assert ok is True
    assert fuente.esta_en_exito()
    assert fuente.estado == EstadoCarga.EXITO
    assert list(fuente.df.columns) == ["region", "producto", "ventas"]
    assert fuente.df["ventas"].dtype.kind in "if"  # se convirtió a numérico


@patch("fuente_datos.requests.get")
def test_error_de_conexion(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("sin red")

    fuente = PrepararDatos()
    ok = fuente.cargar_desde_endpoints("https://api.falsa.com/ventas")

    assert ok is False
    assert fuente.esta_en_error()
    assert "Error de conexion" in fuente.error


@patch("fuente_datos.requests.get")
def test_respuesta_http_error(mock_get):
    mock_get.return_value = _mock_response({}, status_ok=False)

    fuente = PrepararDatos()
    ok = fuente.cargar_desde_endpoints("https://api.falsa.com/ventas")

    assert ok is False
    assert fuente.esta_en_error()


@patch("fuente_datos.requests.get")
def test_json_invalido(mock_get):
    resp = Mock()
    resp.raise_for_status.return_value = None
    resp.json.side_effect = ValueError("no es JSON")
    mock_get.return_value = resp

    fuente = PrepararDatos()
    ok = fuente.cargar_desde_endpoints("https://api.falsa.com/ventas")

    assert ok is False
    assert fuente.esta_en_error()
    assert "JSON valido" in fuente.error


# ---------------------------------------------------------------------------
# 2. Manejo de estados de carga / datos vacíos / payload mal formado
# ---------------------------------------------------------------------------

def test_payload_sin_clave_data():
    fuente = PrepararDatos()
    ok = fuente.cargar_desde_payload(PAYLOAD_SIN_DATA)
    assert ok is False
    assert fuente.esta_en_error()
    assert "clave 'data'" in fuente.error


def test_payload_con_data_vacia():
    fuente = PrepararDatos()
    ok = fuente.cargar_desde_payload(PAYLOAD_DATA_VACIA)
    assert ok is False
    assert fuente.esta_en_error()


def test_estado_inicial_es_inactivo():
    fuente = PrepararDatos()
    assert fuente.estado == EstadoCarga.INACTIVO
    assert not fuente.esta_en_exito()
    assert not fuente.esta_en_error()


# ---------------------------------------------------------------------------
# 3. Pruebas de integración con el Vizualizador (>= 2 tipos de gráfico)
# ---------------------------------------------------------------------------

def test_visualizacion_barras_agrupadas():
    fuente = PrepararDatos()
    assert fuente.cargar_desde_payload(PAYLOAD_BARRAS)

    viz = Vizualizador(fuente)
    fig = viz.graficar(mostrar=False, guardar=False)

    assert fig is not None
    assert fig.axes[0].get_title() == "Ventas por región"


def test_visualizacion_pastel():
    fuente = PrepararDatos()
    assert fuente.cargar_desde_payload(PAYLOAD_PASTEL)

    viz = Vizualizador(fuente)
    fig = viz.graficar(mostrar=False, guardar=False)

    assert fig is not None
    assert fig.axes[0].get_title() == "Distribución de ventas"


def test_visualizador_no_grafica_si_hay_error():
    fuente = PrepararDatos()
    fuente.cargar_desde_payload(PAYLOAD_DATA_VACIA)  # queda en error

    viz = Vizualizador(fuente)
    fig = viz.graficar(mostrar=False)

    assert fig is None


def test_visualizador_columna_filtro_dinamico():
    """Verifica que 'filtros' y 'ordenar_por' del metadata se apliquen."""
    payload = {
        "data": [
            {"region": "Norte", "ventas": "10"},
            {"region": "Sur", "ventas": "50"},
            {"region": "Norte", "ventas": "30"},
        ],
        "config": {
            "tipo_grafico": "barras_agrupadas",
            "columna_x": "region",
            "columna_y": "ventas",
            "columnas_numericas": ["ventas"],
            "filtros": {"region": ["Norte"]},
            "ordenar_por": "ventas",
        },
    }
    fuente = PrepararDatos()
    fuente.cargar_desde_payload(payload)

    viz = Vizualizador(fuente)
    data_filtrada = viz._preparar(
        ["region", "ventas", None], fuente.metadatos, columnas_numericas=["ventas"]
    )
    assert (data_filtrada["region"] == "Norte").all()
    assert list(data_filtrada["ventas"]) == [10.0, 30.0]


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))