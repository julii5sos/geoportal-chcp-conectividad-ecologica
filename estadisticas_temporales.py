"""Estadísticas comparables e interpretación del análisis temporal.

Este módulo es deliberadamente independiente de Streamlit y Earth Engine. Recibe
superficies ya calculadas sobre máscaras válidas, comprueba sus identidades y
deriva porcentajes con denominadores explícitos. También genera una lectura
determinista y prudente de cobertura, fragmentación y conectividad estructural.
"""

from __future__ import annotations

from math import isfinite
from typing import Any


def _numero_no_negativo(nombre: str, valor: float) -> float:
    numero = float(valor)
    if not isfinite(numero) or numero < 0:
        raise ValueError(f"{nombre} debe ser un número finito no negativo.")
    return numero


def _porcentaje(parte: float, total: float) -> float | None:
    if total <= 0:
        return None
    return round(parte / total * 100, 4)


def _periodo(
    *,
    anio: int,
    area_geometrica_ha: float,
    area_valida_ha: float,
    bosque_ha: float,
    tolerancia_ha: float,
) -> dict[str, float | int | None]:
    if area_valida_ha > area_geometrica_ha + tolerancia_ha:
        raise ValueError(
            f"El área válida de {anio} supera el área geométrica fuera de tolerancia."
        )
    if bosque_ha > area_valida_ha + tolerancia_ha:
        raise ValueError(
            f"El bosque de {anio} supera el área válida fuera de tolerancia."
        )
    no_bosque_ha = max(0.0, area_valida_ha - bosque_ha)
    sin_datos_ha = max(0.0, area_geometrica_ha - area_valida_ha)
    return {
        "anio": int(anio),
        "area_geometrica_ha": round(area_geometrica_ha, 4),
        "area_valida_ha": round(area_valida_ha, 4),
        "bosque_ha": round(bosque_ha, 4),
        "no_bosque_ha": round(no_bosque_ha, 4),
        "sin_datos_ha": round(sin_datos_ha, 4),
        "porcentaje_bosque": _porcentaje(bosque_ha, area_valida_ha),
        "porcentaje_no_bosque": _porcentaje(no_bosque_ha, area_valida_ha),
        "porcentaje_area_valida": min(
            100.0, _porcentaje(area_valida_ha, area_geometrica_ha) or 0.0
        ) if area_geometrica_ha > 0 else None,
        "porcentaje_sin_datos": _porcentaje(sin_datos_ha, area_geometrica_ha),
    }


