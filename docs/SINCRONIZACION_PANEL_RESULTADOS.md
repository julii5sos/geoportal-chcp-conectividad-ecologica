# Sincronización Plataforma → Panel

## Flujo implementado

1. La Plataforma envía territorio, geometría, fuente, período, parámetros y versión
   implícita del algoritmo.
2. `ResultCache` deduplica por firma completa y mantiene el último resultado por
   identificador territorial.
3. La respuesta devuelve `result_id`; el navegador conserva ese identificador,
   el territorio y el período en `localStorage`.
4. El Panel consulta el resultado exacto por ID o el último resultado en caché para
   ese territorio. Abrir el Panel **no ejecuta Earth Engine**.
5. Un evento `storage` actualiza un Panel abierto en otra pestaña.
6. Un contador de solicitud y una huella de selección impiden que una respuesta
   antigua sustituya la selección activa.

Estados visibles: disponible, procesando, no calculado, sin observaciones, error y
fuente no configurada. Las tarjetas muestran fuente/período cuando hay resultado.

## Límite de desarrollo

La caché es RAM de proceso, con TTL y límite de entradas. No es persistencia de
Cloud Run. Para publicación se recomienda:

- Firestore para metadatos, firma, territorio, fuente, versión, estado y fechas.
- Cloud Storage para JSON/GeoJSON/ZIP y productos precalculados.
- URL firmada o endpoint autenticado para descargas.
- tarea asíncrona para cálculos largos; nunca confiar en memoria entre instancias.

