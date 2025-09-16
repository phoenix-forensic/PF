# gps-antifragil-v3

Ecossistema modular composto por backend Flask com Socket.IO, aplicativo Android Kotlin e firewall DNS para monitoramento antifrágil.

## Estrutura

```
gps-antifragil-v3/
├── api/                 # Backend Flask
├── modules/PFandroid/   # Aplicativo Android
├── modules/watch.user/  # Extensões para dispositivos vestíveis
├── firewall/            # Firewall DNS
├── infra/               # Dockerfiles e GitHub Actions
├── Makefile             # Atalhos de automação
└── SECURITY.md          # Política de segurança
```

## Como executar

### Backend
```bash
cd api
pip install -r requirements.txt
python artefato_tracker.py
```

### Android
```bash
cd modules/PFandroid
./gradlew assembleDebug
```

### Firewall DNS
```bash
cd firewall
pip install -r requirements.txt
python symbio_dns.py --show
```

## Testes
```bash
cd api
pytest
```
