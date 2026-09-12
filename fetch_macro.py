"""
fetch_macro.py
--------------
Trae la TRM (Tasa Representativa del Mercado) oficial de Colombia para el
panel "Radar de tendencias — Conecta Moda", usando la API abierta y
gratuita del gobierno colombiano (datos.gov.co), con datos que vienen
directamente del Banco de la República / Superintendencia Financiera.

Nota sobre la versión anterior de este script: usaba la API de
Frankfurter (tasas del Banco Central Europeo), que NO incluye el peso
colombiano — por eso daba error 404. Esta versión usa la fuente oficial
correcta para COP.

Por qué importa para comprar telas: la mayoría de telas técnicas,
sintéticas y muchos insumos se cotizan o importan en dólares. Si el peso
se debilita (TRM sube), comprar temprano puede ahorrar plata; si se
fortalece (TRM baja), capaz conviene esperar.

QUÉ HACE
1. Pide la TRM del día y los últimos ~120 registros (cubre ~90 días
   corridos, ya que la TRM se publica todos los días, incluidos festivos,
   usando el último valor hábil).
2. Calcula:
     - TRM actual
     - variación % en 30 días
     - dirección: "subiendo" (dólar más caro / peso se debilita),
       "bajando" (dólar más barato / peso se fortalece), "estable"
     - trayectoria de 6 puntos para el sparkline
3. Escribe:
     - src/data/macro.json  <- lo que LEE EL PANEL
     - macro_live.json      (mismo contenido, formato viejo)
     - macro_live.js        (bloque MACRO, por compatibilidad)

CÓMO CORRERLO
    pip install -r requirements.txt
    python3 fetch_macro.py

Fuente: https://www.datos.gov.co/resource/32sa-8pi3.json
(dataset "Tasa de Cambio Representativa del Mercado - TRM", Banco de la
República / Superintendencia Financiera de Colombia). Es un portal de
datos abiertos del gobierno: gratis, sin llave, aunque con límite de
solicitudes razonable — no lo corras más de un par de veces al día.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Falta requests. Instálalo con: pip install requests")

BASE = Path(__file__).parent
OUT_JSON = BASE / "macro_live.json"
OUT_JS = BASE / "macro_live.js"
PANEL_JSON = BASE / "src" / "data" / "macro.json"   # el que lee el panel

TRM_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"
TRM_FUENTE = "TRM oficial · datos.gov.co (Banco de la República / Superfinanciera)"


def fetch_trm_history(limit=120):
    params = {"$limit": str(limit), "$order": "vigenciadesde DESC"}
    resp = requests.get(TRM_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("La API de datos.gov.co no devolvió registros de TRM. Revisa tu conexión o intenta más tarde.")
    # vienen del más reciente al más antiguo; los ordenamos cronológicamente
    series = [(row["vigenciadesde"][:10], float(row["valor"])) for row in data]
    series.sort(key=lambda x: x[0])
    return series


def build_traj(series, points=6):
    if len(series) < points:
        return [round(v) for _, v in series] + [round(series[-1][1])] * (points - len(series))
    step = len(series) / points
    out = []
    for i in range(points):
        idx = min(int(i * step), len(series) - 1)
        out.append(round(series[idx][1]))
    out[-1] = round(series[-1][1])
    return out


def main():
    print("Consultando TRM oficial (datos.gov.co / Banco de la República)...")
    series = fetch_trm_history(120)

    current = series[-1][1]
    idx_30d = max(0, len(series) - 30)
    thirty_days_ago = series[idx_30d][1]
    change_pct = ((current - thirty_days_ago) / thirty_days_ago) * 100

    if change_pct > 1:
        direction = "subiendo"   # dólar más caro / peso se debilita
    elif change_pct < -1:
        direction = "bajando"    # dólar más barato / peso se fortalece
    else:
        direction = "estable"

    traj = build_traj(series)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="minutes"),
        "source": TRM_FUENTE,
        "usdcop": {
            "actual": round(current, 1),
            "cambio_30d_pct": round(change_pct, 2),
            "direccion": direction,
            "trayectoria": traj,
            "fecha_dato": series[-1][0],
            "fuente": TRM_FUENTE,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    PANEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    PANEL_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Guardado: {PANEL_JSON}  <- el panel ya lee este dato")
    print(f"Guardado: {OUT_JSON}")
    print(f"TRM actual: ${payload['usdcop']['actual']:,.1f}  |  30d: {payload['usdcop']['cambio_30d_pct']}%  |  {direction}")

    js_content = (
        "// Generado por fetch_macro.py — %s\n"
        "const MACRO = {\n"
        "  usdcop: {\n"
        "    actual: %s,\n"
        "    cambio30d: %s,\n"
        "    direccion: %s,\n"
        "    trayectoria: %s,\n"
        "    fechaDato: %s,\n"
        "    fuente: %s,\n"
        "    live: true,\n"
        "  },\n"
        "};\n"
        % (
            payload["generated_at"],
            json.dumps(payload["usdcop"]["actual"]),
            json.dumps(payload["usdcop"]["cambio_30d_pct"]),
            json.dumps(payload["usdcop"]["direccion"], ensure_ascii=False),
            json.dumps(payload["usdcop"]["trayectoria"]),
            json.dumps(payload["usdcop"]["fecha_dato"]),
            json.dumps(payload["usdcop"]["fuente"], ensure_ascii=False),
        )
    )
    OUT_JS.write_text(js_content, encoding="utf-8")
    print(f"Guardado: {OUT_JS}  (formato viejo, por si lo necesitas)")


if __name__ == "__main__":
    main()
