FROM alpine:3.7
RUN apk --no-cache add python3 iptables
ENV PYTHONUNBUFFERED=1
RUN python3 -m venv /app
COPY requirements.txt /app/requirements.txt
RUN /app/bin/pip install -r /app/requirements.txt
COPY firewall.py /app/bin/firewall.py
CMD ["/app/bin/python", "/app/bin/firewall.py"]
