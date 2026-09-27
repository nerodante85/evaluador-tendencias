# Generación de documentación — no aplica

El skill de auditoría pide este archivo para aplicaciones que generan documentos de participación (ej. propuestas para licitaciones, con firmas, anexos, datos de terceros). Se revisó el repositorio completo buscando cualquier flujo de generación de documentos (PDF, DOCX, formularios de envío, exportables con datos de la empresa del usuario) y **no existe ninguno**.

Lo que la aplicación sí produce son archivos JSON/Markdown internos escritos por el propio pipeline (`docs/v2/reporte-*.md`, `data/v2/*.json`) — estos no se le entregan a un tercero como "documento oficial", son la salida técnica que alimenta el panel y la documentación del proyecto. No están sujetos a la regla de oro de esta sección (un documento generado no puede contener información que la app no pueda justificar) porque no hay ningún documento de cara a un tercero que la app "redacte" — el panel solo muestra números y texto de plantilla fija, ya cubierto en `AI-RELIABILITY-REPORT.md`.

Si en el futuro el producto agrega, por ejemplo, un reporte PDF descargable para un cliente con el "caso" de una categoría específica, este archivo debería reactivarse y auditarse con las mismas reglas: cada dato citado debe trazarse hasta una fuente real (ver `DATA-TRACEABILITY-REPORT.md` como plantilla de cómo hacerlo).
