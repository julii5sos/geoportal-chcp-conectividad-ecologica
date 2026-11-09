"""Contratos de entrada de la API web del Geoportal CHCP."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


AreaMode = Literal["draw", "subbasin", "basin"]
AnalysisKind = Literal["coverage", "fragmentation", "connectivity"]


class AreaSelection(BaseModel):
    mode: AreaMode
    geometry: dict[str, Any] | None = None
    subbasin: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def validate_selection(self):
        if self.mode == "draw" and not self.geometry:
            raise ValueError("Debe dibujar un polígono antes de ejecutar el análisis.")
        if self.mode == "subbasin" and not (self.subbasin or "").strip():
            raise ValueError("Debe seleccionar una subcuenca.")
        return self


class AnalysisRequest(BaseModel):
    analyses: list[AnalysisKind] = Field(min_length=1, max_length=3)
    area: AreaSelection
    source: Literal["jrc_tmf", "esri_lulc", "integrated"] = "jrc_tmf"
    initial_year: int
    final_year: int
    maximum_distance_m: float = Field(default=500, ge=50, le=5000)
    minimum_patch_area_ha: float = Field(default=0, ge=0, le=500)
    territory_id: str | None = Field(default=None, max_length=180)

    @model_validator(mode="after")
    def normalize_analyses(self):
        self.analyses = list(dict.fromkeys(self.analyses))
        if self.initial_year >= self.final_year:
            raise ValueError("El año inicial debe ser anterior al año final.")
        return self


class EriRequest(BaseModel):
    area: AreaSelection


class EcologicalEvaluationRequest(BaseModel):
    area: AreaSelection
    territory_id: str | None = Field(default=None, max_length=180)


class IntegratedEvaluationRequest(BaseModel):
    """Preevaluación original más estructura oficial 2021.

    El contrato conserva ambos cálculos como componentes identificables. La
    interfaz puede mostrar primero la preevaluación y solicitar después este
    resultado integral sin recalcularla gracias a la caché por firma.
    """

    area: AreaSelection
    maximum_distance_m: float = Field(default=500, ge=50, le=5000)
    minimum_patch_area_ha: float = Field(default=0, ge=0, le=500)
    selected_components: list[Literal["ecological", "fragmentation", "connectivity"]] = Field(
        default_factory=lambda: ["ecological", "fragmentation", "connectivity"],
        min_length=2,
        max_length=3,
    )
    territory_id: str | None = Field(default=None, max_length=180)

    @model_validator(mode="after")
    def validate_components(self):
        self.selected_components = list(dict.fromkeys(self.selected_components))
        if len(self.selected_components) < 2:
            raise ValueError("El análisis combinado requiere al menos dos componentes.")
        return self


class OfficialCoverageRequest(BaseModel):
    area: AreaSelection
    territory_id: str | None = Field(default=None, max_length=180)


class StructuralConnectivityRequest(BaseModel):
    area: AreaSelection
    scenario: Literal["official_2021", "diagnostic_2023"]
    maximum_distance_m: float = Field(default=500, ge=50, le=5000)
    minimum_patch_area_ha: float = Field(default=0, ge=0, le=500)
    territory_id: str | None = Field(default=None, max_length=180)


class StructuralComparisonRequest(BaseModel):
    """Dos diagnósticos estructurales paralelos con parámetros equivalentes.

    La respuesta no supone comparabilidad temática ni publica deltas causales.
    """

    area: AreaSelection
    maximum_distance_m: float = Field(default=500, ge=50, le=5000)
    minimum_patch_area_ha: float = Field(default=0, ge=0, le=500)
    territory_id: str | None = Field(default=None, max_length=180)


class EvidenceRequest(BaseModel):
    source: Literal["hansen_gfc", "sentinel_ndvi", "gedi", "worldcover", "sinia_2021", "firms"]
    area: AreaSelection
    initial_year: int | None = Field(default=None, ge=2000, le=2026)
    final_year: int | None = Field(default=None, ge=2000, le=2026)
    parameters: dict[str, Any] = Field(default_factory=dict)
    territory_id: str | None = Field(default=None, max_length=180)

    @model_validator(mode="after")
    def validate_period(self):
        if self.initial_year is not None and self.final_year is not None and self.initial_year > self.final_year:
            raise ValueError("El año inicial no puede ser posterior al final.")
        return self


class LayerPreviewRequest(BaseModel):
    source: Literal[
        "sentinel_ndvi",
        "jrc_tmf",
        "hansen_gfc",
        "esri_lulc",
        "gedi",
        "1992_historico",
        "2000_historico",
        "2012_binario",
        "2012_detallado",
        "2019_general",
        "2021_general",
        "2021_detallado",
        "2023_general",
    ]
    area: AreaSelection
    year: int | None = Field(default=None, ge=1990, le=2026)

