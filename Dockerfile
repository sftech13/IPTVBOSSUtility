FROM python:3.8-slim

LABEL maintainer="SFTech13" \
    description="IPTV Stream Checker Builder"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update &&
    apt-get install -y --no-install-recommends \
        python3-tk \
        ffmpeg \
        tk \
        build-essential \
        dpkg-dev \
        patchelf \
        desktop-file-utils \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxft2 \
        libgl1 \
        libglib2.0-0 \
        git \
        curl &&
    pip install --upgrade pip pyinstaller &&
    apt-get clean &&
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN chmod +x build_deb.sh
RUN GITHUB_REF_NAME=dev ./build_deb.sh

CMD ["/bin/bash"]
