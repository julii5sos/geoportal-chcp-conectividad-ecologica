"""Reglas auditables del índice operativo de prioridad territorial.

Este módulo no depende de Streamlit ni de Earth Engine. Mantiene en un único
lugar los umbrales, los pesos y la clasificación de prioridad usados por las
dos interfaces de la aplicación.
"""

PERIODOS_ANALISIS = {
    "referencia": 2025,
    "jrc_diagnostico": 2025,
    "hansen_diagnostico": 2025,
    "esri_inicial": 2017,
    "esri_final": 2024,
    "esri_final_visual": 2025,
    "ndvi_inicial": 2020,
    "ndvi_final": 2025,
    "ndvi_final_visual": 2025,
}

PESOS_INDICE = {
    "tmf": 2.0,
    "hansen": 2.0,
    "esri": 1.5,
    "gedi": 0.5,
    "ndvi": 0.5,
}

PUNTAJE_MAXIMO = sum(PESOS_INDICE.values())

REGLAS_MAPA_COINCIDENCIA = {
    "nombre": "Sectores que requieren revisión",
    "malla_referencia_m": 30,
    "fuentes": {
        "jrc": "degradación o deforestación JRC TMF 2025",
        "hansen": "pérdida Hansen posterior al 31/12/2020",
        "esri": "transición de árboles a no árboles ESRI 2017-2024",
    },
    "clases": {
        1: {
            "color": "#F9A825",
            "etiqueta": "Señal de 1 fuente",
            "interpretacion": (
                "Evidencia espacial aislada. Revise el producto correspondiente "
                "antes de atribuir una causa."
            ),
        },
        2: {
            "color": "#E65100",
            "etiqueta": "Coincidencia de 2 fuentes",
            "interpretacion": (
                "Dos fuentes señalan el mismo sector en la malla común. Priorice "
                "su contraste con imágenes recientes y documentos."
            ),
        },
        3: {
            "color": "#8E1B16",
            "etiqueta": "Coincidencia de 3 fuentes",
            "interpretacion": (
                "JRC, Hansen y ESRI señalan el mismo sector. Es la clase de mayor "
                "prioridad cartográfica, sin que ello demuestre causalidad."
            ),
        },
    },
    "participa_indice": False,
    "limitacion": (
        "La superposición espacial es un apoyo cartográfico indicativo. Orienta "
        "dónde revisar, pero no demuestra la causa del cambio, no sustituye la "
        "verificación documental o de campo y no determina cumplimiento EUDR."
    ),
}

UMBRALES_INDICE = {
    "hansen_post_2020_ha": 0.18,
    "jrc_deforestacion_ha": 0.5,
    "jrc_deforestacion_pct": 1.0,
    "jrc_degradacion_ha": 2.0,
    "jrc_degradacion_pct": 5.0,
    "esri_salida_arboles_ha": 0.10,
    "esri_salida_arboles_pct": 5.0,
    "gedi_dosel_bajo_m": 8.0,
    "gedi_cobertura_minima_pct": 20.0,
    "gedi_linea_base_minima_pct": 10.0,
    "ndvi_delta_disminucion": -0.15,
    "ndvi_vigor_inicial_minimo": 0.4,
    "ndvi_disminucion_ha": 0.12,
    "ndvi_disminucion_pct": 5.0,
    "ndvi_cobertura_minima_pct": 70.0,
}

