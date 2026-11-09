"""Registro único de las ocho coberturas oficiales suministradas para la CHCP.

El catálogo describe productos; no declara que un asset sea operativo hasta que
su tipo y acceso hayan sido verificados con la identidad de Earth Engine activa.
"""

from __future__ import annotations


ASSETS_SINIA: dict[str, dict[str, object]] = {
    "1992_historico": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_1992_COBERTURA_HISTORICA_RASTER30M",
        "nombre": "Cobertura histórica 1992",
        "anio": 1992, "tipo_esperado": "IMAGE", "resolucion": "30 m",
        "crs": "EPSG:32617", "nodata": 255, "estado": "acceso_tipo_verificados",
        "leyenda": {1:"Aguas Interiores",2:"Bosque Intervenido",3:"Bosque Maduro",4:"Bosque Secundario Maduro",5:"Manglar",6:"Otros Usos",7:"Rastrojos (Bosque Pionero)",8:"Sin categoría documentada",9:"Uso Agropecuario",10:"Uso Agropecuario de Subsistencia",11:"Vegetación Baja Inundable"},
        "limitacion": "El código 8 no tiene una categoría ecológica documentada; NoData no representa ausencia de bosque.",
    },
    "2000_historico": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2000_COBERTURA_HISTORICA_RASTER30M",
        "nombre": "Cobertura histórica 2000", "anio": 2000,
        "tipo_esperado": "IMAGE", "resolucion": "30 m", "crs": "EPSG:32617", "nodata": 255,
        "estado": "acceso_tipo_verificados",
        "leyenda": {1:"Agua",2:"Bosque Intervenido",3:"Bosque Maduro",4:"Bosque Secundario Maduro",5:"Manglar",6:"Otros Usos",7:"Rastrojos (Bosque Pionero)",8:"Uso Agropecuario",9:"Uso Agropecuario de Subsistencia",10:"Vegetación Baja Inundable"},
        "limitacion": "Los códigos no son intercambiables con 1992; en particular, el código 8 significa otra categoría.",
    },
    "2012_binario": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2012_BOSQUE_BINARIO_RASTER5M",
        "nombre": "Bosque / no bosque 2012", "anio": 2012,
        "tipo_esperado": "IMAGE", "resolucion": "5 m", "crs": "EPSG:32617", "nodata": 255,
        "estado": "acceso_tipo_verificados", "leyenda": {1:"Bosque",2:"No bosque"},
        "limitacion": "No bosque no equivale exclusivamente a agricultura.",
    },
    "2012_detallado": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2012_USO_SUELO_RASTER5M",
        "nombre": "Uso y cobertura detallada 2012", "anio": 2012,
        "tipo_esperado": "IMAGE", "resolucion": "5 m", "crs": "EPSG:32617", "nodata": 65535,
        "estado": "acceso_tipo_verificados",
        "leyenda": {1:"Bosque latifoliado mixto maduro",2:"Bosque latifoliado mixto secundario",3:"Bosque de mangle",4:"Bosque de orey",5:"Bosque de cativo",6:"Bosque de rafia",7:"Bosque plantado de coníferas",8:"Bosque plantado de latifoliadas",9:"Rastrojo y vegetación arbustiva",10:"Vegetación herbácea",11:"Vegetación baja inundable",12:"Afloramiento rocoso y tierra desnuda",13:"Playa y arenal natural",14:"Café",15:"Cítrico",16:"Palma aceitera",17:"Plátano/banano",18:"Otro cultivo permanente",19:"Arroz",20:"Caña de azúcar",21:"Horticultura mixta",22:"Maíz",23:"Piña",24:"Otro cultivo anual",25:"Área heterogénea de producción agropecuaria",26:"Pasto",27:"Superficie de agua",28:"Área poblada",29:"Infraestructura",30:"Explotación minera",31:"Estanque para acuicultura",32:"Salinera"},
        "limitacion": "Solo 32 categorías están documentadas; no se nombran códigos adicionales.",
    },
    "2019_general": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2019_COBERTURA_GENERAL_RASTER20M",
        "nombre": "Cobertura general 2019", "anio": 2019,
        "tipo_esperado": "IMAGE", "resolucion": "19.799712 m", "crs": "EPSG:32617", "nodata": 0,
        "estado": "acceso_tipo_verificados", "leyenda": {1:"Bosques y otras tierras boscosas",2:"Otras tierras",3:"Cuerpos de agua"},
        "limitacion": "La clase 1 no equivale automáticamente a bosque natural.",
    },
    "2021_general": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2021_COBERTURA_GENERAL_VECTOR",
        "nombre": "Cobertura general oficial 2021", "anio": 2021,
        "tipo_esperado": "TABLE", "resolucion": "Vector institucional", "crs": "Según asset", "nodata": None,
        "estado": "acceso_tipo_verificados", "campo_tematico": "Categoria",
        "leyenda": {1:"Bosques y Otras Tierras Boscosas",2:"Otras Tierras",3:"Aguas Continentales"},
        "limitacion": "Las entidades no son equivalentes a parches forestales. Debe comprobarse equivalencia antes de migrar el motor original.",
    },
    "2021_detallado": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2021_USO_SUELO_RASTER10M",
        "nombre": "Uso y cobertura detallada 2021", "anio": 2021,
        "tipo_esperado": "IMAGE", "resolucion": "10 m", "crs": "EPSG:32617", "nodata": 255,
        "estado": "acceso_tipo_verificados",
        "leyenda": {
            **{code: f"Bosque natural · código {code}" for code in range(1, 7)},
            **{code: f"Bosque plantado · código {code}" for code in range(7, 9)},
            9: "Rastrojo y vegetación arbustiva",
            **{code: f"Código {code} sin documentación" for code in range(10, 34)},
        },
        "limitacion": "El asset contiene 33 códigos. Solo están documentados aquí los grupos 1–6, 7–8 y el código 9; los códigos restantes se muestran sin inventar categorías.",
    },
    "2023_general": {
        "asset_id": "projects/geoportal-513817/assets/SINIA_2023_COBERTURA_GENERAL_RASTER10M",
        "nombre": "Cobertura general diagnóstica 2023", "anio": 2023,
        "tipo_esperado": "IMAGE", "resolucion": "10 m", "crs": "EPSG:32617", "nodata": 0,
        "estado": "integrado_sin_validacion_comparativa", "leyenda": {1:"Bosques y otras tierras boscosas",2:"Otras tierras",3:"Superficie de agua"},
        "limitacion": "Escenario diagnóstico; no demuestra pérdida o ganancia respecto de 2021 sin dictamen de comparabilidad.",
    },
}


def catalogo_assets_sinia() -> list[dict[str, object]]:
    return [{"clave": clave, **ficha} for clave, ficha in ASSETS_SINIA.items()]
