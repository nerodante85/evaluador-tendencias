from dataclasses import replace

from pipeline.taxonomia import TIPOS, Mercado, Nodo, Taxonomia, cargar, validar


def test_la_taxonomia_real_es_valida():
    assert validar(cargar()) == []


def test_tamano_y_cobertura_de_la_taxonomia_real():
    tax = cargar()
    assert len(tax.nodos) >= 150
    assert set(tax.mercados) == {"CO", "MX", "ES"}
    for tipo in TIPOS:
        assert len(tax.por_tipo(tipo)) >= 10, f"muy pocos nodos de tipo {tipo}"


def test_las_30_senales_de_la_v1_tienen_destino():
    tax = cargar()
    con_nodo = {i for n in tax.nodos.values() for i in n.v1}
    for i in range(1, 31):
        assert i in con_nodo or i in tax.fuera_de_alcance, f"señal v1 #{i} sin destino"


def test_el_vocabulario_regional_se_conserva():
    jean = cargar().nodos["prenda.jean"]
    assert jean.consultas == {"CO": "jean", "MX": "jeans", "ES": "vaqueros"}


def test_los_nodos_con_override_de_categoria_verificado_en_vivo_lo_conservan():
    # Ver docs/v2 y los comentarios junto a cada nodo: probado en vivo el
    # 2026-09-27, la categoría "Ropa" ahogaba estos términos de estética.
    tax = cargar()
    for nid in ("estilo.cottagecore", "estilo.mob_wife", "estampado.tie_dye", "estampado.cachemira", "tela.punto", "tela.fibras_naturales"):
        assert tax.nodos[nid].categoria == 0, nid


def test_los_nodos_sin_override_usan_la_categoria_por_defecto():
    tax = cargar()
    for nid in ("estilo.barbiecore", "tela.reciclada", "tela.algodon_organico", "corte.manga_globo"):
        assert tax.nodos[nid].categoria is None, nid


# --- El validador tiene que detectar errores de verdad, no solo aprobar ---


def _base():
    mercados = {"CO": Mercado("CO", "Colombia", "es-CO", 300), "MX": Mercado("MX", "México", "es-MX", 360)}
    a = Nodo("prenda.a", "prenda", "A", {"CO": "a", "MX": "a"})
    c = Nodo("color.rojo", "color", "Rojo", {"CO": "rojo", "MX": "rojo"}, hex="#C22E22", familia="rojo")
    return Taxonomia(mercados, {a.id: a, c.id: c}, {}, {}), a, c


def _con(tax, *nodos):
    return replace(tax, nodos={**tax.nodos, **{n.id: n for n in nodos}})


def test_un_caso_minimo_correcto_no_da_problemas():
    tax, _, _ = _base()
    assert validar(tax, ids_v1=[]) == []


def test_detecta_consulta_faltante_en_un_mercado():
    tax, a, _ = _base()
    tax = _con(tax, replace(a, consultas={"CO": "a"}))
    assert any("sin consulta para ['MX']" in p for p in validar(tax, ids_v1=[]))


def test_detecta_consulta_duplicada_en_un_mercado():
    tax, a, _ = _base()
    b = Nodo("prenda.b", "prenda", "B", {"CO": "A ", "MX": "otra"})  # "A " ~ "a" (sin distinguir mayúsculas ni espacios)
    assert any("ya la usa" in p for p in validar(_con(tax, b), ids_v1=[]))


def test_detecta_padre_inexistente_y_de_otro_tipo():
    tax, a, c = _base()
    assert any("no existe" in p for p in validar(_con(tax, replace(a, padre="prenda.fantasma")), ids_v1=[]))
    assert any("otro tipo" in p for p in validar(_con(tax, replace(a, padre="color.rojo")), ids_v1=[]))


def test_detecta_relacion_inexistente():
    tax, a, _ = _base()
    assert any("la relación 'tela.x' no existe" in p for p in validar(_con(tax, replace(a, relaciones=("tela.x",))), ids_v1=[]))


def test_detecta_color_sin_hex_valido_o_familia_invalida():
    tax, _, c = _base()
    assert any("hex válido" in p for p in validar(_con(tax, replace(c, hex="rojo")), ids_v1=[]))
    assert any("familia" in p for p in validar(_con(tax, replace(c, familia="chillon")), ids_v1=[]))


def test_detecta_id_que_no_corresponde_al_tipo():
    tax, a, _ = _base()
    malo = replace(a, id="tela.a")  # tipo prenda con id de tela
    assert any("el id debe ser" in p for p in validar(replace(tax, nodos={malo.id: malo}), ids_v1=[]))


def test_detecta_senal_v1_sin_destino():
    tax, _, _ = _base()
    assert any("señal v1 #7 sin destino" in p for p in validar(tax, ids_v1=[7]))
    tax_ok = replace(tax, fuera_de_alcance={7: "motivo"})
    assert validar(tax_ok, ids_v1=[7]) == []


def test_detecta_nodo_de_control_inexistente():
    tax, _, _ = _base()
    assert any("no existe" in p for p in validar(replace(tax, control={"pico": ["estilo.nada"]}), ids_v1=[]))