JUSTIFICACION_UMBRALES = {
    "hansen_post_2020_ha": (
        "0.18 ha equivale aproximadamente a dos píxeles de 30 m. Se evita que "
        "un único píxel aislado active la señal y se conserva sensibilidad a "
        "eventos pequeños posteriores al 31/12/2020."
    ),
    "jrc_deforestacion": (
        "La señal se activa con 0.5 ha o 1% del área. El criterio absoluto "
        "filtra parches mínimos y el relativo conserva sensibilidad en predios "
        "pequeños; cualquiera de los dos puede justificar revisión."
    ),
    "jrc_degradacion": (
        "La señal se activa con 2 ha o 5% del área. Se usa un criterio más "
        "conservador que para deforestación porque la degradación es gradual y "
        "puede presentar mayor ambigüedad espectral."
    ),
    "esri_salida_arboles": (
        "Se exigen simultáneamente 0.10 ha y 5% del área. A 10 m, 0.10 ha "
        "representa diez píxeles; combinar extensión mínima y proporción reduce "
        "transiciones aisladas por error de clasificación. ESRI corrobora, no "
        "domina, las fuentes forestales."
    ),
    "gedi_dosel_y_cobertura": (
        "GEDI solo aporta contexto cuando al menos 20% del área tiene datos "
        "válidos, la altura media es menor de 8 m y la línea base arbórea cubre "
        "al menos 10%. Así se evita interpretar dosel bajo en áreas sin "
        "cobertura arbórea previa o con muestreo insuficiente."
    ),
    "ndvi": (
        "La señal exige una disminución de al menos 0.15 entre los compuestos "
        "anuales 2020 y 2025, partiendo de NDVI mayor o igual a 0.4. Debe ocupar "
        "al menos 0.12 ha —tres celdas del resumen a 20 m— y 5% del área, con "
        "datos válidos en 70% o más. Esta regla "
        "reduce alertas por píxeles aislados, pero no elimina efectos de humedad, "
        "estacionalidad, cultivos, pastizales, nubes o sombras."
    ),
}

JUSTIFICACION_PESOS = {
    "tmf": (
        "Peso 2.0: producto forestal anual que distingue directamente "
        "degradación y deforestación en bosque tropical húmedo."
    ),
    "hansen": (
        "Peso 2.0: producto específico de pérdida anual de cobertura arbórea; "
        "aporta una señal independiente posterior al corte de referencia."
    ),
    "esri": (
        "Peso 1.5: producto general de uso y cobertura del suelo. La transición "
        "árbol a no árbol es corroborativa y recibe menos peso que los productos "
        "forestales especializados."
    ),
    "gedi": (
        "Peso 0.5: contexto estructural de altura del dosel con cobertura "
        "espacial limitada; no se interpreta como detección directa de pérdida."
    ),
    "ndvi": (
        "Peso 0.5: señal corroborativa de disminución del vigor vegetal. Recibe "
        "menos peso que ESRI y que los productos forestales porque NDVI no "
        "identifica por sí solo bosque natural ni la causa del cambio."
    ),
}

CLASES_VIGOR_NDVI = (
    {
        "color": "#B30000",
        "etiqueta": "Sin vegetación activa",
        "rango": "NDVI < 0",
        "interpretacion": (
            "No se observa una señal positiva de vegetación fotosintéticamente activa. "
            "Puede corresponder a agua, sombra, nubes residuales o superficies no vegetadas."
        ),
    },
    {
        "color": "#F4A582",
        "etiqueta": "Suelo o cobertura muy escasa",
        "rango": "0.0 ≤ NDVI < 0.2",
        "interpretacion": (
            "Respuesta espectral baja, común en suelo desnudo, áreas construidas o "
            "cobertura vegetal muy dispersa."
        ),
    },
    {
        "color": "#FFFFBF",
        "etiqueta": "Vegetación escasa",
        "rango": "0.2 ≤ NDVI < 0.4",
        "interpretacion": (
            "Cobertura vegetal poco densa o con vigor limitado. Puede incluir pastizales, "
            "cultivos en etapas tempranas o vegetación estacional."
        ),
    },
    {
        "color": "#78C679",
        "etiqueta": "Vegetación moderada",
        "rango": "0.4 ≤ NDVI < 0.6",
        "interpretacion": (
            "Señal intermedia de actividad vegetal y cobertura. Debe compararse con la "
            "época del año, el uso del suelo y las demás fuentes."
        ),
    },
    {
        "color": "#006837",
        "etiqueta": "Vegetación densa",
        "rango": "NDVI ≥ 0.6",
        "interpretacion": (
            "Señal alta de vegetación verde y densa. No demuestra por sí sola que la "
            "cobertura sea bosque natural ni determina su condición legal."
        ),
    },
)

