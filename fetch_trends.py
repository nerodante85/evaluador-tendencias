"""
fetch_trends.py  —  v2
----------------------
Conecta el panel "Radar de tendencias" a datos reales de Google Trends
usando la librería no oficial `pytrends`.

QUÉ CAMBIÓ EN LA v2 (y por qué importa para decidir compras)

La v1 medía una sola cosa: el nivel de interés reciente. Eso confunde tres
fenómenos distintos que exigen decisiones opuestas:

  - Una tendencia real que crece.
  - Un pico estacional que se repite todos los años (el lino sube cada
    diciembre; comprar lino en diciembre porque "está subiendo" es comprar
    tarde y caro).
  - Ruido de una serie con poco volumen, donde el número salta sin que
    haya cambiado nada en el mercado.

La v2 calcula cinco variables nuevas para separarlos:

  yoy           Variación contra el MISMO trimestre del año anterior. Es la
                única forma de distinguir crecimiento real de estacionalidad.
                Si el lino sube 40% contra el trimestre pasado pero 0% contra
                el mismo trimestre del año pasado, no está creciendo: es
                diciembre otra vez.

  persistencia  Cuántos de los últimos 12 meses estuvieron por encima de la
                mediana de la serie. Una tendencia sostenida marca alto; un
                pico aislado marca bajo aunque su momentum sea enorme.

  volatilidad   Coeficiente de variación de la serie mensual. Series muy
                erráticas (típico de términos con poco volumen) dan números
                que parecen señal y son ruido.

  volumen       Nivel medio de interés en toda la ventana. Separa "sube
                mucho desde casi nada" de "sube sobre una base real".

  estacional    Marca si el mes más alto de este año coincide con el mes más
                alto del año pasado. Si coincide, el pico es de calendario,
                no de tendencia.

La confianza deja de depender solo de cuántas semanas traen dato: ahora
combina cobertura, volumen y volatilidad. Una serie completa pero errática
y de bajo volumen ya no se reporta como confianza alta.

SALIDAS
  src/data/trends.json        <- lo que LEE EL PANEL. Es la salida que importa.
  trends_live.json            datos completos para auditar (mismo contenido)
  trends_live.js              el array TRENDS, por compatibilidad con el flujo viejo
  historial/AAAA-MM-DD.json   foto de esta corrida, para medir aciertos después

CÓMO CORRERLO
    pip install -r requirements.txt
    python3 fetch_trends.py

Después de correrlo, el panel ya tiene los datos nuevos: `npm run dev` para
verlo local, o `git commit && git push` para que GitHub Pages lo publique.

Notas: Google Trends no tiene API oficial. pytrends simula el navegador, así
que puede devolver 429 si se corre muy seguido. Con una corrida por semana
sobra. El script hace 2 llamadas por señal, así que con 30 señales tarda
alrededor de 10 minutos.
"""

import json
import time
import sys
import statistics
from datetime import datetime, timedelta
from pathlib import Path

try:
    from pytrends.request import TrendReq
except ImportError:
    sys.exit("Falta pytrends. Instálalo con: pip install pytrends")

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "trends_config.json"
OUT_JSON = BASE / "trends_live.json"
OUT_JS = BASE / "trends_live.js"
PANEL_JSON = BASE / "src" / "data" / "trends.json"   # el que lee el panel
HIST_DIR = BASE / "historial"

TIMEFRAME_MONTHS = 24
SECONDS_BETWEEN_REQUESTS = 10
MAX_RETRIES = 3
APPAREL_CATEGORY = 68              # categoría "Ropa" de Google Trends
MIN_SIGNAL = 4                     # por debajo de esto, no hay señal utilizable


def _timeframe():
    end = datetime.now().date()
    start = end - timedelta(days=30 * TIMEFRAME_MONTHS)
    return f"{start.isoformat()} {end.isoformat()}"


def _clean_series(df, query):
    """Quita la semana en curso (isPartial=True): Google todavía no terminó
    de medirla y casi siempre aparece baja, lo que simula una caída."""
    if "isPartial" in df.columns:
        df = df[df["isPartial"] == False]  # noqa: E712
    return df[query]


def _query_series(pytrends, query, geo, category):
    pytrends.build_payload([query], cat=category, timeframe=_timeframe(), geo=geo)
    df = pytrends.interest_over_time()
    if df.empty:
        raise ValueError("Sin datos devueltos")
    series = _clean_series(df, query)
    if series.empty:
        raise ValueError("Sin datos utilizables tras quitar la semana parcial")
    return series


