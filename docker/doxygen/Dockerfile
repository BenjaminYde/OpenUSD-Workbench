FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        # cpp
        build-essential \
        # networking & remote
        curl \
        wget \
        tar \
        # doxygen dependencies
        python3.12-dev \
        flex \
        bison \
        # permissions
        ca-certificates \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Install CMake
ENV CMAKE_VERSION=3.31.8
RUN \
    # Install CMake
    cd /tmp && \
    wget --no-check-certificate https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    tar -xzvf cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    mv cmake-${CMAKE_VERSION}-linux-x86_64 /opt/cmake && \
    rm cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    # Install CMake Tools
    apt update && \
    apt -qq install -y --no-install-recommends \
        graphviz \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists
ENV PATH="/opt/cmake/bin:${PATH}"

# Download and unzip DoxyGen
ENV DOXYGEN_INSTALL_DIR=/opt/doxygen
RUN wget -q https://github.com/doxygen/doxygen/releases/download/Release_1_16_1/doxygen-1.16.1.src.tar.gz -O /tmp/doxygen.tar.gz && \
    tar -xf /tmp/doxygen.tar.gz -C /tmp && \
    rm -f /tmp/doxygen.tar.gz && \
    cd /tmp/doxygen-* && \
    # cmake build & install
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$DOXYGEN_INSTALL_DIR && \
    cmake --build build -j$(nproc) && \
    cmake --install ./build
ENV PATH="/opt/doxygen/bin:$PATH"

# Log version-
CMD ["doxygen", "-v"]