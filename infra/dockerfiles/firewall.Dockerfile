FROM python:3.11-slim

WORKDIR /opt/firewall
COPY firewall/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY firewall/ ./
CMD ["python", "symbio_dns.py"]
