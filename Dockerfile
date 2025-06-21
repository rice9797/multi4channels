FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configure apt sources
RUN rm -f /etc/apt/sources.list.d/* && \
    echo "deb http://httpredir.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://httpredir.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://httpredir.debian.org/debian bookworm-backports main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    cat /etc/apt/sources.list

# Update package lists with debug
RUN apt-get update -o Debug::pkgProblemResolver=yes || { echo "apt-get update failed"; cat /var/log/apt/*.log; exit 1; } && \
    apt-cache policy python3.11 python3

# Install Python packages
RUN apt-get install -y python3.11 python3.11-venv python3-pip || \
    { echo "Failed to install python3.11, trying python3"; \
      apt-get install -y python3 python3-venv python3-pip || \
      { echo "apt-get install python3 failed"; exit 1; }; }

# Install other dependencies
RUN apt-get install -y \
    vlc curl nano \
    vainfo libva2 libva-drm2 libva-x11-2 libva-wayland2 libva-dev \
    intel-media-driver-non-free \
    && ls -l /usr/lib/x86_64-linux-gnu/dri/*_drv_video.so || echo "No VAAPI drivers found" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    || { echo "apt-get install dependencies failed"; exit 1; }

# Verify python3
RUN command -v python3 || { echo "python3 not found"; exit 1; } && \
    python3 --version

RUN useradd -m vlcuser && \
    groupadd -r render && \
    usermod -aG video,render vlcuser

RUN python3 -m venv /opt/venv || { echo "python3 -m venv failed"; exit 1; }
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir flask requests || { echo "pip install failed"; exit 1; }

COPY app /app
COPY photos/bg.jpg /app/photos/bg.jpg
COPY start.sh /start.sh

RUN chmod +x /start.sh && \
    chown -R vlcuser:vlcuser /app && \
    chmod -R u+w /app

USER vlcuser
CMD ["/start.sh"]
