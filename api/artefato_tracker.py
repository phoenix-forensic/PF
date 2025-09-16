"""Flask backend providing artefact tracking and realtime telemetry."""
from __future__ import annotations

from datetime import datetime, timedelta
import csv
import hashlib
import io
import logging
import os
from typing import Any, Dict

import requests
from flask import (Flask, Response, jsonify, render_template, request,
                   send_file)
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from PIL import Image

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "chave-super-secreta")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "super-secreto")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///artefatos.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
jwt = JWTManager(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(
    filename="artefato.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class Evento(db.Model):
    """Evento capturado pelo pixel ou pela API."""

    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    ip_hash = db.Column(db.String(64), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    provider = db.Column(db.String(50))
    consent_federated = db.Column(db.Boolean, default=False)
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "tag": self.tag,
            "lat": self.lat,
            "lon": self.lon,
            "accuracy": self.accuracy,
            "provider": self.provider,
            "consent_federated": self.consent_federated,
            "timestamp": self.timestamp.isoformat(),
        }


@app.before_first_request
def init_db() -> None:
    """Ensure database tables exist before the first request."""

    db.create_all()
    logging.info("Banco de dados inicializado")


@app.route("/")
def dashboard() -> str:
    """Renderiza o dashboard com Socket.IO embutido."""

    return render_template("dashboard.html")


@app.route("/auth/token", methods=["POST"])
def login() -> Response:
    """Cria um token JWT simples para autenticação das APIs protegidas."""

    payload = request.get_json(force=True)
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        return jsonify({"error": "Credenciais ausentes"}), 400

    # Demo only: in production use hashed password storage
    if username != os.getenv("ARTEFATO_USER", "admin") or password != os.getenv(
        "ARTEFATO_PASS", "admin"
    ):
        return jsonify({"error": "Credenciais inválidas"}), 401

    token = create_access_token(identity=username)
    return jsonify({"access_token": token})


@app.route("/pixel/<source>/<tag>.png")
def pixel(source: str, tag: str) -> Response:
    """Pixel 1x1 utilizado para rastrear aberturas de e-mail ou acessos web."""

    img = Image.new("RGB", (1, 1), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    evento = registrar_evento(source, tag, provider="pixel")
    if evento:
        socketio.emit("novo_evento", _evento_payload(evento))

    return send_file(buf, mimetype="image/png")


@app.route("/track/<source>/<tag>")
def track(source: str, tag: str) -> Response:
    """Endpoint HTTP para registrar eventos com dados opcionais de geolocalização."""

    data = request.get_json(silent=True) or {}
    evento = registrar_evento(
        source,
        tag,
        lat=data.get("lat"),
        lon=data.get("lon"),
        accuracy=data.get("accuracy"),
        provider=data.get("provider", "api"),
        consent=data.get("consent_federated", False),
    )
    if evento:
        socketio.emit("novo_evento", _evento_payload(evento))
    return jsonify({"status": "tracked"})


@app.route("/events")
@jwt_required()
def list_events() -> Response:
    """Lista eventos recentes para consumo por dashboards seguros."""

    limit = int(request.args.get("limit", 50))
    eventos = Evento.query.order_by(Evento.timestamp.desc()).limit(limit).all()
    return jsonify([evento.to_dict() for evento in eventos])


@app.route("/export")
@jwt_required()
def export_events() -> Response:
    """Exporta os eventos em CSV para auditoria."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "source",
        "tag",
        "lat",
        "lon",
        "accuracy",
        "provider",
        "consent_federated",
        "timestamp",
    ])

    for evento in Evento.query.order_by(Evento.timestamp.desc()).all():
        writer.writerow(
            [
                evento.id,
                evento.source,
                evento.tag,
                evento.lat,
                evento.lon,
                evento.accuracy,
                evento.provider,
                evento.consent_federated,
                evento.timestamp.isoformat(),
            ]
        )

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=eventos.csv"
    return response


@socketio.on("connect")
def handle_connect():
    emit("connected", {"message": "Conexão estabelecida"})


@socketio.on("ping")
def handle_ping(message=None):
    emit("pong", {"status": "ok"})


def registrar_evento(
    source: str,
    tag: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    accuracy: float | None = None,
    provider: str | None = None,
    consent: bool = False,
) -> Evento | None:
    """Cria um evento persistido e registra logs estruturados."""

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "0.0.0.0")
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()

    if lat is None or lon is None:
        lat, lon = _buscar_geolocalizacao(ip)

    evento = Evento(
        source=source,
        tag=tag,
        ip_hash=ip_hash,
        lat=lat,
        lon=lon,
        accuracy=accuracy,
        provider=provider,
        consent_federated=consent,
        user_agent=request.headers.get("User-Agent"),
    )

    db.session.add(evento)
    db.session.commit()

    logging.info(
        "evento_cadastrado source=%s tag=%s lat=%s lon=%s provider=%s",
        source,
        tag,
        lat,
        lon,
        provider,
    )

    return evento


def _buscar_geolocalizacao(ip: str | None) -> tuple[float | None, float | None]:
    """Obtém geolocalização aproximada via serviço externo opcional."""

    if not ip or ip.startswith("127.") or ip == "0.0.0.0":
        return None, None

    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
        if response.ok:
            payload = response.json()
            return payload.get("latitude"), payload.get("longitude")
    except requests.RequestException:
        logging.warning("Falha ao consultar geolocalização", exc_info=True)
    return None, None


def _evento_payload(evento: Evento) -> Dict[str, Any]:
    return {
        "lat": evento.lat,
        "lon": evento.lon,
        "risk": avaliar_risco(evento),
        "tag": evento.tag,
        "source": evento.source,
        "timestamp": evento.timestamp.isoformat(),
    }


def avaliar_risco(evento: Evento) -> str:
    """Detecta rapidamente risco baseado em heurísticas simples."""

    if evento.accuracy and evento.accuracy > 1000:
        return "spoof"
    if not evento.lat or not evento.lon:
        return "unknown"
    return "low"


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
