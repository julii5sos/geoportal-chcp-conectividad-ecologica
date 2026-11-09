# Comparación visual — Fase 4

Fecha de validación: 5 de noviembre de 2026
Rama: `feature/interfaz-html-definitiva`

## Referencias utilizadas

El HTML de `conectividad_canal(2).zip` fue la referencia principal para las propiedades visuales. El video `Panel de cuencas · Conectividad Panamá` se revisó completo mediante fotogramas para comprobar la apertura de paneles, la navegación, el asistente y la aparición de resultados.

| Estado original | Implementación Fase 4 |
|---|---|
| [Inicio del video](../artifacts/reference/video-panel-inicio.jpg) | [Inicio actual](../artifacts/screenshots/fase4-inicio-completo.png) |
| [Explorador original](../artifacts/reference/video-plataforma.jpg) | [Explorador actual](../artifacts/screenshots/fase4-plataforma-final.png) |
| [Asistente original](../artifacts/reference/video-asistente.jpg) | [Asistente actual](../artifacts/screenshots/fase4-asistente-final-real.png) |
| [Resultados originales](../artifacts/reference/video-resultados.jpg) | [Resultado científico actual](../artifacts/screenshots/fase4-resultados-reales-miraflores.png) |
| — | [Vista móvil real a 375 × 812 px](../artifacts/screenshots/fase4-inicio-375.png) |

## Diferencias corregidas

| Aspecto | Antes de la Fase 4 | Estado actual |
|---|---|---|
| Encabezado | Barra Streamlit y navegación genérica | Encabezado azul de dos niveles, identidad CHCP, navegación horizontal y menú adaptable |
| Pantalla inicial | Tarjetas y guía vertical | Portada territorial con resumen, mapa CHCP y acceso directo al explorador |
| Explorador | Flujo vertical con desplazamiento largo | Panel lateral de 340 px, mapa central amplio y resultados a la derecha |
| Capas | Controles dispersos | Pestañas Capas, Filtros y Mapas base; grupos jerárquicos e interruptores |
| Análisis | Formulario expuesto permanentemente | Asistente modal en cuatro pasos con estado conservado |
| Área | Orden no alineado con la especificación | Dibujo, subcuenca y CHCP completa, en ese orden; no se incorporaron fincas |
| Resultados | Debajo del mapa | Panel derecho con métricas, barras comparativas, método, advertencia y descarga |
| Ciencia | Riesgo de confundir selección y recálculo | La ejecución llama al motor temporal real y solo muestra resultados tras completar el cálculo |
| Acciones | Botones repartidos | Acción principal fija y descarga fija cuando existe un resultado; descarga adicional en el panel |
| Móvil | Sin validación específica | Captura real a 375 px, navegación compacta y contenido sin desplazamiento horizontal |

## Validación funcional

- El asistente conserva los cuatro tipos de análisis: cobertura, fragmentación, conectividad e integral.
- JRC TMF y ESRI permanecen como metodologías separadas, con sus años válidos.
- Fragmentación y conectividad reutilizan el motor científico de la Fase 3 sin modificar fórmulas.
- El ERI se mantiene como evaluación complementaria independiente; no se convirtió en un índice anual.
- Una ejecución real JRC TMF 2020–2025 sobre una subcuenca completó la recuperación de Earth Engine, la vectorización de parches, la red de conectividad, las transiciones, las métricas y el ZIP metodológico.
- El mapa permite alternar transiciones, año inicial y año final.
- La descarga contiene estadísticas, GeoJSON y metadatos ya generados por el motor temporal.

## Diferencias visuales todavía presentes

1. El control nativo de plegado de la barra lateral y algunos controles de formulario conservan el renderizado de Streamlit.
2. La navegación superior reproduce la estructura y los destinos, pero no implementa todos los submenús extensos del prototipo estático porque no existen destinos funcionales equivalentes.
3. Los gráficos usan Altair para conservar accesibilidad, tabla de datos y descarga; por ello, sus menús internos no son idénticos a los del HTML.
4. En móvil, el panel lateral se transforma en el cajón nativo de Streamlit, en lugar de replicar una aplicación JavaScript independiente.

Estas diferencias no alteran el cálculo científico ni producen controles decorativos. Una migración futura a un frontend JavaScript podría eliminarlas, pero no es necesaria para ejecutar de forma robusta el motor Python actual.
