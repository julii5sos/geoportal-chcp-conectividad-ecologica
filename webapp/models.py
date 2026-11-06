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
    source: Literal["jrc_tmf", "esri_lulc"] = "jrc_tmf"
    initial_year: int
    final_year: int
    maximum_distance_m: float = Field(default=500, ge=50, le=5000)
    minimum_patch_area_ha: float = Field(default=0, ge=0, le=500)

    @model_validator(mode="after")
    def normalize_analyses(self):
        self.analyses = list(dict.fromkeys(self.analyses))
        if self.initial_year >= self.final_year:
            raise ValueError("El año inicial debe ser anterior al año final.")
        return self


class EriRequest(BaseModel):
    area: AreaSelection