REGLAS_PRIORIDAD = {
    "alta": "puntaje >= 3.0",
    "media": "puntaje >= 1.5 y < 3.0",
    "preventiva": "puntaje >= 0.5 y < 1.5",
    "baja": "puntaje < 0.5",
}

REGLAS_CONSISTENCIA = {
    "alta": "JRC TMF, Hansen y ESRI presentan señal de deterioro",
    "parcial": "exactamente dos de JRC TMF, Hansen y ESRI presentan señal",
    "mixta": "coexisten señales de deterioro y de regeneración forestal/ganancia",
    "sin_senal": "menos de dos fuentes principales coinciden en deterioro",
}

# La prioridad de visita es una capa de decisión separada del índice satelital.
# El cambio observado mantiene el mayor peso (hasta 6.5 puntos), el corredor
# aumenta el valor estratégico (hasta 1.5 puntos) y la condición estructural
# orienta espacialmente la visita sin recibir un peso no calibrado.
REGLAS_PRIORIDAD_VISITA = {
    "nombre": "Prioridad integrada de visita",
    "puntaje_maximo_cambios": PUNTAJE_MAXIMO,
    "aporte_maximo_corredor": 1.5,
    "porcentaje_saturacion_corredor": 25.0,
    "aporte_maximo_solapamiento": 1.0,
    "aporte_corredor_mesoamericano": 0.5,
    "principios": {
        "dominancia_cambios": (
            "Las señales satelitales determinan la urgencia; el corredor solo "
            "aumenta la relevancia estratégica de organizar una visita."
        ),
        "sin_urgencia_por_corredor_solo": (
            "Un corredor sin señales de cambio puede justificar seguimiento "
            "preventivo, pero nunca una prioridad alta o muy alta de visita."
        ),
        "categorias_externas": (
            "Las categorías alta, mediana y media-baja de Almanaque Azul se "
            "conservan como atributos y no se convierten en evidencia de deterioro."
        ),
        "estructura_sin_peso_inventado": (
            "La fragmentación y la conectividad del bosque de 2021 orientan "
            "dónde focalizar la visita, pero no suman puntos hasta contar con "
            "umbrales ecológicos calibrados para el territorio y las especies objetivo."
        ),
    },
    "clases": {
        "Muy alta": (
            "Cambios con prioridad alta y aporte estratégico del corredor de al "
            "menos 1 punto."
        ),
        "Alta": "Puntaje integrado de al menos 3 puntos.",
        "Media": "Puntaje integrado de al menos 1.5 puntos.",
        "Preventiva": (
            "Puntaje integrado de al menos 0.5 puntos o valor de corredor sin "
            "señales suficientes de cambio."
        ),
        "Baja": "Puntaje integrado menor de 0.5 puntos.",
    },
}

REGLAS_CONTEXTO_ESTRUCTURAL = {
    "fuente": "SINIA–MiAMBIENTE · Bosque y otros usos · 2021",
    "participa_puntaje": False,
    "criterios": {
        "conectada": "un solo componente al umbral seleccionado",
        "predominante": "más de un componente y al menos 75% de los parches en el mayor",
        "intermedia": "entre 50% y menos de 75% de los parches en el mayor componente",
        "dividida": "menos de 50% de los parches en el mayor componente",
    },
    "limitacion": (
        "Es una lectura estructural dependiente del umbral entre parches y de la "
        "cobertura clasificada en 2021. No demuestra conectividad funcional ni "
        "movimiento de una especie."
    ),
}

PUNTAJE_MAXIMO_VISITA = (
    PUNTAJE_MAXIMO + REGLAS_PRIORIDAD_VISITA["aporte_maximo_corredor"]
)


