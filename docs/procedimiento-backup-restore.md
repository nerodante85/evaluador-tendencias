# Backup y restauración de datos

No hay un sistema de respaldo dedicado — pero no hace falta uno nuevo: **git ya cumple ese rol** para todo lo que importa, porque todo lo que importa ya está versionado. Este documento existía como hueco en la auditoría del 2026-09-27 (`AUDIT-REPORT.md`, sección 31: "el procedimiento no está escrito") — no porque faltara la capacidad de recuperación, sino porque nadie había dejado por escrito cómo usarla.

## Qué está respaldado, y dónde

| Qué | Dónde vive | Se puede regenerar sin git? |
|---|---|---|
| Historia cruda de Trends (v2) | `data/v2/raw/trends/**/*.json` (474 archivos, commiteados) | Sí, volviendo a correr `python -m pipeline.cli historia` — pero tarda horas y depende de que `pytrends` siga funcionando ese día. |
| Foto de cada corrida (v1) | `historial/*.json` | **No.** Es evidencia histórica — si se pierde, se pierde la comparación con esa fecha para siempre (por eso `CLAUDE.md` prohíbe tocar esta carpeta). |
| Lo que lee el panel (v1) | `src/data/trends.json`, `src/data/macro.json` | Sí, volviendo a correr `fetch_trends.py`/`fetch_macro.py` — pero el resultado sería la corrida de HOY, no la de la fecha que se perdió. |
| Lo que lee el panel (v2) | `src/data/v2/catalogo.json`, `data/v2/{calidad,senales,backtesting,trend_score,trend_score_pesos}.json` | Sí, encadenando `python -m pipeline.cli {calidad,senales,backtest,trend_score,exportar}` — determinístico a partir de `data/v2/raw/` (semillas fijas en el muestreo), así que da el mismo resultado si no cambió el código ni la taxonomía. |
| Taxonomía, código, documentación | `taxonomia/`, `pipeline/`, `src/`, `docs/` | Es código — vive en git como cualquier otro archivo del repositorio. |
| Criterio editorial (v1) | `src/data/plan.json`, `src/data/contexto.json` | No — es trabajo manual de Ricardo, sin fuente automática que lo regenere. |
| Credenciales (MercadoLibre) | `data/v2/.secretos/` | **Nunca se sube a git a propósito** (`.gitignore`) — no es parte de este backup. Si se pierde, se vuelve a pedir el token con `python -m pipeline.cli mercadolibre-auth`. |

## Cómo restaurar

**Un archivo o carpeta se corrompió o se borró por error, y el cambio ya se commiteó:**

```bash
git log --oneline -- ruta/al/archivo    # encontrar el último commit bueno
git checkout <hash-del-commit> -- ruta/al/archivo
```

**Se necesita volver todo el repositorio a como estaba en una fecha:**

```bash
git log --oneline --before="2026-09-12"   # encontrar el commit de esa fecha
git checkout <hash>   # mirar en ese estado, sin moverse de main
git switch main       # volver
```

**Se perdió `data/v2/raw/` completo (el escenario más caro):** si el commit más reciente lo tiene, `git checkout` lo trae de vuelta tal cual (opción de arriba). Si de verdad no está en ningún commit, hay que volver a correr `python -m pipeline.cli historia` desde cero — es reanudable (`historia.py`), así que se puede cortar y seguir después, pero vuelve a tardar horas y a depender de que `pytrends` esté funcionando ese día.

**`src/data/v2/catalogo.json` (o cualquier salida de `data/v2/*.json`) quedó mal o desactualizado:** nunca se edita a mano — se regenera corriendo el pipeline completo en orden:

```bash
python -m pipeline.cli calidad
python -m pipeline.cli senales
python -m pipeline.cli backtest --series 280 --cortes 10   # tarda ~15 min
python -m pipeline.cli trend_score
python -m pipeline.cli exportar
```

## Lo que este procedimiento NO cubre

- **`historial/*.json` no tiene backup fuera de git.** Si el repositorio completo se pierde (no solo un checkout local, sino también GitHub), esa evidencia se pierde para siempre. GitHub en sí es la única copia fuera del computador de Ricardo hoy — no hay un tercer lugar.
- No hay backup automático ni programado — todo esto es manual, a pedido, cuando alguien lo necesita. Consistente con el resto del proyecto (sin monitorización activa, ver `AUDIT-REPORT.md` sección 32) pero vale la pena saberlo antes de asumir que "está respaldado" significa "se restaura solo".
