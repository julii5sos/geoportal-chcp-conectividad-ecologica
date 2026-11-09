"""Informe técnico condicional construido exclusivamente desde un resultado en caché."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reporte_cartografico import crear_mapa_conectividad, crear_mapa_fragmentacion


AZUL = colors.HexColor("#0A4393")
VERDE = colors.HexColor("#176B45")
GRIS = colors.HexColor("#45536A")


def _ha(value: Any) -> str:
    try:
        return f"{float(value):,.2f} ha"
    except (TypeError, ValueError):
        return "No disponible"


def _bar_chart(rows: list[tuple[str, float, str]], width=470, height=190) -> Drawing:
    drawing = Drawing(width, height)
    maximum = max([abs(float(value)) for _, value, _ in rows] or [1]) or 1
    for index, (label, value, color) in enumerate(rows):
        y = height - 34 - index * 30
        drawing.add(String(0, y + 5, str(label)[:24], fontName="Helvetica", fontSize=8, fillColor=GRIS))
        drawing.add(Rect(125, y, 260, 15, fillColor=colors.HexColor("#E6ECF4"), strokeColor=None))
        drawing.add(Rect(125, y, max(2, 260 * abs(float(value)) / maximum), 15, fillColor=colors.HexColor(color), strokeColor=None))
        drawing.add(String(395, y + 4, f"{float(value):,.2f}", fontName="Helvetica-Bold", fontSize=8, fillColor=AZUL))
    return drawing


def _signal_evidence_rows(evaluation: dict[str, Any]) -> list[list[str]]:
    metrics = evaluation.get("metrics") or {}
    periods = evaluation.get("periods") or {}
    signals = evaluation.get("signals") or {}
    contributions = evaluation.get("contributions") or {}
    evidence = {
        "tmf": (
            f"Deforestacion {_ha(metrics.get('tmf_deforestacion'))}; "
            f"degradacion {_ha(metrics.get('tmf_degradacion'))}",
            f"JRC TMF {periods.get('jrc_diagnostico', 'diagnostico')}",
        ),
        "hansen": (
            f"Perdida posterior a 2020: {_ha(metrics.get('hansen_post'))}",
            f"Hansen hasta {periods.get('hansen_diagnostico', 'diagnostico')}",
        ),
        "esri": (
            f"Salida de arboles: {_ha(metrics.get('esri_salida'))}",
            f"ESRI {periods.get('esri_inicial', '?')}-{periods.get('esri_final', '?')}",
        ),
        "gedi": (
            f"Altura media {float(metrics.get('gedi_altura') or 0):,.2f} m; "
            f"cobertura valida {float(metrics.get('gedi_cobertura_pct') or 0):,.1f}%",
            "GEDI, contexto estructural",
        ),
        "ndvi": (
            f"Disminucion: {_ha(metrics.get('ndvi_disminucion'))}; "
            f"delta medio {float(metrics.get('ndvi_delta_medio') or 0):,.3f}",
            f"Sentinel-2 {periods.get('ndvi_inicial', '?')}-{periods.get('ndvi_final', '?')}",
        ),
    }
    labels = {"tmf": "JRC TMF", "hansen": "Hansen GFC", "esri": "ESRI LULC", "gedi": "GEDI", "ndvi": "Sentinel-2 NDVI"}
    rows = [["Fuente", "Estado", "Aporte", "Evidencia y periodo"]]
    for key in ("tmf", "hansen", "esri", "gedi", "ndvi"):
        detail, period = evidence[key]
        rows.append([
            labels[key],
            "Activa" if signals.get(key) else "Sin señal",
            f"{float(contributions.get(key) or 0):,.1f} puntos",
            f"{detail}. {period}.",
        ])
    return rows


def generar_informe_tecnico(registro: dict[str, Any]) -> bytes:
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCHCP", parent=styles["Title"], textColor=AZUL, fontSize=24, leading=29, alignment=TA_CENTER, spaceAfter=16))
    styles.add(ParagraphStyle(name="H2CHCP", parent=styles["Heading2"], textColor=AZUL, fontSize=15, leading=19, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyCHCP", parent=styles["BodyText"], textColor=GRIS, fontSize=9.2, leading=14))
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=1.6*cm, leftMargin=1.6*cm, topMargin=1.7*cm, bottomMargin=1.6*cm, title="Informe técnico · Geoportal CHCP")
    story: list[Any] = []
    area = registro.get("area") or {}
    result = registro.get("result") or {}
    kind = registro.get("kind", "resultado")
    identifier = registro.get("result_id") or registro.get("identifier") or "sin identificador"
    story += [Spacer(1, 1.3*cm), Paragraph("Geoportal de Conectividad Ecológica de la Cuenca Hidrográfica del Canal de Panamá", styles["TitleCHCP"]), Paragraph("Informe técnico de preevaluación", styles["H2CHCP"]), Paragraph(f"<b>Territorio:</b> {area.get('label','Área seleccionada')}<br/><b>Resultado:</b> {identifier}<br/><b>Fecha de generación:</b> {datetime.now().strftime('%Y-%m-%d')}<br/><b>Módulo:</b> {kind}", styles["BodyCHCP"]), Spacer(1, .7*cm)]
    geometry = area.get("geometry")
    if geometry:
        map_payload = {"area_objetivo_geojson":{"type":"Feature","properties":{},"geometry":geometry}}
        story += [crear_mapa_fragmentacion(map_payload), Paragraph("Figura 1. Ubicación del área analizada. El mapa muestra el ámbito del resultado; no representa por sí solo condición ecológica.", styles["BodyCHCP"])]
    story += [PageBreak(), Paragraph("Resumen ejecutivo", styles["H2CHCP"]), Paragraph("Este documento utiliza únicamente el resultado ya calculado. No vuelve a ejecutar Earth Engine. Las conclusiones son indicativas y requieren interpretación técnica y, cuando corresponda, verificación de campo.", styles["BodyCHCP"])]

    evaluation = result.get("evaluation") if kind == "integrated_ecological_analysis" else result if kind == "ecological_evaluation" else None
    structure = result.get("structure") if kind == "integrated_ecological_analysis" else result if kind == "structural_connectivity" else None
    if evaluation:
        rows = [["Indicador", "Resultado", "Período / alcance"], ["Prioridad territorial", evaluation.get("priority","No disponible"), "Períodos fijos del diagnóstico"], ["Índice de indicios", f"{evaluation.get('score','—')} / {evaluation.get('maximum_score',6.5)}", "No es probabilidad"]]
        visit = evaluation.get("visit_priority") or {}
        story += [Table(rows, colWidths=[5.2*cm,5.2*cm,6.0*cm], style=[("BACKGROUND",(0,0),(-1,0),AZUL),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor('#C7D4E5')),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8.5),("PADDING",(0,0),(-1,-1),7)]), Paragraph("Interpretación del resultado", styles["H2CHCP"]), Paragraph(f"<b>Prioridad de visita:</b> {visit.get('prioridad_visita', 'No disponible')}. {visit.get('lectura_integrada', '')} {visit.get('foco_visita', '')}", styles["BodyCHCP"]), Paragraph("Señales de preevaluación", styles["H2CHCP"])]
        contributions = evaluation.get("contributions") or {}
        colors_by_source = {"tmf":"#166B51","hansen":"#C43D2B","esri":"#276C98","gedi":"#68439A","ndvi":"#6F8F14"}
        story += [_bar_chart([(key.upper(), float(value or 0), colors_by_source.get(key,"#073F8C")) for key,value in contributions.items()]), Paragraph("Figura 2. Aportes al índice. Las barras muestran puntos, no probabilidad ni superficie afectada.", styles["BodyCHCP"]), PageBreak(), Paragraph("Evidencia por fuente", styles["H2CHCP"]), Table(_signal_evidence_rows(evaluation), colWidths=[2.7*cm,2.4*cm,2.3*cm,9.0*cm], repeatRows=1, style=[("BACKGROUND",(0,0),(-1,0),AZUL),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor('#C7D4E5')),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),7.8),("PADDING",(0,0),(-1,-1),6)])]
        consistency = evaluation.get("consistency") or {}
        story += [Paragraph("Consistencia entre fuentes", styles["H2CHCP"]), Paragraph(f"<b>{consistency.get('nivel', 'No disponible')}.</b> {consistency.get('detalle', '')}", styles["BodyCHCP"])]
        corridor = registro.get("corridor_context") or {}
        if corridor:
            names = ", ".join(item.get("nombre", "") for item in corridor.get("corredores", []) if item.get("nombre")) or "Ninguno"
            story += [Paragraph("Contexto de corredores publicados", styles["H2CHCP"]), Table([["Indicador", "Resultado"],["Área dentro de corredores", _ha(corridor.get("area_en_corredores_ha"))],["Proporción del territorio", f"{float(corridor.get('porcentaje_aoi_en_corredores') or 0):,.2f}%"],["Corredores", names]], colWidths=[6.0*cm,10.4*cm], style=[("BACKGROUND",(0,0),(-1,0),AZUL),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor('#C7D4E5')),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8.2),("PADDING",(0,0),(-1,-1),6)]), Paragraph("La superposición aporta contexto estratégico a la prioridad de visita; no prueba conectividad funcional.", styles["BodyCHCP"])]
    if structure:
        landscape = structure.get("metricas_clase") or {}
        network = structure.get("metricas_red") or {}
        story += [PageBreak(), Paragraph("Fragmentación y conectividad estructural", styles["H2CHCP"]), Table([["Métrica","Valor"],["Superficie forestal",_ha(landscape.get("area_total_bosque_ha"))],["Número de parches",str(landscape.get("numero_parches","No disponible"))],["Componentes",str(network.get("numero_componentes","No disponible"))],["Parches aislados",str(network.get("numero_parches_aislados","No disponible"))],["Conexiones",str(network.get("numero_aristas","No disponible"))]], colWidths=[8*cm,8*cm], style=[("BACKGROUND",(0,0),(-1,0),AZUL),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor('#C7D4E5')),("PADDING",(0,0),(-1,-1),7)])]
        story += [crear_mapa_fragmentacion(structure), Paragraph("Figura 3. Parches dentro del área objetivo. El contexto exterior no aumenta la superficie reportada.", styles["BodyCHCP"]), Spacer(1, 8), crear_mapa_conectividad(structure), Paragraph("Figura 4. Relaciones estructurales potenciales. Las líneas no demuestran desplazamiento de fauna ni conectividad funcional.", styles["BodyCHCP"])]
    if kind in {"official_coverage_2021", "official_coverage_2023"}:
        classes = (result.get("statistics") or {}).get("classes") or []
        story += [Paragraph("Cobertura clasificada", styles["H2CHCP"]), _bar_chart([(row.get("label","Clase"), float(row.get("area_ha") or 0), ["#176B45","#9A7A3E","#1976A8"][index % 3]) for index,row in enumerate(classes)]), Paragraph("Las superficies se calculan sobre datos válidos. NoData no se interpreta como pérdida ni ausencia forestal.", styles["BodyCHCP"])]
    if kind == "structural_comparison_2021_2023":
        scenarios = result.get("scenarios") or {}
        comparison_rows = [["Métrica", "Referencia 2021", "Diagnóstico 2023"]]
        for label, section, key, formatter in (
            ("Superficie forestal", "metricas_clase", "area_total_bosque_ha", _ha),
            ("Número de parches", "metricas_clase", "numero_parches", str),
            ("Componentes", "metricas_red", "numero_componentes", str),
            ("Parches aislados", "metricas_red", "numero_parches_aislados", str),
            ("Conexiones modeladas", "metricas_red", "numero_aristas", str),
        ):
            value_2021 = (scenarios.get("2021") or {}).get(section, {}).get(key)
            value_2023 = (scenarios.get("2023") or {}).get(section, {}).get(key)
            comparison_rows.append([
                label,
                formatter(value_2021) if value_2021 is not None else "No disponible",
                formatter(value_2023) if value_2023 is not None else "No disponible",
            ])
        story += [
            Paragraph("Escenarios estructurales 2021 y 2023", styles["H2CHCP"]),
            Paragraph(result.get("interpretation", ""), styles["BodyCHCP"]),
            Table(comparison_rows, colWidths=[6.0*cm,5.2*cm,5.2*cm], style=[
                ("BACKGROUND",(0,0),(-1,0),AZUL),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("GRID",(0,0),(-1,-1),.4,colors.HexColor('#C7D4E5')),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8.2),
                ("PADDING",(0,0),(-1,-1),6),
            ]),
            Paragraph("Las columnas son diagnósticos paralelos. No se calcula una pérdida o ganancia causal entre cartografías de distinto método y soporte.", styles["BodyCHCP"]),
        ]
        for year in ("2021", "2023"):
            scenario = scenarios.get(year) or {}
            story += [
                PageBreak(),
                Paragraph(f"Estructura forestal del escenario {year}", styles["H2CHCP"]),
                crear_mapa_fragmentacion(scenario),
                Paragraph(f"Parches del escenario {year}. El área exterior de contexto no incrementa la superficie del AOI.", styles["BodyCHCP"]),
                Spacer(1, 8),
                crear_mapa_conectividad(scenario),
                Paragraph(f"Conexiones estructurales modeladas del escenario {year}; no representan corredores biológicos oficiales ni movimiento de fauna.", styles["BodyCHCP"]),
            ]
    warnings = registro.get("warnings") or result.get("limitations") or []
    story += [PageBreak(), Paragraph("Fuentes, limitaciones y uso responsable", styles["H2CHCP"]), Paragraph("El resultado conserva las fuentes, períodos y parámetros registrados en resultado_completo.json. Las coberturas oficiales, JRC, ESRI, Hansen, Sentinel-2, GEDI y ERI mantienen definiciones distintas.", styles["BodyCHCP"])]
    for warning in warnings: story.append(Paragraph(f"• {warning}", styles["BodyCHCP"]))
    story += [Spacer(1, 10), Paragraph("Este informe es una preevaluación. No confirma deforestación ilegal, no acredita cumplimiento normativo, no sustituye una evaluación ambiental oficial y no prueba movimiento real de fauna.", styles["BodyCHCP"]), Paragraph("Atribuciones", styles["H2CHCP"]), Paragraph("Fuentes utilizadas según el módulo ejecutado: JRC Tropical Moist Forest, Hansen Global Forest Change, ESRI Land Use/Land Cover, Sentinel-2, GEDI y Almanaque Azul. Las coberturas institucionales SINIA-MiAMBIENTE solo se incluyen cuando el resultado correspondiente fue calculado.", styles["BodyCHCP"])]

    def footer(canvas, doc):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#C7D4E5")); canvas.line(1.6*cm,1.15*cm,A4[0]-1.6*cm,1.15*cm); canvas.setFillColor(GRIS); canvas.setFont("Helvetica",7.5); canvas.drawString(1.6*cm,.75*cm,"Preevaluación territorial indicativa · requiere verificación"); canvas.drawRightString(A4[0]-1.6*cm,.75*cm,f"Página {doc.page}"); canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
