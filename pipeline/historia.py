"""Descarga la historia larga de cada nodo × mercado y la guarda en data/v2/raw/.

Diseño para una corrida de ~450 series (150 nodos × 3 mercados), que a un ritmo
prudente tarda más de una hora y puede toparse con el límite de Google:

  - Una serie por archivo. Que el archivo exista = esa serie está hecha, así
    que la corrida se puede cortar y reanudar sin repetir nada.
  - Escritura atómica (archivo temporal + renombrar): un corte a mitad de
    escritura nunca deja un archivo a medias que parezca válido.
  - Pausa entre consultas con un poco de azar, y espera larga y creciente
    cuando Google bloquea (429).
  - Si varias series seguidas fallan incluso tras reintentar, se asume que
    Google está bloqueando la conexión y la corrida se detiene limpia, en vez
    de seguir golpeando y empeorar el bloqueo.

Se descarta el último mes si Trends lo marca como parcial: todavía se está
midiendo y casi siempre aparece bajo, lo que simularía una caída (mismo
criterio que la v1).
"""

import json
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .fuentes.trends import CATEGORIA_ROPA, TIMEFRAME_HISTORIA, Bloqueado, ErrorFuente
from .taxonomia import RAIZ

DIR_RAW = RAIZ / "data" / "v2" / "raw" / "trends"
ESQUEMA = 1


@dataclass
class Resumen:
    total: int = 0
    en_cache: int = 0
    descargadas: int = 0
    sin_datos: int = 0
    fallidas: list = field(default_factory=list)
    interrumpida: bool = False
    motivo: str = ""


def ruta_serie(mercado, nodo_id, dir_raw=DIR_RAW):
    return Path(dir_raw) / mercado / f"{nodo_id}.json"


def leer_serie(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _escribir_atomico(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, ruta)


def _registro(nodo, mercado, consulta, filas, backend, ahora):
    parcial_descartado = bool(filas) and filas[-1]["parcial"]
    if parcial_descartado:
        filas = filas[:-1]
    return {
        "esquema": ESQUEMA,
        "nodo": nodo.id,
        "mercado": mercado.codigo,
        "consulta": consulta,
        "categoria": CATEGORIA_ROPA,
        "timeframe": TIMEFRAME_HISTORIA,
        "backend": backend.nombre,
        "descargado": ahora().isoformat(timespec="minutes"),
        "estado": "ok" if filas else "sin_datos",
        "parcial_descartado": parcial_descartado,
        "serie": [[f["fecha"], f["valor"]] for f in filas],
    }


def descargar_historia(
    tax,
    backend,
    dir_raw=DIR_RAW,
    mercados=None,
    tipos=None,
    limite=None,
    refrescar=False,
    pausa=8.0,
    jitter=3.0,
    reintentos=4,
    max_fallos_seguidos=4,
    dormir=time.sleep,
    ahora=datetime.now,
    log=print,
):
    """Descarga las series que falten. `limite` corta tras N descargas nuevas
    (sirve para probar). Devuelve un Resumen."""
    codigos = list(mercados) if mercados else list(tax.mercados)
    nodos = [n for n in tax.nodos.values() if not tipos or n.tipo in tipos]
    trabajo = [(tax.mercados[c], n) for c in codigos for n in nodos]

    r = Resumen(total=len(trabajo))
    fallos_seguidos = 0
    hechas_ahora = 0

    for i, (mercado, nodo) in enumerate(trabajo, 1):
        ruta = ruta_serie(mercado.codigo, nodo.id, dir_raw)
        if ruta.exists() and not refrescar:
            r.en_cache += 1
            continue
        if limite is not None and hechas_ahora >= limite:
            r.interrumpida, r.motivo = True, f"límite de {limite} descargas alcanzado"
            break

        consulta = nodo.consultas[mercado.codigo]
        filas = None
        for intento in range(1, reintentos + 1):
            try:
                filas = backend.interes_en_el_tiempo(consulta, mercado)
                break
            except Bloqueado as e:
                espera = min(60 * 2 ** (intento - 1), 600)
                log(f"  [{i}/{r.total}] bloqueado (429) en {mercado.codigo} '{consulta}', espero {espera}s (intento {intento}/{reintentos})")
                dormir(espera)
            except ErrorFuente as e:
                log(f"  [{i}/{r.total}] error en {mercado.codigo} '{consulta}': {e} (intento {intento}/{reintentos})")
                dormir(15 * intento)

        if filas is None:
            r.fallidas.append((mercado.codigo, nodo.id))
            fallos_seguidos += 1
            if fallos_seguidos >= max_fallos_seguidos:
                r.interrumpida = True
                r.motivo = f"{fallos_seguidos} series seguidas fallaron: probable bloqueo. Reanuda más tarde con el mismo comando."
                log(r.motivo)
                break
            continue

        fallos_seguidos = 0
        registro = _registro(nodo, mercado, consulta, filas, backend, ahora)
        _escribir_atomico(ruta, registro)
        hechas_ahora += 1
        if registro["estado"] == "sin_datos":
            r.sin_datos += 1
        else:
            r.descargadas += 1
        log(f"[{i}/{r.total}] {mercado.codigo} {nodo.id} ('{consulta}'): {len(registro['serie'])} meses, {registro['estado']}")
        dormir(pausa + random.uniform(0, jitter))

    return r