def _fetch_rising(pytrends, query, geo, category):
    """Hasta 3 búsquedas relacionadas en fuerte alza. Es más específico que
    el momentum: dice QUÉ variante concreta se está buscando."""
    try:
        pytrends.build_payload([query], cat=category, timeframe=_timeframe(), geo=geo)
        related = pytrends.related_queries()
        rising = related.get(query, {}).get("rising")
        if rising is None or rising.empty:
            return []
        out = []
        for _, row in rising.head(3).iterrows():
            value = row["value"]
            es_breakout = str(value) == "5000" or row.get("formattedValue") == "Breakout"
            out.append({
                "termino": str(row["query"]),
                "crecimiento": "Breakout" if es_breakout else f"+{value}%",
            })
        return out
    except Exception as e:
        print(f"    (sin búsquedas relacionadas para '{query}': {e})")
        return []


# ---------------------------------------------------------------------------
# Variables nuevas de la v2
# ---------------------------------------------------------------------------

def _yoy(monthly):
    """Variación del último trimestre contra el mismo trimestre del año
    anterior. Devuelve None si la serie no cubre 15 meses, porque sin un año
    completo de referencia el número sería inventado."""
    if len(monthly) < 15:
        return None
    actual = monthly.tail(3).mean()
    previo = monthly.iloc[-15:-12].mean()
    if previo <= 0:
        return None
    return round((actual - previo) / previo * 100)


def _persistencia(monthly):
    """De los últimos 12 meses, cuántos estuvieron por encima de la mediana
    de toda la serie. Un pico aislado da 1 o 2; una tendencia sostenida da 8+."""
    if len(monthly) < 6:
        return 0
    mediana = monthly.median()
    ultimos = monthly.tail(12)
    return int((ultimos > mediana).sum())


def _volatilidad(monthly):
    """Coeficiente de variación: desviación estándar sobre media. Por encima
    de ~0,6 la serie es demasiado errática para leerla como tendencia."""
    vals = [v for v in monthly.tolist() if v is not None]
    if len(vals) < 3:
        return None
    media = statistics.fmean(vals)
    if media <= 0:
        return None
    return round(statistics.pstdev(vals) / media, 2)


def _pico_estacional(monthly, yoy):
    """¿El alza es de calendario y no de tendencia?

    Coincidir el mes pico dos años seguidos no basta: una serie que sube
    todos los meses también tiene su máximo al final de cada ventana, y se
    marcaría como estacional siendo justo lo contrario. Por eso exige tres
    condiciones a la vez: los meses pico coinciden, el pico sobresale de
    verdad sobre la mediana de su año, y no hay crecimiento interanual que
    explique el alza mejor que el calendario."""
    if len(monthly) < 24:
        return False
    reciente = monthly.tail(12)
    anterior = monthly.iloc[-24:-12]
    if reciente.max() <= 0 or anterior.max() <= 0:
        return False

    mismo_mes = reciente.idxmax().month == anterior.idxmax().month
    mediana = reciente.median()
    sobresale = mediana > 0 and reciente.max() >= mediana * 1.3
    sin_crecimiento = yoy is None or yoy < 25

    return bool(mismo_mes and sobresale and sin_crecimiento)


def _confianza(series, monthly, volatilidad):
    """Confianza de la LECTURA, no de la tendencia. Combina tres cosas:
    cuántas semanas traen dato real, qué volumen tiene el término y qué tan
    errática es la serie. Una serie completa pero errática y de bajo volumen
    no merece confianza alta por más puntos que tenga."""
    if len(series) == 0:
        return "baja"

    cobertura = (series > 0).sum() / len(series)
    volumen = statistics.fmean(monthly.tolist()) if len(monthly) else 0

    # Una serie muy errática no sostiene ninguna lectura, tenga el volumen
    # que tenga: el número siguiente puede ser cualquiera.
    if volatilidad is not None and volatilidad > 1.0:
        return "baja"

    if cobertura >= 0.5 and volumen >= 15 and (volatilidad is None or volatilidad <= 0.6):
        return "alta"
    if cobertura >= 0.3 and volumen >= 5 and (volatilidad is None or volatilidad <= 0.85):
        return "media"
    return "baja"


