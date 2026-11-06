"""Servidor Flask para la versión HTML del Geoportal CHCP 2.0."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, render_template, request, send_file
from pydantic import ValidationError
from werkzeug.middleware.proxy_fix import ProxyFix

from gee_config import resolver_proyecto_gee
from territorio_local import nombres_subcuencas
from webapp.models import AnalysisRequest, EriRequest
from webapp.security import ConcurrencyGate, SlidingWindowRateLimiter
from webapp.service import (
    RequestLimitError,
    build_download,
    configuration,
    run_analysis,
    run_eri,
    territory_payload,
)


ROOT = Path(__file__).resolve().parent


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un número entero.") from exc
    return max(minimum, min(value, maximum))


def _validation_details(exc: ValidationError) -> list[dict[str, str]]:
    """No devuelve el valor de entrada, que podría contener una geometría completa."""

    return [
        {
            "location": ".".join(str(part) for part in error.get("loc", ())),
            "message": str(error.get("msg", "Parámetro inválido.")),
            "type": str(error.get("type", "validation_error")),
        }
        for error in exc.errors(include_url=False, include_input=False)
    ]


def create_app(*, testing: bool = False) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.update(
        TESTING=testing,
        MAX_CONTENT_LENGTH=_env_int(
            "WEB_MAX_REQUEST_BYTES",
            1024 * 1024,
            minimum=64 * 1024,
            maximum=4 * 1024 * 1024,
        ),
        JSON_SORT_KEYS=False,
    )
    if os.getenv("WEB_TRUST_PROXY_HEADERS", "").lower() in {"1", "true", "yes"}:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    window_seconds = _env_int("WEB_RATE_LIMIT_WINDOW_SECONDS", 600, minimum=60, maximum=3600)
    analysis_limiter = SlidingWindowRateLimiter(
        limit=_env_int("WEB_ANALYSIS_RATE_LIMIT", 4, minimum=1, maximum=60),
        window_seconds=window_seconds,
    )
    download_limiter = SlidingWindowRateLimiter(
        limit=_env_int("WEB_DOWNLOAD_RATE_LIMIT", 20, minimum=1, maximum=240),
        window_seconds=window_seconds,
    )
    analysis_gate = ConcurrencyGate(
        _env_int("WEB_MAX_CONCURRENT_ANALYSES", 1, minimum=1, maximum=4)
    )
    app.extensions["chcp_analysis_limiter"] = analysis_limiter
    app.extensions["chcp_download_limiter"] = download_limiter
    app.extensions["chcp_analysis_gate"] = analysis_gate

    def client_identity() -> str:
        if os.getenv("WEB_TRUST_IAP_HEADERS", "").lower() in {"1", "true", "yes"}:
            authenticated = request.headers.get("X-Goog-Authenticated-User-Email", "").strip()
            if authenticated:
                return f"iap:{authenticated.lower()}"
        return f"remote:{request.remote_addr or 'unknown'}"

    def check_rate_limit(limiter: SlidingWindowRateLimiter):
        decision = limiter.check(client_identity())
        g.rate_limit = decision
        if decision.allowed:
            return None
        response = jsonify(
            error="Se alcanzó el límite temporal de solicitudes. Intente más tarde.",
            code="rate_limit",
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(decision.retry_after)
        return response

    @app.before_request
    def request_safety_checks():
        g.request_id = uuid.uuid4().hex[:12]
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        fetch_site = request.headers.get("Sec-Fetch-Site", "").lower()
        if fetch_site == "cross-site":
            return jsonify(error="No se permiten solicitudes entre sitios.", code="cross_site"), 403
        origin = request.headers.get("Origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != request.host.lower():
                return jsonify(error="El origen de la solicitud no está autorizado.", code="origin"), 403
        return None

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
        response.headers.setdefault("X-Request-ID", getattr(g, "request_id", ""))
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        decision = getattr(g, "rate_limit", None)
        if decision is not None:
            response.headers.setdefault("RateLimit-Limit", str(decision.limit))
            response.headers.setdefault("RateLimit-Remaining", str(decision.remaining))
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
        )
        if request.path.startswith(("/api/v1/analyses", "/api/v1/eri", "/api/v1/results/")):
            response.headers.setdefault("Cache-Control", "no-store, private")
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
        if not request.is_json:
            return jsonify(error="Se requiere Content-Type application/json."), 415
        limited = check_rate_limit(analysis_limiter)
        if limited is not None:
            return limited
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="La solicitud debe contener un objeto JSON."), 400
        try:
            model = AnalysisRequest.model_validate(payload)
            if not analysis_gate.acquire():
                response = jsonify(
                    error="La instancia ya está procesando un análisis. Intente nuevamente.",
                    code="busy",
                )
                response.status_code = 429
                response.headers["Retry-After"] = "15"
                return response
            try:
                return jsonify(run_analysis(model))
            finally:
                analysis_gate.release()
        except ValidationError as exc:
            return jsonify(error="Revise los parámetros.", details=_validation_details(exc)), 400
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
        if not request.is_json:
            return jsonify(error="Se requiere Content-Type application/json."), 415
        limited = check_rate_limit(analysis_limiter)
        if limited is not None:
            return limited
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="La solicitud debe contener un objeto JSON."), 400
        try:
            model = EriRequest.model_validate(payload)
            if not analysis_gate.acquire():
                response = jsonify(
                    error="La instancia ya está procesando un análisis. Intente nuevamente.",
                    code="busy",
                )
                response.status_code = 429
                response.headers["Retry-After"] = "15"
                return response
            try:
                return jsonify(run_eri(model))
            finally:
                analysis_gate.release()
        except ValidationError as exc:
            return jsonify(error="Revise el área.", details=_validation_details(exc)), 400
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
        limited = check_rate_limit(download_limiter)
        if limited is not None:
            return limited
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

