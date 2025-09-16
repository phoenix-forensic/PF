"""Mini firewall DNS com bloqueio baseado em listas."""
from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path
from typing import List

import dns.message
import dns.query
import dns.rcode
from rich.console import Console
from rich.table import Table

DEFAULT_BLOCKLIST = Path(__file__).with_name("blocklist.txt")
FORWARDER = "8.8.8.8"
console = Console()


def load_blocklist(path: Path) -> List[str]:
    entries: List[str] = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line.lower())
    return entries


def should_block(hostname: str, blocklist: List[str]) -> bool:
    hostname = hostname.lower()
    return any(hostname.endswith(item) for item in blocklist)


def serve(port: int, blocklist: List[str]) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    console.print(f"[bold green]Firewall DNS escutando na porta {port}")
    while True:
        data, addr = sock.recvfrom(4096)
        request = dns.message.from_wire(data)
        qname = request.question[0].name.to_text().rstrip('.')

        if should_block(qname, blocklist):
            console.print(f"[bold red]Bloqueado[/bold red] {qname} de {addr[0]}")
            reply = dns.message.make_response(request)
            reply.set_rcode(dns.rcode.REFUSED)
            sock.sendto(reply.to_wire(), addr)
            continue

        upstream = dns.query.udp(request, FORWARDER, timeout=2)
        sock.sendto(upstream.to_wire(), addr)


def show_blocklist(blocklist: List[str]) -> None:
    table = Table(title="Entradas bloqueadas")
    table.add_column("Domínio")
    for entry in blocklist:
        table.add_row(entry)
    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Firewall DNS antifrágil")
    parser.add_argument("--port", type=int, default=5353)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--blocklist", type=Path, default=DEFAULT_BLOCKLIST)
    args = parser.parse_args()

    blocklist = load_blocklist(args.blocklist)

    if args.show:
        show_blocklist(blocklist)
        sys.exit(0)

    serve(args.port, blocklist)


if __name__ == "__main__":
    main()