def fetch_one(pytrends, entry):
    """Consulta una señal. Prueba geo local + categoría Ropa; si no hay señal
    suficiente va relajando: sin categoría, y por último alcance mundial."""
    query = entry["query"]
    local_geo = entry.get("geo", "")
    geo_attempts = [local_geo] if local_geo != "" else [""]
    if local_geo != "":
        geo_attempts.append("")

    for geo in geo_attempts:
        for category in (APPAREL_CATEGORY, 0):
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    series = _query_series(pytrends, query, geo, category)
                    monthly = series.resample("MS").mean().dropna()

                    traj = [round(v) for v in monthly.tail(6).tolist()]
                    while len(traj) < 6:
                        traj.insert(0, traj[0] if traj else 0)

                    momentum = round(series.tail(6).mean())
                    if momentum < MIN_SIGNAL and max(traj, default=0) < MIN_SIGNAL:
                        break

                    recent = series.tail(10).mean()
                    previous = series.tail(20).head(10).mean() if len(series) >= 20 else recent
                    delta = recent - previous
                    direction = "subiendo" if delta > 3 else "bajando" if delta < -3 else "estable"

                    volatilidad = _volatilidad(monthly)
                    yoy = _yoy(monthly)

                    time.sleep(SECONDS_BETWEEN_REQUESTS / 2)
                    relacionadas = _fetch_rising(pytrends, query, geo, category)

                    return {
                        "momentum": int(momentum),
                        "dir": direction,
                        "traj": traj,
                        "geo_usado": geo or "global",
                        "sin_datos_suficientes": False,
                        "confianza": _confianza(series, monthly, volatilidad),
                        "relacionadas": relacionadas,
                        # --- variables v2 ---
                        "yoy": yoy,
                        "persistencia": _persistencia(monthly),
                        "volatilidad": volatilidad,
                        "volumen": round(statistics.fmean(monthly.tolist())) if len(monthly) else 0,
                        "estacional": _pico_estacional(monthly, yoy),
                        "meses_serie": len(monthly),
                    }

                except Exception as e:
                    print(f"  intento {attempt}/{MAX_RETRIES} (geo='{geo or 'global'}', cat={category}) falló para '{query}': {e}")
                    time.sleep(SECONDS_BETWEEN_REQUESTS * attempt)

    print(f"  -> '{query}' sin señal suficiente en Trends en ninguna combinación")
    return {
        "momentum": 0, "dir": "estable", "traj": [0] * 6, "geo_usado": None,
        "sin_datos_suficientes": True, "confianza": "baja", "relacionadas": [],
        "yoy": None, "persistencia": 0, "volatilidad": None, "volumen": 0,
        "estacional": False, "meses_serie": 0,
    }


