# Verificación metodológica del ERI indicativo

**Fecha:** 5 de noviembre de 2026  
**Alcance:** pesos, normalización, clases, fuentes, presentación y separación de índices.

## Dictamen

Los pesos originales se conservan y suman uno:

| Componente | Peso |
|---|---:|
| Integridad estructural | 35 % |
| Conectividad local | 25 % |
| Estabilidad topográfica | 20 % |
| Proximidad riparia | 20 % |

`eri_indicativo.py` limita cada componente al intervalo [0, 1], aplica la suma
ponderada y vuelve a clasificar el resultado en cinco intervalos. El resultado declara
`participa_en_prioridad=False`; por tanto, permanece separado del índice de indicios
territoriales y de las métricas temporales de conectividad.

## Construcción de los componentes

| Componente | Procedimiento actual | Fuente/escala | Limitación |
|---|---|---|---|
| Integridad estructural | 50 % altura GEDI normalizada a 35 m + 50 % probabilidad de árboles | GEDI/OpenForis + Dynamic World | Donde GEDI no cubre, se usa probabilidad de árboles como respaldo; no es una medición completa de estructura |
| Conectividad local | Proporción de píxeles `trees ≥ 0,5` en ventana circular de 1,5 km | Dynamic World, referencia 2024 | Proxy local; no es ECA ni conectividad funcional |
| Estabilidad topográfica | `1 - pendiente_normalizada × (1 - p_árboles)` | Copernicus DEM GLO-30 | Regla heurística, no modelo de estabilidad de laderas validado |
| Proximidad riparia | Decaimiento lineal hasta 1.000 m desde cauces con ≥1 km² de área aportante | MERIT Hydro | Depende del umbral de cauce y no valida condición ribereña local |

El resumen se calcula aproximadamente a 90 m. El año de referencia se fija en 2024.

## Normalización y clasificación

`limitar_01()` convierte valores no numéricos en cero y restringe todo valor a [0, 1].
Las clases son:

- muy baja: [0,00, 0,25);
- baja: [0,25, 0,40);
- media: [0,40, 0,60);
- alta: [0,60, 0,75);
- muy alta: [0,75, 1,00].

La prueba de fronteras confirma 0,25, 0,40, 0,60, 0,75 y 1,00. Otra prueba verifica
un caso conocido cuyo promedio ponderado es exactamente 0,60. También se prueba la
identificación del componente limitante y que el ERI no modifica la prioridad.

## Separación conceptual

- **ERI:** lectura complementaria de condición ecológica relativa en un año de
  referencia; no se fuerza a ser anual.
- **Índice de indicios territoriales:** reglas de preevaluación por fuente; no recibe
  puntos del ERI.
- **Conectividad temporal:** red de parches recalculada para 2020 y 2025; no se usa
  como sustituto del componente local del ERI.

Esta separación está explícita en `eri_indicativo.py`, `app_experiencia.py` y las
pruebas de interfaz/metodología.

## Estado de validación

| Componente | Estado |
|---|---|
| Pesos y suma ponderada | Implementado y verificado por pruebas |
| Límite [0, 1] y clases | Implementado y verificado por pruebas |
| Cálculo Earth Engine de componentes | Implementado; verificado operativamente en la aplicación |
| Validez ecológica de los pesos | Sin validación independiente documentada |
| Umbrales de 35 m, 1,5 km, 1.000 m y 1 km² | Decisiones metodológicas documentadas, sin calibración local independiente |
| Exactitud espacial de las clases ERI | Pendiente de validación de campo |

## Riesgos y recomendaciones

1. Mantener siempre las palabras **indicativo** y **complementario**.
2. No presentar el valor como probabilidad, exactitud ni resiliencia observada.
3. Conservar los cuatro componentes visibles para que el usuario pueda interpretar
   qué limita el resultado.
4. Publicar los parámetros y las fuentes junto a cada descarga.
5. Antes de uso decisorio, validar los pesos y umbrales con expertos, parcelas y casos
   de campo independientes en la CHCP.
6. No convertir el ERI en serie temporal hasta disponer de insumos equivalentes y una
   metodología temporal validada.

## Conclusión

El ERI está correctamente implementado respecto de su especificación interna y está
bien separado de los demás indicadores. Está apto como **orientación exploratoria**,
no como resultado científico validado en campo ni como índice temporal.