def clasificar_prioridad(puntaje):
    """Clasifica un puntaje ya calculado sin alterar su valor."""
    if puntaje >= 3.0:
        return "Alta"
    if puntaje >= 1.5:
        return "Media"
    if puntaje >= 0.5:
        return "Preventiva"
    return "Baja"


def evaluar_contexto_estructural(contexto_fragmentacion):
    """Resume la red de parches sin convertirla en un puntaje no calibrado."""

    contexto = contexto_fragmentacion or {}
    metricas_clase = contexto.get("metricas_clase") or {}
    metricas_red = contexto.get("metricas_red") or {}
    if not metricas_clase or not metricas_red:
        return {
            "disponible": False,
            "estado": "No evaluada",
            "requiere_focalizacion": False,
            "numero_parches": 0,
            "numero_componentes": 0,
            "porcentaje_componente_mayor": 0.0,
            "porcentaje_bosque": 0.0,
            "umbral_m": None,
            "conexion_potencial_corredor": False,
            "corredor_referencia": None,
            "categoria_corredor": None,
            "interpretacion": (
                "La administración debe configurar el asset de Bosque y otros usos "
                "2021 para incorporar fragmentación y conectividad al diagnóstico."
            ),
            "participa_puntaje": False,
            "limitacion": REGLAS_CONTEXTO_ESTRUCTURAL["limitacion"],
        }

    numero_parches = max(0, int(metricas_clase.get("numero_parches") or 0))
    numero_componentes = max(0, int(metricas_red.get("numero_componentes") or 0))
    porcentaje_mayor = max(
        0.0,
        min(
            100.0,
            float(metricas_red.get("porcentaje_nodos_componente_mayor") or 0.0),
        ),
    )
    porcentaje_bosque = max(
        0.0,
        min(
            100.0,
            float(metricas_clase.get("porcentaje_paisaje_bosque") or 0.0),
        ),
    )
    conexion_corredor = contexto.get("conexion_corredor") or {}
    conexion_potencial_corredor = bool(conexion_corredor.get("conecta"))

    if numero_parches == 0:
        estado = "Sin bosque identificado"
        requiere_focalizacion = True
        interpretacion = (
            "La cobertura institucional de 2021 no identifica parches de bosque "
            "dentro del área evaluada. Conviene verificar el recorte y el estado en campo."
        )
    elif numero_parches == 1:
        estado = "Un solo parche"
        requiere_focalizacion = False
        interpretacion = (
            "La cobertura seleccionada forma un único parche dentro del área evaluada."
        )
    elif numero_componentes <= 1:
        estado = "Conectada al umbral"
        requiere_focalizacion = False
        interpretacion = (
            "Todos los parches pertenecen a una sola red con la distancia seleccionada."
        )
    elif porcentaje_mayor >= 75.0:
        estado = "Conectividad predominante"
        requiere_focalizacion = True
        interpretacion = (
            "La mayoría de los parches pertenece a una red principal, aunque existen "
            "componentes aislados que conviene revisar."
        )
    elif porcentaje_mayor >= 50.0:
        estado = "Conectividad intermedia"
        requiere_focalizacion = True
        interpretacion = (
            "La red principal reúne entre la mitad y tres cuartas partes de los "
            "parches; los conectores y separaciones requieren atención espacial."
        )
    else:
        estado = "Red dividida"
        requiere_focalizacion = True
        interpretacion = (
            "Menos de la mitad de los parches pertenece al componente principal; "
            "la red está distribuida en varios grupos al umbral seleccionado."
        )

    return {
        "disponible": True,
        "estado": estado,
        "requiere_focalizacion": requiere_focalizacion,
        "numero_parches": numero_parches,
        "numero_componentes": numero_componentes,
        "porcentaje_componente_mayor": round(porcentaje_mayor, 4),
        "porcentaje_bosque": round(porcentaje_bosque, 4),
        "umbral_m": float(metricas_red.get("umbral_m") or 0.0),
        "conexion_potencial_corredor": conexion_potencial_corredor,
        "corredor_referencia": conexion_corredor.get("corredor_nombre"),
        "categoria_corredor": conexion_corredor.get("categoria_etiqueta"),
        "distancia_ruta_corredor_m": conexion_corredor.get(
            "distancia_acumulada_m"
        ),
        "interpretacion": interpretacion,
        "participa_puntaje": False,
        "limitacion": REGLAS_CONTEXTO_ESTRUCTURAL["limitacion"],
    }


