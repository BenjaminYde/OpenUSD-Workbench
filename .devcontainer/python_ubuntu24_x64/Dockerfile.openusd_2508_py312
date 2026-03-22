FROM ubuntu:24.04

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    USD_INSTALL_DIR=/opt/usd_2508_py312

# Install apt packages
RUN apt-get update && apt-get install -y --install-recommends \
        wget \
        unzip \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Download and unzip OpenUSD built from NVIDIA
RUN wget -q https://developer.nvidia.com/downloads/usd/usd_binaries/25.08/usd.py312.manylinux_2_35_x86_64.usdview.release-v25.08.71e038c1.zip \
    -O /tmp/usd_binaries.zip && \
    mkdir -p $USD_INSTALL_DIR && \
    unzip /tmp/usd_binaries.zip -d $USD_INSTALL_DIR && \
    rm /tmp/usd_binaries.zip