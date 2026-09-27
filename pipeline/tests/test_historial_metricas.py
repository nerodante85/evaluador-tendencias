import json

from pipeline.historial_metricas import registrar


def _pesos(calibrado, auc, exactitud, exactitud_mayoria=0.6, n_train=100, n_test=50):
    return {
        "calibrado": calibrado,
        "n_entrenamiento": n_train,
        "n_prueba": n_test,
        "evaluacion_fuera_de_muestra": {"n": n_test, "exactitud": exactitud, "exactitud_mayoria": exactitud_mayoria, "auc": auc},
    }


def test_primera_calibracion_no_es_alerta_y_se_registra(tmp_path):
    ruta = tmp_path / "historial.json"
    alerta, mensaje = registrar(_pesos("2026-01-01T00:00", auc=0.7, exactitud=0.65), ruta)
    assert alerta is False
    assert mensaje is None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert len(datos["calibraciones"]) == 1
    assert datos["calibraciones"][0]["auc"] == 0.7


def test_auc_estable_entre_calibraciones_no_es_alerta(tmp_path):
    ruta = tmp_path / "historial.json"
    registrar(_pesos("2026-01-01T00:00", auc=0.7, exactitud=0.65), ruta)
    alerta, _ = registrar(_pesos("2026-02-01T00:00", auc=0.68, exactitud=0.64), ruta)
    assert alerta is False


def test_caida_grande_de_auc_es_alerta(tmp_path):
    ruta = tmp_path / "historial.json"
    registrar(_pesos("2026-01-01T00:00", auc=0.7, exactitud=0.65), ruta)
    alerta, mensaje = registrar(_pesos("2026-02-01T00:00", auc=0.6, exactitud=0.62), ruta)
    assert alerta is True
    assert "AUC bajó" in mensaje
    assert "0.7" in mensaje and "0.6" in mensaje


def test_exactitud_por_debajo_de_la_mayoria_es_alerta_aunque_el_auc_no_haya_caido_mucho(tmp_path):
    ruta = tmp_path / "historial.json"
    registrar(_pesos("2026-01-01T00:00", auc=0.65, exactitud=0.65, exactitud_mayoria=0.6), ruta)
    alerta, mensaje = registrar(_pesos("2026-02-01T00:00", auc=0.63, exactitud=0.58, exactitud_mayoria=0.62), ruta)
    assert alerta is True
    assert "dejó de aportar" in mensaje


def test_el_historial_es_acumulativo_no_se_pisa_la_entrada_anterior(tmp_path):
    ruta = tmp_path / "historial.json"
    registrar(_pesos("2026-01-01T00:00", auc=0.7, exactitud=0.65), ruta)
    registrar(_pesos("2026-02-01T00:00", auc=0.71, exactitud=0.66), ruta)
    registrar(_pesos("2026-03-01T00:00", auc=0.69, exactitud=0.64), ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert [c["calibrado"] for c in datos["calibraciones"]] == ["2026-01-01T00:00", "2026-02-01T00:00", "2026-03-01T00:00"]


def test_sin_auc_disponible_no_revienta_ni_da_falsa_alerta(tmp_path):
    ruta = tmp_path / "historial.json"
    registrar(_pesos("2026-01-01T00:00", auc=None, exactitud=0.5), ruta)
    alerta, _ = registrar(_pesos("2026-02-01T00:00", auc=None, exactitud=0.5), ruta)
    assert alerta is False