def calcular_prioridad_visita(
    *, puntaje_cambios, contexto_corredores, contexto_fragmentacion=None
):
    """Integra urgencia, corredor y condición estructural en una decisión.

    La fórmula no altera el índice satelital. El solapamiento aporta de forma
    proporcional hasta alcanzar un punto cuando 25 % del AOI está dentro de
    corredores. La pertenencia al Corredor Biológico Mesoamericano añade 0.5.
    Sin señales satelitales, el resultado queda limitado a Preventiva. La red
    de parches orienta el foco espacial sin sumar un peso no calibrado.
    """

    contexto = contexto_corredores or {}
    porcentaje = max(
        0.0,
        min(100.0, float(contexto.get("porcentaje_aoi_en_corredores") or 0.0)),
    )
    intersecta = bool(contexto.get("intersecta")) and porcentaje > 0
    intersecta_mesoamericano = intersecta and bool(
        contexto.get("intersecta_mesoamericano")
    )
    saturacion = REGLAS_PRIORIDAD_VISITA["porcentaje_saturacion_corredor"]
    aporte_solapamiento = (
        min(
            porcentaje / saturacion,
            REGLAS_PRIORIDAD_VISITA["aporte_maximo_solapamiento"],
        )
        if intersecta
        else 0.0
    )
    aporte_mesoamericano = (
        REGLAS_PRIORIDAD_VISITA["aporte_corredor_mesoamericano"]
        if intersecta_mesoamericano
        else 0.0
    )
    aporte_corredor = round(
        min(
            aporte_solapamiento + aporte_mesoamericano,
            REGLAS_PRIORIDAD_VISITA["aporte_maximo_corredor"],
        ),
        2,
    )
    puntaje_cambios = round(max(0.0, min(PUNTAJE_MAXIMO, float(puntaje_cambios))), 1)
    puntaje_integrado = round(puntaje_cambios + aporte_corredor, 2)

    if not intersecta:
        valor_corredor = "Sin intersección"
    elif aporte_corredor >= 1.0:
        valor_corredor = "Alto"
    elif aporte_corredor >= 0.5:
        valor_corredor = "Medio"
    else:
        valor_corredor = "Contextual"

    # El corredor por sí solo no se interpreta como evidencia que obligue a
    # una visita. Solo puede elevar el resultado hasta Preventiva.
    if puntaje_cambios < 0.5:
        prioridad_visita = "Preventiva" if aporte_corredor >= 0.5 else "Baja"
    elif puntaje_cambios >= 3.0 and aporte_corredor >= 1.0:
        prioridad_visita = "Muy alta"
    elif puntaje_integrado >= 3.0:
        prioridad_visita = "Alta"
    elif puntaje_integrado >= 1.5:
        prioridad_visita = "Media"
    elif puntaje_integrado >= 0.5:
        prioridad_visita = "Preventiva"
    else:
        prioridad_visita = "Baja"

    estructura = evaluar_contexto_estructural(contexto_fragmentacion)
    hay_cambio = puntaje_cambios >= 0.5
    red_requiere_focalizacion = bool(
        estructura["disponible"] and estructura["requiere_focalizacion"]
    )
    conexion_potencial_corredor = bool(
        estructura.get("conexion_potencial_corredor")
    )

    if hay_cambio and intersecta and red_requiere_focalizacion:
        combinacion_territorial = "Cambios + corredor + estructura"
        foco_visita = (
            "Ubique primero los sectores con señales recientes dentro del corredor; "
            "entre ellos, priorice parches conectores y separaciones entre componentes."
        )
    elif hay_cambio and intersecta:
        combinacion_territorial = "Cambios + corredor"
        foco_visita = (
            "Ubique primero las señales recientes que se encuentran dentro del corredor."
        )
    elif hay_cambio and red_requiere_focalizacion:
        if conexion_potencial_corredor:
            combinacion_territorial = "Cambios + conexión potencial + estructura"
            foco_visita = (
                "Contraste las señales recientes con la cadena estructural potencial "
                f"hacia {estructura.get('corredor_referencia') or 'el corredor de referencia'}; "
                "revise especialmente sus separaciones sin asumir tránsito de fauna."
            )
        else:
            combinacion_territorial = "Cambios + estructura"
            foco_visita = (
                "Contraste las señales recientes con los parches conectores y los "
                "componentes aislados de la red."
            )
    elif hay_cambio and conexion_potencial_corredor:
        combinacion_territorial = "Cambios + conexión potencial"
        foco_visita = (
            "Revise si las señales recientes afectan la cadena estructural potencial "
            f"hacia {estructura.get('corredor_referencia') or 'el corredor de referencia'}."
        )
    elif hay_cambio:
        combinacion_territorial = "Cambios recientes"
        foco_visita = (
            "Revise los sectores señalados por dos o tres fuentes y contraste su causa."
        )
    elif intersecta and red_requiere_focalizacion:
        combinacion_territorial = "Corredor + estructura preventiva"
        foco_visita = (
            "Sin urgencia satelital, documente preventivamente los conectores y "
            "separaciones de la red que se encuentran dentro del corredor."
        )
    elif intersecta:
        combinacion_territorial = "Corredor preventivo"
        foco_visita = (
            "Mantenga seguimiento preventivo del área incluida en el corredor."
        )
    elif red_requiere_focalizacion:
        if conexion_potencial_corredor:
            combinacion_territorial = "Conexión potencial preventiva"
            foco_visita = (
                "Revise preventivamente la cadena estructural potencial hacia "
                f"{estructura.get('corredor_referencia') or 'el corredor de referencia'}, "
                "sin interpretarla como conectividad funcional confirmada."
            )
        else:
            combinacion_territorial = "Estructura preventiva"
            foco_visita = (
                "Mantenga seguimiento de los conectores y componentes aislados sin "
                "interpretarlos como cambio reciente."
            )
    elif conexion_potencial_corredor:
        combinacion_territorial = "Conexión potencial preventiva"
        foco_visita = (
            "Mantenga seguimiento preventivo de la cadena estructural potencial hacia "
            f"{estructura.get('corredor_referencia') or 'el corredor de referencia'}."
        )
    else:
        combinacion_territorial = "Monitoreo ordinario"
        foco_visita = (
            "No se identificó una combinación que aumente la focalización de la visita."
        )

    lectura_integrada = (
        f"Urgencia por cambios: {clasificar_prioridad(puntaje_cambios)}; "
        f"valor del corredor: {valor_corredor}; condición estructural: "
        f"{estructura['estado']}."
    )
    if conexion_potencial_corredor and not intersecta:
        lectura_integrada += (
            " Aunque el área no intersecta un corredor publicado, la cobertura 2021 "
            "muestra una conexión estructural potencial hacia "
            f"{estructura.get('corredor_referencia') or 'un corredor de referencia'}."
        )

    return {
        "puntaje_cambios": puntaje_cambios,
        "prioridad_cambios": clasificar_prioridad(puntaje_cambios),
        "porcentaje_aoi_en_corredores": round(porcentaje, 4),
        "intersecta_corredor": intersecta,
        "intersecta_mesoamericano": intersecta_mesoamericano,
        "aporte_solapamiento": round(aporte_solapamiento, 2),
        "aporte_mesoamericano": round(aporte_mesoamericano, 2),
        "aporte_corredor": aporte_corredor,
        "valor_corredor": valor_corredor,
        "puntaje_integrado": puntaje_integrado,
        "puntaje_maximo": PUNTAJE_MAXIMO_VISITA,
        "prioridad_visita": prioridad_visita,
        "contexto_estructural": estructura,
        "combinacion_territorial": combinacion_territorial,
        "foco_visita": foco_visita,
        "lectura_integrada": lectura_integrada,
        "diagnostico_completo": estructura["disponible"],
        "limitacion": (
            "La prioridad de visita orienta la planificación operativa. No "
            "demuestra la causa del cambio, daño ambiental ni conectividad "
            "funcional para una especie."
        ),
    }