def construir_estadisticas_cobertura(
    *,
    anio_inicial: int,
    anio_final: int,
    area_geometrica_ha: float,
    area_valida_inicial_ha: float,
    bosque_inicial_ha: float,
    area_valida_final_ha: float,
    bosque_final_ha: float,
    area_valida_comun_ha: float,
    bosque_estable_ha: float,
    perdida_bosque_ha: float,
    ganancia_bosque_ha: float,
    no_bosque_estable_ha: float,
    tolerancia_ha: float = 0.01,
    tolerancia_geometria_ha: float | None = None,
) -> dict[str, Any]:
    """Valida y deriva los indicadores de cobertura y transición.

    Los porcentajes anuales usan el área válida de su año. Los cambios usan solo
    el área válida común, de modo que una diferencia de máscara nunca se presenta
    como pérdida o ganancia de bosque.
    """

    nombres = {
        "area_geometrica_ha": area_geometrica_ha,
        "area_valida_inicial_ha": area_valida_inicial_ha,
        "bosque_inicial_ha": bosque_inicial_ha,
        "area_valida_final_ha": area_valida_final_ha,
        "bosque_final_ha": bosque_final_ha,
        "area_valida_comun_ha": area_valida_comun_ha,
        "bosque_estable_ha": bosque_estable_ha,
        "perdida_bosque_ha": perdida_bosque_ha,
        "ganancia_bosque_ha": ganancia_bosque_ha,
        "no_bosque_estable_ha": no_bosque_estable_ha,
        "tolerancia_ha": tolerancia_ha,
    }
    valores = {nombre: _numero_no_negativo(nombre, valor) for nombre, valor in nombres.items()}
    area_geometrica = valores["area_geometrica_ha"]
    area_comun = valores["area_valida_comun_ha"]
    tolerancia = valores["tolerancia_ha"]
    tolerancia_geometria = _numero_no_negativo(
        "tolerancia_geometria_ha",
        tolerancia if tolerancia_geometria_ha is None else tolerancia_geometria_ha,
    )
    if area_comun > min(
        valores["area_valida_inicial_ha"], valores["area_valida_final_ha"]
    ) + tolerancia:
        raise ValueError("El área válida común supera el área válida de un período.")

    inicial = _periodo(
        anio=anio_inicial,
        area_geometrica_ha=area_geometrica,
        area_valida_ha=valores["area_valida_inicial_ha"],
        bosque_ha=valores["bosque_inicial_ha"],
        tolerancia_ha=tolerancia_geometria,
    )
    final = _periodo(
        anio=anio_final,
        area_geometrica_ha=area_geometrica,
        area_valida_ha=valores["area_valida_final_ha"],
        bosque_ha=valores["bosque_final_ha"],
        tolerancia_ha=tolerancia_geometria,
    )

    estable = valores["bosque_estable_ha"]
    perdida = valores["perdida_bosque_ha"]
    ganancia = valores["ganancia_bosque_ha"]
    no_bosque_estable = valores["no_bosque_estable_ha"]
    suma_transiciones = estable + perdida + ganancia + no_bosque_estable
    diferencia_cierre = suma_transiciones - area_comun
    if abs(diferencia_cierre) > tolerancia:
        raise ValueError(
            "Las cuatro transiciones no reproducen el área válida común: "
            f"diferencia {diferencia_cierre:.4f} ha."
        )

    bosque_inicial_comparable = estable + perdida
    bosque_final_comparable = estable + ganancia
    no_bosque_inicial_comparable = no_bosque_estable + ganancia
    no_bosque_final_comparable = no_bosque_estable + perdida
    cambio_neto = ganancia - perdida
    bosque_inicial_pct = _porcentaje(bosque_inicial_comparable, area_comun)
    bosque_final_pct = _porcentaje(bosque_final_comparable, area_comun)
    cambio_pp = (
        round(bosque_final_pct - bosque_inicial_pct, 4)
        if bosque_inicial_pct is not None and bosque_final_pct is not None
        else None
    )

    return {
        "periodos": {str(anio_inicial): inicial, str(anio_final): final},
        "comparacion": {
            "area_valida_comun_ha": round(area_comun, 4),
            "bosque_estable_ha": round(estable, 4),
            "perdida_bosque_ha": round(perdida, 4),
            "ganancia_bosque_ha": round(ganancia, 4),
            "no_bosque_estable_ha": round(no_bosque_estable, 4),
            "bosque_inicial_comparable_ha": round(bosque_inicial_comparable, 4),
            "bosque_final_comparable_ha": round(bosque_final_comparable, 4),
            "no_bosque_inicial_comparable_ha": round(no_bosque_inicial_comparable, 4),
            "no_bosque_final_comparable_ha": round(no_bosque_final_comparable, 4),
            "porcentaje_bosque_inicial_comparable": bosque_inicial_pct,
            "porcentaje_bosque_final_comparable": bosque_final_pct,
            "porcentaje_perdida_bosque_inicial": _porcentaje(
                perdida, bosque_inicial_comparable
            ),
            "porcentaje_ganancia_no_bosque_inicial": _porcentaje(
                ganancia, no_bosque_inicial_comparable
            ),
            "porcentaje_bosque_estable_bosque_inicial": _porcentaje(
                estable, bosque_inicial_comparable
            ),
            "cambio_neto_bosque_ha": round(cambio_neto, 4),
            "cambio_neto_puntos_porcentuales": cambio_pp,
            "variacion_relativa_bosque_pct": _porcentaje(
                cambio_neto, bosque_inicial_comparable
            ),
            "suma_transiciones_ha": round(suma_transiciones, 4),
            "diferencia_cierre_ha": round(diferencia_cierre, 6),
            "transiciones_consistentes": abs(diferencia_cierre) <= tolerancia,
            "tolerancia_ha": round(tolerancia, 6),
            "tolerancia_borde_geometria_ha": round(tolerancia_geometria, 6),
            "denominadores": {
                "porcentajes_anuales": "Área válida de la clasificación en cada año.",
                "cambio_temporal": "Píxeles válidos y comparables en ambos años.",
                "perdida_pct": "Bosque inicial dentro del área válida común.",
                "ganancia_pct": "No bosque inicial dentro del área válida común.",
                "estable_pct": "Bosque inicial dentro del área válida común.",
            },
        },
    }


def _delta(resumen_i: dict[str, Any], resumen_f: dict[str, Any], clave: str) -> float:
    return float(resumen_f.get(clave, 0.0)) - float(resumen_i.get(clave, 0.0))