def _js_value(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return json.dumps(v, ensure_ascii=False)


def escribir_js(results, generated_at):
    items = []
    for r in results:
        relacionadas_js = "[%s]" % ", ".join(
            "{ termino: %s, crecimiento: %s }" % (
                json.dumps(x["termino"], ensure_ascii=False),
                json.dumps(x["crecimiento"]),
            )
            for x in r.get("relacionadas", [])
        )
        items.append(
            "  { id: %d, cat: %s, scope: %s, name: %s, code: %s, %s"
            "momentum: %d, dir: %s, note: %s, source: %s, traj: %s, "
            "sinDatosSuficientes: %s, geoUsado: %s, confianza: %s, "
            "yoy: %s, persistencia: %d, volatilidad: %s, volumen: %d, estacional: %s, "
            "relacionadas: %s },"
            % (
                r["id"],
                json.dumps(r["cat"], ensure_ascii=False),
                json.dumps(r["scope"], ensure_ascii=False),
                json.dumps(r["name"], ensure_ascii=False),
                json.dumps(r["code"], ensure_ascii=False),
                (f"swatch: {json.dumps(r['swatch'])}, " if r.get("swatch") else ""),
                r["momentum"],
                json.dumps(r["dir"], ensure_ascii=False),
                json.dumps(r["note"], ensure_ascii=False),
                json.dumps(r["source"], ensure_ascii=False),
                json.dumps(r["traj"]),
                _js_value(r["sin_datos_suficientes"]),
                _js_value(r.get("geo_usado")),
                json.dumps(r.get("confianza", "baja")),
                _js_value(r.get("yoy")),
                r.get("persistencia", 0),
                _js_value(r.get("volatilidad")),
                r.get("volumen", 0),
                _js_value(r.get("estacional", False)),
                relacionadas_js,
            )
        )
    OUT_JS.write_text(
        "// Generado por fetch_trends.py v2 — %s\nconst TRENDS = [\n%s\n];\n" % (generated_at, "\n".join(items)),
        encoding="utf-8",
    )


def escribir_panel(results, generated_at):
    """Escribe el JSON que el panel importa directamente.

    El panel usa nombres en camelCase (`sinDatosSuficientes`, `geoUsado`),
    que es como venían escritos a mano en el .jsx original; los campos nuevos
    de la v2 conservan su nombre. Traducir aquí evita tener que tocar el
    panel cada vez que cambia el script.
    """
    trends = []
    for r in results:
        item = {
            "id": r["id"], "cat": r["cat"], "scope": r["scope"], "name": r["name"],
            "code": r["code"], "momentum": r["momentum"], "dir": r["dir"],
            "note": r["note"], "source": r["source"], "traj": r["traj"],
            "sinDatosSuficientes": r["sin_datos_suficientes"],
            "geoUsado": r.get("geo_usado"),
            "confianza": r.get("confianza", "baja"),
            "yoy": r.get("yoy"),
            "persistencia": r.get("persistencia", 0),
            "volatilidad": r.get("volatilidad"),
            "volumen": r.get("volumen", 0),
            "estacional": r.get("estacional", False),
            "relacionadas": r.get("relacionadas", []),
        }
        if r.get("swatch"):
            item["swatch"] = r["swatch"]
        trends.append(item)

    PANEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    PANEL_JSON.write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "source": "Google Trends (pytrends, no oficial)",
                "version": 2,
                "trends": trends,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def guardar_historial(results, generated_at):
    """Foto de esta corrida. Con dos o tres fotos ya se puede medir si el
    panel acierta: qué recomendó, y qué pasó con esa señal después."""
    HIST_DIR.mkdir(exist_ok=True)
    fecha = datetime.now().date().isoformat()
    resumen = [
        {
            "id": r["id"], "name": r["name"], "momentum": r["momentum"], "dir": r["dir"],
            "confianza": r.get("confianza"), "yoy": r.get("yoy"),
            "persistencia": r.get("persistencia"), "volatilidad": r.get("volatilidad"),
            "volumen": r.get("volumen"), "estacional": r.get("estacional"),
        }
        for r in results
    ]
    destino = HIST_DIR / f"{fecha}.json"
    destino.write_text(
        json.dumps({"generated_at": generated_at, "señales": resumen}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destino


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    pytrends = TrendReq(hl="es-CO", tz=300)

    results = []
    for i, entry in enumerate(config, 1):
        print(f"[{i}/{len(config)}] {entry['name']} ({entry['query']}) geo='{entry.get('geo','')}'")
        merged = dict(entry)
        merged.update(fetch_one(pytrends, entry))
        results.append(merged)
        time.sleep(SECONDS_BETWEEN_REQUESTS)

    generated_at = datetime.now().isoformat(timespec="minutes")

    con_datos = sum(1 for r in results if not r["sin_datos_suficientes"])
    alta = sum(1 for r in results if r.get("confianza") == "alta")
    creciendo_yoy = sum(1 for r in results if (r.get("yoy") or 0) > 10)
    estacionales = sum(1 for r in results if r.get("estacional"))

    print(f"\n{con_datos}/{len(results)} señales con datos suficientes.")
    print(f"{alta}/{len(results)} con confianza alta (cobertura + volumen + estabilidad).")
    print(f"{creciendo_yoy}/{len(results)} creciendo más de 10% contra el año pasado.")
    print(f"{estacionales}/{len(results)} con pico estacional — su alza es de calendario, no de tendencia.")

    payload = {
        "generated_at": generated_at,
        "source": "Google Trends (pytrends, no oficial)",
        "version": 2,
        "trends": results,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_js(results, generated_at)
    escribir_panel(results, generated_at)
    hist = guardar_historial(results, generated_at)

    print(f"\nGuardado: {PANEL_JSON}  <- el panel ya lee estos datos")
    print(f"Guardado: {OUT_JSON}")
    print(f"Guardado: {OUT_JS}  (formato viejo, por si lo necesitas)")
    print(f"Guardado: {hist}  (foto para medir aciertos más adelante)")
    print("\nSiguiente paso: 'npm run dev' para verlo local, o 'git add -A && git commit && git push' para publicarlo.")


if __name__ == "__main__":
    main()