def texto_recomendacion_visita(prioridad):
    """Devuelve una acción operativa para cada clase de prioridad de visita."""

    return {
        "Muy alta": (
            "Programar una visita prioritaria a los sectores con cambios "
            "coincidentes que también aportan al corredor."
        ),
        "Alta": (
            "Programar la revisión detallada y preparar una visita de campo a "
            "los sectores señalados."
        ),
        "Media": (
            "Revisar imágenes recientes y documentación; realizar una visita si "
            "las señales se confirman o afectan la continuidad del corredor."
        ),
        "Preventiva": (
            "Mantener seguimiento periódico y documentar el estado del corredor; "
            "no se requiere una visita urgente con la evidencia disponible."
        ),
        "Baja": (
            "Continuar el monitoreo ordinario; no hay evidencia suficiente para "
            "priorizar una visita."
        ),
    }[prioridad]


def evaluar_senales(
    *,
    tmf_deforestacion_ha,
    tmf_deforestacion_pct,
    tmf_degradacion_ha,
    tmf_degradacion_pct,
    hansen_post_2020_ha,
    esri_salida_arboles_ha,
    esri_salida_arboles_pct,
    gedi_altura_media_m,
    gedi_cobertura_valida_pct,
    linea_base_arborea_pct,
    ndvi_disminucion_ha,
    ndvi_disminucion_pct,
    ndvi_cobertura_valida_pct,
):
    """Aplica los umbrales metodológicos sin asignar pesos todavía."""
    senal_tmf = (
        tmf_deforestacion_ha >= UMBRALES_INDICE["jrc_deforestacion_ha"]
        or tmf_deforestacion_pct >= UMBRALES_INDICE["jrc_deforestacion_pct"]
        or tmf_degradacion_ha >= UMBRALES_INDICE["jrc_degradacion_ha"]
        or tmf_degradacion_pct >= UMBRALES_INDICE["jrc_degradacion_pct"]
    )
    senal_hansen = (
        hansen_post_2020_ha >= UMBRALES_INDICE["hansen_post_2020_ha"]
    )
    # ESRI exige extensión y proporción simultáneamente. Esta conjunción evita
    # que el producto general de cobertura domine el índice por cambios aislados.
    senal_esri = (
        esri_salida_arboles_ha >= UMBRALES_INDICE["esri_salida_arboles_ha"]
        and esri_salida_arboles_pct >= UMBRALES_INDICE["esri_salida_arboles_pct"]
    )
    gedi_disponible = (
        gedi_cobertura_valida_pct
        >= UMBRALES_INDICE["gedi_cobertura_minima_pct"]
    )
    senal_gedi = (
        gedi_disponible
        and gedi_altura_media_m < UMBRALES_INDICE["gedi_dosel_bajo_m"]
        and linea_base_arborea_pct
        >= UMBRALES_INDICE["gedi_linea_base_minima_pct"]
    )
    ndvi_disponible = (
        ndvi_cobertura_valida_pct
        >= UMBRALES_INDICE["ndvi_cobertura_minima_pct"]
    )
    senal_ndvi = (
        ndvi_disponible
        and ndvi_disminucion_ha >= UMBRALES_INDICE["ndvi_disminucion_ha"]
        and ndvi_disminucion_pct >= UMBRALES_INDICE["ndvi_disminucion_pct"]
    )
    return {
        "tmf": bool(senal_tmf),
        "hansen": bool(senal_hansen),
        "esri": bool(senal_esri),
        "gedi": bool(senal_gedi),
        "ndvi": bool(senal_ndvi),
    }, {
        "gedi": bool(gedi_disponible),
        "ndvi": bool(ndvi_disponible),
    }


