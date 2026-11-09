# Validación del asset oficial de cobertura 2021

Fecha: 2026-11-07
Proyecto Earth Engine: `geoportal-513817`
Asset: `projects/geoportal-513817/assets/SINIA_2021_COBERTURA_GENERAL_VECTOR`

## Resultado

El asset nuevo es accesible con la identidad local autorizada, es una tabla de
Earth Engine utilizable como `ee.FeatureCollection` y puede alimentar sin cambios
de fórmula el motor original de fragmentación y conectividad.

## Evidencia del asset

- Tipo informado por Earth Engine: `TABLE`.
- Número total de entidades: 28 288.
- Tipo de la primera geometría: `Polygon`.
- Campos observados: `Area_ha`, `Categoria`, `ID_PARTE`, `system:index`.
- Categorías y número de entidades:
  - `Bosques y Otras Tierras Boscosas`: 10 994.
  - `Otras Tierras`: 12 797.
  - `Aguas Continentales`: 4 497.

La clase forestal coincide literalmente con
`CAMPO_COBERTURA_BOSQUE_2021 = "Categoria"` y
`VALOR_COBERTURA_BOSQUE_2021 = "Bosques y Otras Tierras Boscosas"` del análisis
original. No se cambió la definición temática.

## Prueba territorial controlada

Área: subcuenca `Qda. Bonita`.

| Indicador | Resultado |
|---|---:|
| Superficie del AOI | 509.9985 ha |
| Bosques y otras tierras boscosas | 379.2601 ha (74.3649 %) |
| Otras tierras | 128.7998 ha (25.2549 %) |
| Aguas continentales | 1.9387 ha (0.3801 %) |
| Superficie clasificada | 509.9985 ha |
| Superficie sin clasificar | 0 ha |

La consulta también produjo una URL de teselas de Earth Engine para representar
las tres categorías en el mapa.

## Fragmentación y conectividad

Se ejecutó `analizar_estructura_cobertura("official_2021", ...)` con el motor
existente, distancia máxima de 500 m, área mínima de parche 0 ha y contexto de
500 m.

| Métrica | Resultado |
|---|---:|
| Parches dentro del AOI | 6 |
| Superficie forestal estructural | 377.6973 ha |
| Densidad de parches | 1.1813 por 100 ha |
| Densidad de borde | 91.5251 m/ha |
| Nodos | 6 |
| Aristas | 9 |
| Componentes | 1 |
| Parches aislados | 0 |
| Distancia media de conexiones | 174.90 m |
| Distancia máxima de conexiones | 475.19 m |

La diferencia pequeña entre la superficie temática y la estructural responde al
flujo geométrico del motor (simplificación, reparación, recorte y representación
de parches), no a una reclasificación de la cobertura.

## Alcance de la equivalencia

Se confirmó:

1. equivalencia temática del campo y la clase forestal;
2. cobertura completa del AOI de prueba por las tres categorías;
3. compatibilidad geométrica con el mismo motor de parches y red;
4. lectura desde `geoportal-513817`, sin dependencia del proyecto personal
   anterior.

No se puede confirmar igualdad entidad por entidad frente a
`CBOTB_2021_CHCP_15KM_GEE_FINAL`, porque ese asset ya no existe o no es accesible
para realizar la comparación directa. Esta limitación debe conservarse en la
trazabilidad científica.

## Configuración y seguridad

`estructura_cobertura.py` toma el identificador del catálogo central
`catalogo_assets_sinia.py`. La variable `SINIA_2021_FOREST_ASSET` queda disponible
solo como sobreescritura operativa. No se incorporaron claves ni credenciales.

La prueba confirma lectura para la identidad local. La cuenta de servicio de un
despliegue futuro deberá recibir permiso de lectura del asset y validarse mediante
Application Default Credentials antes de publicar; esta tarea no modifica IAM.

## Interfaz y diagnóstico

Los errores conocidos de acceso se convierten en un mensaje público compacto:

> No se pudo cargar la cobertura forestal oficial 2021. Los análisis de
> fragmentación y conectividad no están disponibles temporalmente.

El identificador y la excepción completa se registran únicamente en el servidor.
La notificación se presenta como un aviso pequeño en la esquina inferior derecha
y no bloquea el mapa.
