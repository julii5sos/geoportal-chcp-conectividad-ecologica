"""Servidor Flask para la versión HTML del Geoportal CHCP 2.0."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from pydantic import ValidationError

from gee_config import resolver_proyecto_gee
from territorio_local import nombres_subcuencas
from webapp.models import AnalysisRequest, EriRequest
from webapp.service import (
    RequestLimitError,
    build_download,
    configuration,
    run_analysis,
    run_eri,
    territory_payload,
)


ROOT = Path(__file__).resolve().parent


def create_app(*, testing: bool = False) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.update(
        TESTING=testing,
        MAX_CONTENT_LENGTH=int(os.getenv("WEB_MAX_REQUEST_BYTES", str(2 * 1024 * 1024))),
        JSON_SORT_KEYS=False,
    )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
        )
        return response

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            active="home",
            subbasin_count=len(nombres_subcuencas()),
            project_id=resolver_proyecto_gee(),
            use_map=True,
        )

    @app.get("/platform")
    def platform():
        return render_template(
            "platform.html",
            active="platform",
            project_id=resolver_proyecto_gee(),
            use_map=True,
            app_page=True,
        )

    @app.get("/methodology")
    def methodology():
        return render_template("methodology.html", active="methodology")

    @app.get("/about")
    def about():
        return render_template("about.html", active="about")

    @app.get("/api/v1/health")
    def health():
        return jsonify(
            status="ok",
            application="Geoportal CHCP 2.0 HTML",
            project_id=resolver_proyecto_gee(),
            earth_engine="lazy",
        )

    @app.get("/api/v1/config")
    def api_config():
        return jsonify(configuration())

    @app.get("/api/v1/territory")
    def api_territory():
        return jsonify(territory_payload())

    @app.post("/api/v1/analyses")
    def api_analysis():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="La solicitud debe contener un objeto JSON."), 400
        try:
            model = AnalysisRequest.model_validate(payload)
            return jsonify(run_analysis(model))
        except ValidationError as exc:
            return jsonify(error="Revise los parámetros.", details=exc.errors(include_url=False)), 400
        except RequestLimitError as exc:
            return jsonify(error=str(exc), code="request_limit"), 413
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except Exception:
            error_id = uuid.uuid4().hex[:10]
            app.logger.exception("Análisis web fallido [%s]", error_id)
            return jsonify(
                error="No se pudo completar el análisis con Earth Engine.",
                support_id=error_id,
            ), 502

    @app.post("/api/v1/eri")
    def api_eri():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="La solicitud debe contener un objeto JSON."), 400
        try:
            model = EriRequest.model_validate(payload)
            return jsonify(run_eri(model))
        except ValidationError as exc:
            return jsonify(error="Revise el área.", details=exc.errors(include_url=False)), 400
        except RequestLimitError as exc:
            return jsonify(error=str(exc), code="request_limit"), 413
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except Exception:
            error_id = uuid.uuid4().hex[:10]
            app.logger.exception("ERI web fallido [%s]", error_id)
            return jsonify(
                error="No se pudo completar el ERI complementario.",
                support_id=error_id,
            ), 502

    @app.get("/api/v1/results/<identifier>/download.zip")
    def api_download(identifier: str):
        content = build_download(identifier)
        if content is None:
            return jsonify(error="El resultado no existe o expiró."), 404
        from io import BytesIO

        return send_file(
            BytesIO(content),
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"geoportal_chcp_{identifier[:8]}.zip",
        )

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="La solicitud supera el tamaño máximo permitido."), 413

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8080")), debug=False)

