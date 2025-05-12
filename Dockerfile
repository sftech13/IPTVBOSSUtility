# Use a lightweight base image with Python 3.8
FROM python:3.8-slim

LABEL maintainer="SFTech13" \
    description="IPTV Stream Checker Builder"

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

# Copy the entire project into the container
COPY . /app

# Make sure the build script is executable
RUN chmod +x build_deb.sh

# Build the .deb package using dummy tag for dev
RUN GITHUB_REF_NAME=dev ./build_deb.sh

# Default command if container is run
CMD ["/bin/bash"]
