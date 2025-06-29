FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Clear default sources and set custom sources.list with US mirror
RUN rm -f /etc/apt/sources.list.d/* && \
    echo "deb http://ftp.us.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://ftp.us.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    cat /etc/apt/sources.list

# Update and install packages, with optional intel-media-driver and libva-utils
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip vlc curl nano ffmpeg \
    --no-install-recommends && \
    apt-get install -y --no-install-recommends intel-media-driver libva-utils || \
    echo "Warning: intel-media-driver or libva-utils not found, continuing without them" && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m vlcuser

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir flask requests python-vlc

COPY app /app
COPY start.sh /start.sh

RUN chmod +x /start.sh && \
    chown -R vlcuser:vlcuser /app && \
    chmod -R u+w /app

USER vlcuser
CMD ["/start.sh"]
