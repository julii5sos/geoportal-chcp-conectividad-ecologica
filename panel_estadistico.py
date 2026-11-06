"""Panel derecho de resultados temporales del Geoportal CHCP 2.0."""

from __future__ import annotations

from typing import Any

import altair as alt
import streamlit as st


AZUL = "#0A4393"
AZUL_CLARO = "#3A7CA5"
VERDE = "#2E7D32"
VERDE_CLARO = "#77CC09"
NO_BOSQUE = "#D7C6A5"
PERDIDA = "#D0442C"
GANANCIA = "#43AA8B"
GRIS = "#9AA5B1"


def _valor(valor: float | None, formato: str = ",.1f", sufijo: str = "") -> str:
    if valor is None:
        return "No aplica"
    return f"{float(valor):{formato}}{sufijo}"


def _delta(valor: float, sufijo: str = "") -> str:
    return f"{float(valor):+,.1f}{sufijo}"


def _tarjeta(etiqueta: str, valor: str, detalle: str = "", clase: str = "") -> str:
    return (
        f'<div class="fase4-mc {clase}"><small>{etiqueta}</small>'
        f"<strong>{valor}</strong><span>{detalle}</span></div>"
    )


def grafica_donas(estadisticas: dict[str, Any], anios: tuple[int, int]):
    graficas = []
    for anio in anios:
        periodo = estadisticas["periodos"][str(anio)]
        datos = [
            {"Cobertura": "Bosque", "ha": periodo["bosque_ha"]},
            {"Cobertura": "No bosque", "ha": periodo["no_bosque_ha"]},
        ]
        base = alt.Chart(alt.Data(values=datos)).encode(
            theta=alt.Theta("ha:Q", stack=True),
            color=alt.Color(
                "Cobertura:N",
                scale=alt.Scale(
                    domain=["Bosque", "No bosque"], range=[VERDE, NO_BOSQUE]
                ),
                legend=None,
            ),
            tooltip=[
                "Cobertura:N",
                alt.Tooltip("ha:Q", title="Superficie (ha)", format=",.1f"),
            ],
        )
        arco = base.mark_arc(innerRadius=37, outerRadius=56, stroke="#ffffff")
        texto = alt.Chart(
            alt.Data(
                values=[
                    {
                        "texto": _valor(periodo["porcentaje_bosque"], ".1f", "%")
                    }
                ]
            )
        ).mark_text(fontSize=16, fontWeight=700, color="#062A5E").encode(text="texto:N")
        graficas.append((arco + texto).properties(width=112, height=112, title=str(anio)))
    return (
        alt.hconcat(*graficas, spacing=12)
        .resolve_scale(color="shared")
        .configure_title(font="DM Sans", color="#062A5E", fontSize=12)
        .configure_view(stroke=None)
    )


def grafica_cobertura(estadisticas: dict[str, Any], anios: tuple[int, int]):
    datos = []
    for anio in anios:
        periodo = estadisticas["periodos"][str(anio)]
        datos.extend(
            [
                {"Año": str(anio), "Cobertura": "Bosque", "ha": periodo["bosque_ha"]},
                {"Año": str(anio), "Cobertura": "No bosque", "ha": periodo["no_bosque_ha"]},
            ]
        )
    return (
        alt.Chart(alt.Data(values=datos))
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Año:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
            xOffset="Cobertura:N",
            y=alt.Y("ha:Q", title="Superficie válida (ha)"),
            color=alt.Color(
                "Cobertura:N",
                scale=alt.Scale(
                    domain=["Bosque", "No bosque"], range=[VERDE, NO_BOSQUE]
                ),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["Año:N", "Cobertura:N", alt.Tooltip("ha:Q", format=",.1f")],
        )
        .properties(height=210)
    )


def grafica_transiciones(comparacion: dict[str, Any]):
    datos = [
        {"Transición": "Bosque estable", "ha": comparacion["bosque_estable_ha"]},
        {"Transición": "Pérdida", "ha": comparacion["perdida_bosque_ha"]},
        {"Transición": "Ganancia", "ha": comparacion["ganancia_bosque_ha"]},
        {
            "Transición": "No bosque estable",
            "ha": comparacion["no_bosque_estable_ha"],
        },
    ]
    orden = ["Bosque estable", "Pérdida", "Ganancia", "No bosque estable"]
    colores = [VERDE, PERDIDA, GANANCIA, GRIS]
    base = alt.Chart(alt.Data(values=datos)).encode(
        y=alt.Y("Transición:N", sort=orden, title=None),
        x=alt.X("ha:Q", title="Superficie común (ha)"),
        color=alt.Color(
            "Transición:N",
            scale=alt.Scale(domain=orden, range=colores),
            legend=None,
        ),
        tooltip=["Transición:N", alt.Tooltip("ha:Q", format=",.1f")],
    )
    barras = base.mark_bar(cornerRadiusEnd=3)
    etiquetas = base.mark_text(align="left", baseline="middle", dx=4, fontSize=10).encode(
        text=alt.Text("ha:Q", format=",.1f"), color=alt.value("#1B2433")
    )
    return (barras + etiquetas).properties(height=185)


