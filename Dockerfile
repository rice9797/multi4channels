FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip vlc curl nano \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m vlcuser

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir flask requests

COPY app /app
COPY photos/bg.jpg /app/photos/bg.jpg
COPY start.sh /start.sh

RUN chmod +x /start.sh && \
    chown -R vlcuser:vlcuser /app && \
    chmod -R u+w /app

USER vlcuser
CMD ["/start.sh"]