def generar_interpretacion_ecologica(resultado: dict[str, Any]) -> dict[str, Any]:
    """Genera una lectura reproducible, sin atribuir causalidad ni restauración."""

    estadisticas = resultado["estadisticas_cobertura"]
    anio_i = int(resultado["anio_inicial"])
    anio_f = int(resultado["anio_final"])
    periodo_i = estadisticas["periodos"][str(anio_i)]
    periodo_f = estadisticas["periodos"][str(anio_f)]
    comparacion = estadisticas["comparacion"]
    resumen_i = resultado["periodos"][str(anio_i)]["resumen"]
    resumen_f = resultado["periodos"][str(anio_f)]["resumen"]

    neto = float(comparacion["cambio_neto_bosque_ha"])
    direccion = "aumento neto" if neto > 0 else "disminución neta" if neto < 0 else "sin cambio neto"
    cobertura = (
        f"La cobertura forestal representa {periodo_i['porcentaje_bosque'] or 0:.1f}% "
        f"del área válida en {anio_i} y {periodo_f['porcentaje_bosque'] or 0:.1f}% en {anio_f}. "
        f"En la máscara común se detectaron {comparacion['perdida_bosque_ha']:,.1f} ha "
        f"de pérdida y {comparacion['ganancia_bosque_ha']:,.1f} ha clasificadas nuevamente "
        f"como bosque: {direccion} de {neto:+,.1f} ha. La ganancia es un cambio de clase "
        "satelital y no demuestra por sí sola restauración ecológica."
    )

    senales_fragmentacion = {
        "más parches": _delta(resumen_i, resumen_f, "numero_parches") > 0,
        "menor tamaño medio": _delta(resumen_i, resumen_f, "area_media_parche_ha") < 0,
        "mayor densidad de parches": _delta(resumen_i, resumen_f, "densidad_parches_por_100ha") > 0,
        "menor parche principal": _delta(resumen_i, resumen_f, "indice_parche_mayor_pct") < 0,
        "mayor densidad de borde": _delta(resumen_i, resumen_f, "densidad_borde_m_ha") > 0,
        "más aislamiento": _delta(resumen_i, resumen_f, "porcentaje_parches_aislados") > 0,
    }
    cantidad_fragmentacion = sum(senales_fragmentacion.values())
    if cantidad_fragmentacion >= 4:
        lectura_fragmentacion = "varias métricas son compatibles con una estructura más fragmentada"
    elif cantidad_fragmentacion <= 2:
        lectura_fragmentacion = "no existe una señal conjunta suficiente para afirmar mayor fragmentación"
    else:
        lectura_fragmentacion = "las métricas de fragmentación presentan una señal mixta"
    fragmentacion = (
        f"El número de parches cambió de {resumen_i['numero_parches']:,} a "
        f"{resumen_f['numero_parches']:,} y su tamaño medio de "
        f"{resumen_i['area_media_parche_ha']:,.2f} a {resumen_f['area_media_parche_ha']:,.2f} ha; "
        f"{lectura_fragmentacion}. El conteo de parches no se interpreta de forma aislada."
    )

    aristas_delta = _delta(resumen_i, resumen_f, "numero_aristas")
    componentes_delta = _delta(resumen_i, resumen_f, "numero_componentes")
    aislados_delta = _delta(resumen_i, resumen_f, "porcentaje_parches_aislados")
    principal_delta = _delta(
        resumen_i, resumen_f, "porcentaje_nodos_componente_mayor"
    )
    favorables = sum(
        (aristas_delta > 0, componentes_delta < 0, aislados_delta < 0, principal_delta > 0)
    )
    desfavorables = sum(
        (aristas_delta < 0, componentes_delta > 0, aislados_delta > 0, principal_delta < 0)
    )
    if favorables >= 3 and desfavorables == 0:
        lectura_red = "la red presenta una tendencia estructural más integrada"
    elif desfavorables >= 3 and favorables == 0:
        lectura_red = "la red presenta una tendencia estructural menos integrada"
    else:
        lectura_red = "los indicadores de red son mixtos y deben leerse conjuntamente"
    conectividad = (
        f"Las conexiones cambiaron de {resumen_i['numero_aristas']:,} a "
        f"{resumen_f['numero_aristas']:,}, los componentes de "
        f"{resumen_i['numero_componentes']:,} a {resumen_f['numero_componentes']:,} y "
        f"los parches aislados de {resumen_i['porcentaje_parches_aislados']:.1f}% a "
        f"{resumen_f['porcentaje_parches_aislados']:.1f}%; {lectura_red}. "
        "La conectividad es estructural bajo el umbral configurado y no prueba movimiento de fauna."
    )

    contradicciones = []
    if neto > 0 and cantidad_fragmentacion >= 4:
        contradicciones.append(
            "Aumentó el bosque neto, pero varias métricas sugieren mayor fragmentación."
        )
    if neto < 0 and favorables >= 3:
        contradicciones.append(
            "Disminuyó el bosque neto, mientras la red remanente muestra mayor integración estructural."
        )
    if favorables and desfavorables:
        contradicciones.append(
            "Las métricas de conectividad no cambian todas en la misma dirección."
        )

    fuente = resultado["fuente"]
    return {
        "cobertura": cobertura,
        "fragmentacion": fragmentacion,
        "conectividad": conectividad,
        "contradicciones": contradicciones,
        "limitaciones": [
            fuente["limitacion"],
            f"Resolución nominal: {fuente['resolucion_m']} m; los bordes y parches pequeños están condicionados por esa escala.",
            "Los cambios indican diferencias de clasificación entre fechas; no identifican automáticamente sus causas.",
        ],
        "reglas": {
            "fragmentacion": "Se exige coincidencia de al menos cuatro de seis señales para describir mayor fragmentación.",
            "conectividad": "Se exige coincidencia de al menos tres de cuatro señales y ausencia de señales opuestas para asignar una tendencia.",
        },
    }
