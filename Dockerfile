# Use Python 3.8 slim base
FROM python:3.8-slim-bullseye

LABEL maintainer="SFTech13" \
    description="Docker-based IPTV Stream Checker Builder"

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
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

# Set working directory
WORKDIR /app

# Copy project
COPY . .

# Make build script executable
RUN chmod +x build_deb.sh

# Build inside container (fallback tag if not provided)
ARG GITHUB_REF_NAME=dev
ENV GITHUB_REF_NAME=$GITHUB_REF_NAME

RUN ./build_deb.sh

# Optional: default command (remove if not using interactively)
CMD ["/bin/bash"]