def _grafica_metrica(
    valores: list[dict[str, Any]], clave: str, titulo: str, formato: str = ",.1f"
):
    datos = [{"Año": str(fila["Año"]), "Valor": fila[clave]} for fila in valores]
    base = alt.Chart(alt.Data(values=datos)).encode(
        x=alt.X("Año:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Valor:Q", title=titulo),
        color=alt.Color(
            "Año:N", scale=alt.Scale(range=[AZUL_CLARO, VERDE_CLARO]), legend=None
        ),
        tooltip=["Año:N", alt.Tooltip("Valor:Q", title=titulo, format=formato)],
    )
    barras = base.mark_bar(size=46, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    etiquetas = base.mark_text(dy=-7, fontSize=10, color="#062A5E").encode(
        text=alt.Text("Valor:Q", format=formato)
    )
    return (barras + etiquetas).properties(height=145)


def _filas_periodos(resultado: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "Año": anio,
            **resultado["periodos"][str(anio)]["resumen"],
        }
        for anio in (resultado["anio_inicial"], resultado["anio_final"])
    ]


def renderizar_panel_estadistico(
    resultado: dict[str, Any],
    *,
    tipo_analisis: str,
    descarga_zip: bytes,
) -> None:
    """Presenta el panel sin sustituir ni ocultar el mapa central."""

    anio_i = int(resultado["anio_inicial"])
    anio_f = int(resultado["anio_final"])
    anios = (anio_i, anio_f)
    estadisticas = resultado["estadisticas_cobertura"]
    periodo_i = estadisticas["periodos"][str(anio_i)]
    periodo_f = estadisticas["periodos"][str(anio_f)]
    comparacion = estadisticas["comparacion"]
    interpretacion = resultado["interpretacion_ecologica"]
    fuente = resultado["fuente"]
    parametros = resultado["parametros_equivalentes"]
    filas = _filas_periodos(resultado)
    resumen_i = filas[0]
    resumen_f = filas[1]
    neto = float(comparacion["cambio_neto_bosque_ha"])
    clase_neto = "fase4-delta-pos" if neto >= 0 else "fase4-delta-neg"

    with st.container(key="fase4_panel_resultados"):
        st.markdown(
            '<div class="fase4-res-body">'
            f'<div class="fase4-big"><small>Bosque válido {anio_f}</small>'
            f'<strong>{_valor(periodo_f["porcentaje_bosque"], ".1f", "%")}</strong>'
            f'<span>{periodo_f["bosque_ha"]:,.1f} ha · '
            f'<b class="{clase_neto}">{neto:+,.1f} ha netas</b></span></div>'
            '<div class="fase4-cards">'
            + _tarjeta("Pérdida bruta", _valor(comparacion["perdida_bosque_ha"], ",.1f", " ha"))
            + _tarjeta("Ganancia detectada", _valor(comparacion["ganancia_bosque_ha"], ",.1f", " ha"))
            + _tarjeta("Cambio en cobertura", _valor(comparacion["cambio_neto_puntos_porcentuales"], "+.2f", " pp"))
            + _tarjeta("Variación relativa", _valor(comparacion["variacion_relativa_bosque_pct"], "+.1f", "%"))
            + "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="fase4-chart-title">Cobertura válida por período</div>', unsafe_allow_html=True)
        st.altair_chart(grafica_donas(estadisticas, anios), width="stretch", theme=None)
        st.caption("Verde: bosque. Beige: otras coberturas. NoData se excluye de ambos porcentajes.")

        with st.expander("Cobertura y transiciones", expanded=True):
            st.altair_chart(grafica_cobertura(estadisticas, anios), width="stretch", theme=None)
            st.altair_chart(grafica_transiciones(comparacion), width="stretch", theme=None)
            st.markdown(
                f"**Área geométrica:** {periodo_i['area_geometrica_ha']:,.1f} ha  \n"
                f"**Área válida {anio_i}:** {periodo_i['area_valida_ha']:,.1f} ha · "
                f"**NoData:** {periodo_i['sin_datos_ha']:,.1f} ha  \n"
                f"**Área válida {anio_f}:** {periodo_f['area_valida_ha']:,.1f} ha · "
                f"**NoData:** {periodo_f['sin_datos_ha']:,.1f} ha  \n"
                f"**Máscara común comparable:** {comparacion['area_valida_comun_ha']:,.1f} ha"
            )
            st.caption(
                f"Cierre de transiciones: {comparacion['suma_transiciones_ha']:,.2f} ha; "
                f"diferencia {comparacion['diferencia_cierre_ha']:+.4f} ha, dentro de "
                f"±{comparacion['tolerancia_ha']:.2f} ha."
            )

        if tipo_analisis in {"fragmentacion", "integral"}:
            with st.expander("Fragmentación forestal", expanded=tipo_analisis == "fragmentacion"):
                delta_parches = resumen_f["numero_parches"] - resumen_i["numero_parches"]
                st.markdown(
                    '<div class="fase4-cards">'
                    + _tarjeta("Parches", f"{resumen_i['numero_parches']:,} → {resumen_f['numero_parches']:,}", _delta(delta_parches))
                    + _tarjeta("Tamaño medio", f"{resumen_f['area_media_parche_ha']:,.2f} ha", _delta(resumen_f['area_media_parche_ha'] - resumen_i['area_media_parche_ha'], " ha"))
                    + _tarjeta("Densidad", f"{resumen_f['densidad_parches_por_100ha']:,.2f}", "parches / 100 ha")
                    + _tarjeta("Parche mayor", f"{resumen_f['indice_parche_mayor_pct']:,.1f}%", _delta(resumen_f['indice_parche_mayor_pct'] - resumen_i['indice_parche_mayor_pct'], " pp"))
                    + "</div>",
                    unsafe_allow_html=True,
                )
                st.altair_chart(_grafica_metrica(filas, "numero_parches", "Número de parches", ",.0f"), width="stretch", theme=None)
                st.altair_chart(_grafica_metrica(filas, "densidad_borde_m_ha", "Borde (m/ha)"), width="stretch", theme=None)
                st.markdown(interpretacion["fragmentacion"])

        if tipo_analisis in {"conectividad", "integral"}:
            with st.expander("Conectividad estructural", expanded=tipo_analisis == "conectividad"):
                st.markdown(
                    '<div class="fase4-cards">'
                    + _tarjeta("Conexiones", f"{resumen_i['numero_aristas']:,} → {resumen_f['numero_aristas']:,}")
                    + _tarjeta("Componentes", f"{resumen_i['numero_componentes']:,} → {resumen_f['numero_componentes']:,}")
                    + _tarjeta("Parches conectados", f"{resumen_f['porcentaje_parches_conectados']:,.1f}%", _delta(resumen_f['porcentaje_parches_conectados'] - resumen_i['porcentaje_parches_conectados'], " pp"))
                    + _tarjeta("Componente principal", f"{resumen_f['porcentaje_nodos_componente_mayor']:,.1f}%", _delta(resumen_f['porcentaje_nodos_componente_mayor'] - resumen_i['porcentaje_nodos_componente_mayor'], " pp"))
                    + "</div>",
                    unsafe_allow_html=True,
                )
                st.altair_chart(_grafica_metrica(filas, "numero_aristas", "Conexiones", ",.0f"), width="stretch", theme=None)
                st.altair_chart(_grafica_metrica(filas, "porcentaje_parches_aislados", "Parches aislados (%)"), width="stretch", theme=None)
                st.markdown(interpretacion["conectividad"])

        with st.expander("Interpretación ecológica", expanded=True):
            st.markdown(interpretacion["cobertura"])
            for texto in interpretacion["contradicciones"]:
                st.warning(texto)
            for texto in interpretacion["limitaciones"]:
                st.caption(f"• {texto}")

        with st.expander("Fuente, método y valores", expanded=False):
            st.markdown(
                f"**Fuente:** {fuente['nombre']}  \n"
                f"**Versión:** {fuente['version']}  \n"
                f"**Período:** {anio_i}–{anio_f}  \n"
                f"**Resolución nominal:** {fuente['resolucion_m']} m  \n"
                f"**Definición de bosque:** {fuente['definicion_bosque']}  \n"
                f"**Área válida común:** {comparacion['area_valida_comun_ha']:,.1f} ha  \n"
                f"**Área mínima de parche:** {parametros['area_minima_parche_ha']} ha  \n"
                f"**Umbral entre parches:** {parametros['distancia_maxima_m']} m  \n"
                f"**Ejecución UTC:** {resultado['metadatos']['generado_utc']}"
            )
            st.dataframe(filas, hide_index=True, width="stretch")
            st.caption("El ERI conserva su metodología independiente y no se suma al cambio temporal.")

        st.markdown(
            '<div class="fase4-warning">Los resultados representan cambios de clasificación y conectividad estructural potencial. Requieren verificación de campo y no demuestran causalidad ni movimiento de fauna.</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Descargar resultados y metadatos",
            data=descarga_zip,
            file_name=f"analisis_temporal_{resultado['fuente']['clave']}_{anio_i}_{anio_f}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
            key="descarga_panel_estadistico",
        )
