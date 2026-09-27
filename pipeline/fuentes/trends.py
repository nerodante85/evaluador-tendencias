"""Fuente Google Trends, detrás de una interfaz intercambiable.

El repositorio de pytrends está archivado desde el 17 de abril de 2025: hoy
funciona (verificado el 2026-09-26) pero nadie lo mantiene y Google puede
romperlo sin aviso. Por eso el resto del pipeline no conoce pytrends: habla
con cualquier objeto que tenga `nombre` e `interes_en_el_tiempo(...)`. El día
que haga falta cambiar (API oficial, un proveedor de pago, un fork), se
escribe otro adaptador y nada más se toca. Ver docs/v2/00-decisiones.md.

Escala: Trends normaliza cada consulta a 0–100 dentro de su propia ventana.
Cada serie descargada aquí está en su escala propia; sirve para estudiar la
forma en el tiempo (crecimiento, persistencia, estacionalidad), no para
comparar el nivel entre nodos distintos.
"""

CATEGORIA_ROPA = 68  # categoría "Ropa" de Google Trends (igual que la v1)
TIMEFRAME_HISTORIA = "all"  # mensual desde 2004; hace falta para backtestear a 24 meses


class ErrorFuente(Exception):
    """Falló una consulta por una causa que puede ser pasajera."""


class Bloqueado(ErrorFuente):
    """Google está limitando las consultas (HTTP 429). Conviene esperar mucho."""


class BackendPytrends:
    nombre = "pytrends"

    def __init__(self):
        self._clientes = {}

    def _cliente(self, mercado):
        if mercado.codigo not in self._clientes:
            from pytrends.request import TrendReq  # import tardío: las pruebas no lo necesitan

            self._clientes[mercado.codigo] = TrendReq(hl=mercado.hl, tz=mercado.tz)
        return self._clientes[mercado.codigo]

    def interes_en_el_tiempo(self, consulta, mercado, categoria=CATEGORIA_ROPA, timeframe=TIMEFRAME_HISTORIA):
        """Devuelve [{"fecha": "AAAA-MM-01", "valor": int, "parcial": bool}, ...].
        Lista vacía si Trends no tiene datos para esa consulta."""
        try:
            cliente = self._cliente(mercado)
            cliente.build_payload([consulta], cat=categoria, timeframe=timeframe, geo=mercado.codigo)
            df = cliente.interest_over_time()
        except Exception as e:  # pytrends lanza tipos distintos según la falla
            if "429" in str(e):
                raise Bloqueado(str(e)) from e
            raise ErrorFuente(str(e)) from e

        if df.empty:
            return []
        parcial = df["isPartial"] if "isPartial" in df.columns else [False] * len(df)
        return [
            {"fecha": idx.date().isoformat(), "valor": int(v), "parcial": bool(p)}
            for idx, v, p in zip(df.index, df[consulta], parcial)
        ]
