"""Tarefas utilitárias para manutenção do banco de eventos."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from pathlib import Path

from artefato_tracker import Evento, db

LOGGER = logging.getLogger(__name__)


def purge_old_events(days: int = 30) -> int:
    """Remove eventos mais antigos que o número de dias configurado."""

    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = Evento.query.filter(Evento.timestamp < cutoff).delete()
    db.session.commit()
    LOGGER.info("Eventos anteriores a %s removidos (%s itens)", cutoff, deleted)
    return deleted


def export_snapshot(path: str = "snapshots/eventos.csv") -> Path:
    """Exporta um CSV com todos os eventos para auditoria manual."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as handler:
        handler.write(
            "id,source,tag,lat,lon,accuracy,provider,consent_federated,timestamp\n"
        )
        for evento in Evento.query.order_by(Evento.timestamp).all():
            handler.write(
                f"{evento.id},{evento.source},{evento.tag},{evento.lat},{evento.lon},"
                f"{evento.accuracy},{evento.provider},{evento.consent_federated},"
                f"{evento.timestamp.isoformat()}\n"
            )

    LOGGER.info("Snapshot exportado para %s", target)
    return target
