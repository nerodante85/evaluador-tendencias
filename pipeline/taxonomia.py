"""Carga y valida la taxonomía de moda de Radar 2.0 (carpeta taxonomia/).

La taxonomía es la columna vertebral de la v2: en vez de medir nombres libres
("verde oliva profundo"), cada cosa que se mide es un nodo con tipo (prenda,
corte, tela, color, estampado, estilo), una consulta por mercado y relaciones
con otros nodos. Eso permite agregar, navegar (prendas → cortes → telas → …)
y comparar en el tiempo con ids estables.

`cargar()` lee los YAML y falla si la estructura está mal formada.
`validar()` revisa la coherencia entre nodos y devuelve la lista de problemas
(vacía = todo bien); las pruebas exigen que esté vacía.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
DIR_TAXONOMIA = RAIZ / "taxonomia"

TIPOS = ("prenda", "corte", "tela", "color", "estampado", "estilo")
ARCHIVO_DE_TIPO = {
    "prenda": "prendas.yaml",
    "corte": "cortes.yaml",
    "tela": "telas.yaml",
    "color": "colores.yaml",
    "estampado": "estampados.yaml",
    "estilo": "estilos.yaml",
}
FAMILIAS_COLOR = ("neutro", "marron", "azul", "verde", "amarillo", "naranja", "rojo", "rosa", "morado", "metalico")

_ID = re.compile(r"^([a-z]+)\.[a-z0-9_]+$")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ErrorTaxonomia(Exception):
    """La estructura de un archivo de la taxonomía no se puede leer."""


@dataclass(frozen=True)
class Mercado:
    codigo: str
    nombre: str
    hl: str
    tz: int


@dataclass(frozen=True)
class Nodo:
    id: str
    tipo: str
    nombre: str
    consultas: dict  # {codigo_mercado: consulta}
    padre: str | None = None
    relaciones: tuple = ()
    v1: tuple = ()
    hex: str | None = None
    familia: str | None = None
    # Override de categoría de Google Trends para este nodo (ver
    # pipeline/fuentes/trends.py CATEGORIA_ROPA). None = usa la categoría por
    # defecto del pipeline. Se agregó el 2026-09-27 tras probar en vivo que
    # varios términos de estética ("cottagecore", "tie dye", "tejido de
    # punto") aparecían casi en cero dentro de la categoría "Ropa" pero con
    # volumen real fuera de ella — el filtro los ahogaba. Solo se usa en los
    # nodos donde esa prueba mostró mejora real, no como regla general.
    categoria: int | None = None


@dataclass(frozen=True)
class Taxonomia:
    mercados: dict  # {codigo: Mercado}
    nodos: dict  # {id: Nodo}
    fuera_de_alcance: dict  # {id_v1: motivo}
    control: dict  # {comportamiento: [id_nodo]}

    def por_tipo(self, tipo):
        return [n for n in self.nodos.values() if n.tipo == tipo]


def _leer(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise ErrorTaxonomia(f"No se pudo leer {ruta.name}: {e}") from e


def _consultas(nodo_id, q, codigos):
    """`q` puede ser un texto (igual en todos los mercados) o un mapa por mercado."""
    if isinstance(q, str):
        return {c: q for c in codigos}
    if isinstance(q, dict):
        return {str(c): str(v) for c, v in q.items()}
    raise ErrorTaxonomia(f"{nodo_id}: `q` debe ser texto o mapa por mercado")


def cargar(directorio=DIR_TAXONOMIA):
    directorio = Path(directorio)

    mercados = {}
    for m in _leer(directorio / "mercados.yaml")["mercados"]:
        mercados[m["codigo"]] = Mercado(m["codigo"], m["nombre"], m["hl"], int(m["tz"]))
    codigos = tuple(mercados)

    nodos = {}
    for tipo, archivo in ARCHIVO_DE_TIPO.items():
        datos = _leer(directorio / archivo)
        if datos.get("tipo") != tipo:
            raise ErrorTaxonomia(f"{archivo}: se esperaba tipo '{tipo}', dice '{datos.get('tipo')}'")
        for n in datos["nodos"]:
            for campo in ("id", "nombre", "q"):
                if campo not in n:
                    raise ErrorTaxonomia(f"{archivo}: un nodo no tiene el campo '{campo}': {n}")
            if n["id"] in nodos:
                raise ErrorTaxonomia(f"{archivo}: id repetido '{n['id']}'")
            nodos[n["id"]] = Nodo(
                id=n["id"],
                tipo=tipo,
                nombre=n["nombre"],
                consultas=_consultas(n["id"], n["q"], codigos),
                padre=n.get("padre"),
                relaciones=tuple(n.get("relaciones", ())),
                v1=tuple(n.get("v1", ())),
                hex=n.get("hex"),
                familia=n.get("familia"),
                categoria=n.get("categoria"),
            )

    migracion = _leer(directorio / "migracion_v1.yaml")
    control = _leer(directorio / "control.yaml")["control"]
    return Taxonomia(
        mercados=mercados,
        nodos=nodos,
        fuera_de_alcance={int(k): v for k, v in migracion["fuera_de_alcance"].items()},
        control=control,
    )


def validar(tax, ids_v1=range(1, 31)):
    """Devuelve la lista de problemas de coherencia. Vacía = la taxonomía está bien."""
    problemas = []

    consultas_vistas = {}
    for n in tax.nodos.values():
        m = _ID.match(n.id)
        if not m or m.group(1) != n.tipo:
            problemas.append(f"{n.id}: el id debe ser '{n.tipo}.<nombre_en_minusculas>'")

        faltan = set(tax.mercados) - set(n.consultas)
        sobran = set(n.consultas) - set(tax.mercados)
        if faltan:
            problemas.append(f"{n.id}: sin consulta para {sorted(faltan)}")
        if sobran:
            problemas.append(f"{n.id}: consulta para mercados que no existen {sorted(sobran)}")
        for codigo, consulta in n.consultas.items():
            if not consulta.strip():
                problemas.append(f"{n.id}: consulta vacía en {codigo}")
                continue
            clave = (codigo, consulta.strip().lower())
            if clave in consultas_vistas:
                problemas.append(f"{n.id}: la consulta '{consulta}' ({codigo}) ya la usa {consultas_vistas[clave]}")
            consultas_vistas[clave] = n.id

        if n.padre is not None:
            padre = tax.nodos.get(n.padre)
            if padre is None:
                problemas.append(f"{n.id}: el padre '{n.padre}' no existe")
            elif padre.tipo != n.tipo:
                problemas.append(f"{n.id}: el padre '{n.padre}' es de otro tipo")
        for r in n.relaciones:
            if r not in tax.nodos:
                problemas.append(f"{n.id}: la relación '{r}' no existe")
            elif r == n.id:
                problemas.append(f"{n.id}: se relaciona consigo mismo")

        if n.tipo == "color":
            if not n.hex or not _HEX.match(n.hex):
                problemas.append(f"{n.id}: falta un hex válido (#RRGGBB)")
            if n.familia not in FAMILIAS_COLOR:
                problemas.append(f"{n.id}: familia '{n.familia}' no está en {FAMILIAS_COLOR}")

    # Ninguna señal de la v1 puede quedar sin destino: es lo que mantiene
    # conectada la v2 con la línea base de septiembre.
    con_nodo = {i for n in tax.nodos.values() for i in n.v1}
    for i in ids_v1:
        if i not in con_nodo and i not in tax.fuera_de_alcance:
            problemas.append(f"señal v1 #{i} sin destino (ni nodo con v1:[{i}] ni fuera_de_alcance)")
        if i in con_nodo and i in tax.fuera_de_alcance:
            problemas.append(f"señal v1 #{i} está a la vez en un nodo y en fuera_de_alcance")

    for comportamiento, ids in tax.control.items():
        for i in ids:
            if i not in tax.nodos:
                problemas.append(f"control.{comportamiento}: el nodo '{i}' no existe")

    return problemas