def calcular_indice_prioridad(
    *,
    senal_tmf,
    senal_hansen,
    senal_esri,
    senal_gedi,
    senal_ndvi=False,
):
    """Suma una sola vez el peso de cada fuente cuya señal está activa."""
    senales = {
        "tmf": bool(senal_tmf),
        "hansen": bool(senal_hansen),
        "esri": bool(senal_esri),
        "gedi": bool(senal_gedi),
        "ndvi": bool(senal_ndvi),
    }
    aportes = {
        fuente: PESOS_INDICE[fuente] if activa else 0.0
        for fuente, activa in senales.items()
    }
    puntaje = round(sum(aportes.values()), 1)
    return aportes, puntaje, clasificar_prioridad(puntaje)


def evaluar_consistencia(
    *,
    senal_tmf,
    senal_hansen,
    senal_esri,
    tmf_recuperacion_ha,
    tmf_recuperacion_pct,
    esri_ganancia_arboles_ha,
    esri_ganancia_arboles_pct,
):
    """Describe coincidencias entre fuentes sin modificar el índice.

    La consistencia es una lectura complementaria. Las ganancias se filtran con
    umbrales simétricos a los usados para deforestación JRC y transición ESRI,
    de modo que un píxel o una fracción mínima no produzcan una lectura mixta.
    """
    deterioro = [
        nombre
        for nombre, activa in (
            ("JRC TMF", bool(senal_tmf)),
            ("Hansen GFC", bool(senal_hansen)),
            ("ESRI LULC", bool(senal_esri)),
        )
        if activa
    ]
    recuperacion_tmf = (
        tmf_recuperacion_ha >= UMBRALES_INDICE["jrc_deforestacion_ha"]
        or tmf_recuperacion_pct >= UMBRALES_INDICE["jrc_deforestacion_pct"]
    )
    ganancia_esri = (
        esri_ganancia_arboles_ha
        >= UMBRALES_INDICE["esri_salida_arboles_ha"]
        and esri_ganancia_arboles_pct
        >= UMBRALES_INDICE["esri_salida_arboles_pct"]
    )
    recuperacion = [
        nombre
        for nombre, activa in (
            ("JRC TMF (regeneración forestal)", recuperacion_tmf),
            ("ESRI LULC (ganancia de árboles)", ganancia_esri),
        )
        if activa
    ]

    if deterioro and recuperacion:
        nivel = "Lectura mixta"
        detalle = (
            "El área contiene señales de deterioro y de regeneración forestal o ganancia "
            "arbórea. Revise su distribución espacial; no deben compensarse "
            "numéricamente ni interpretarse como ausencia de cambio."
        )
    elif len(deterioro) == 3:
        nivel = "Alta consistencia"
        detalle = (
            "JRC TMF, Hansen GFC y ESRI LULC presentan señales de deterioro. "
            "Las fuentes se refuerzan, aunque no se exige coincidencia píxel a píxel."
        )
    elif len(deterioro) == 2:
        nivel = "Consistencia parcial"
        detalle = (
            "Dos fuentes principales presentan señales de deterioro. La tercera "
            "puede responder a otra definición, resolución o período."
        )
    else:
        nivel = "Sin señal consistente"
        detalle = (
            "Menos de dos fuentes principales coinciden en deterioro. Mantenga "
            "el monitoreo y revise individualmente cualquier señal aislada."
        )

    return {
        "nivel": nivel,
        "detalle": detalle,
        "fuentes_deterioro": deterioro,
        "fuentes_recuperacion": recuperacion,
    }
