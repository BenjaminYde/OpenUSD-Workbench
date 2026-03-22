FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive 
ARG DEVELOPER_UID=1000
LABEL Author="BenjaminYde"

# Install Development APT Packages
RUN --mount=type=cache,target=/var/cache/apt \
    apt -qq update && \
    apt -qq install -y --no-install-recommends \
        # general
        apt-utils \
        lsb-release \
        # git
        git \
        git-lfs \
        # files & io
        parallel \
        rsync \
        unzip \
        # networking & remote
        curl \
        ssh \
        openssh-client \
        wget \
        xdg-utils \
        gpg-agent \
        # cpp
        build-essential \
        ccache \
        autoconf \
        automake \
        dos2unix \
        g++ \
        gcc \
        gdb \
        make \
        ninja-build \
        software-properties-common \
        # permissions
        acl \
        sudo \
        gnupg \
        ca-certificates \
        # terminal
        bash-completion \
        nano \
        zsh \
        && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Install CMake
ENV CMAKE_VERSION 3.31.8
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

# Install Clang APT Packages
# Checkout the website: https://llvm.org/
# Checkout the website: https://apt.llvm.org/
# Checkout the website: https://apt.llvm.org/noble/pool/main/l/llvm-toolchain-20/
ENV CLANG_MAJOR_VERSION="20"
RUN \
    # Download and add the official LLVM GPG key
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    # # Add the LLVM repository
    echo "deb http://apt.llvm.org/$(lsb_release -sc)/ llvm-toolchain-$(lsb_release -sc)-${CLANG_MAJOR_VERSION} main" > /etc/apt/sources.list.d/llvm-${CLANG_MAJOR_VERSION}.list && \
    # Install APT packages
    # - clang-XX: The C/C++ compiler
    # - lld-XX: The fast linker
    # - libc++-XX-dev: The C++ standard library headers
    # - libc++abi-XX-dev: The C++ ABI library headers
    apt update && apt install -y --no-install-recommends \
        clang-${CLANG_MAJOR_VERSION} \
        lld-${CLANG_MAJOR_VERSION} \
        libc++-${CLANG_MAJOR_VERSION}-dev \
        libc++abi-${CLANG_MAJOR_VERSION}-dev \
        clang-tools-${CLANG_MAJOR_VERSION} \
        clang-${CLANG_MAJOR_VERSION}-doc \
        libclang-common-${CLANG_MAJOR_VERSION}-dev \
        libclang-${CLANG_MAJOR_VERSION}-dev \
        clang-format-${CLANG_MAJOR_VERSION}  \
        libclang1-${CLANG_MAJOR_VERSION} \
        clangd-${CLANG_MAJOR_VERSION} \
        clang-tidy-${CLANG_MAJOR_VERSION} \
    && \
    # Create symlinks so you can just run `clang++`
ln -s /usr/bin/clang-${CLANG_MAJOR_VERSION} /usr/bin/clang && \
    ln -s /usr/bin/clang++-${CLANG_MAJOR_VERSION} /usr/bin/clang++ && \
    ln -s /usr/bin/clangd-${CLANG_MAJOR_VERSION} /usr/bin/clangd && \
    ln -s /usr/bin/clang-format-${CLANG_MAJOR_VERSION} /usr/bin/clang-format && \
    ln -s /usr/bin/clang-tidy-${CLANG_MAJOR_VERSION} /usr/bin/clang-tidy && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Install x11 & rendering dependencies
RUN apt-get update && apt-get install -y --install-recommends \
        # open gl
        libegl1-mesa-dev \    
        libgl1-mesa-dev \
        libgles2-mesa-dev \
        # x general
        libxrandr-dev \
        libxinerama-dev \
        libxcursor-dev \
        xauth \
        libx11-dev \
        libx11-xcb-dev \
        libxi-dev \
        libxcb1-dev \
        libxcb-randr0-dev \
        libxfixes-dev \
        libxss-dev \
        libxkbcommon-dev \
        libxt-dev \
        # other
        libxcb-shape0 \
        libdbus-1-3 \
        libxkbcommon-x11-0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-xinerama0 \
        libxcb-xinput0 \
        libxcb-xfixes0 \
        libxcb-cursor0 \
        libfontconfig1 \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Download and extract the LunarG Vulkan SDK
ENV VULKAN_SDK_VERSION 1.4.321.0
RUN cd /tmp && \
    curl -fL -O https://sdk.lunarg.com/sdk/download/${VULKAN_SDK_VERSION}/linux/vulkansdk-linux-x86_64-${VULKAN_SDK_VERSION}.tar.xz && \
    tar xvf vulkansdk-linux-x86_64-${VULKAN_SDK_VERSION}.tar.xz && \
    mkdir -p /opt/vulkansdk && \
    cp -r ${VULKAN_SDK_VERSION}/x86_64/* /opt/vulkansdk/ && \
    rm -rf /tmp/*
    
# Setup Vulkan SDK environment variables
ENV VULKAN_SDK="/opt/vulkansdk"
ENV PATH="${VULKAN_SDK}/bin:$PATH"
ENV LD_LIBRARY_PATH="${VULKAN_SDK}/lib:$LD_LIBRARY_PATH"
ENV VK_LAYER_PATH="${VULKAN_SDK}/etc/vulkan/explicit_layer.d"

# Set environment variables for NVIDIA and Vulkan
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES graphics,utility,compute
ENV VK_ICD_FILENAMES=/vulkan-icd/nvidia_icd.json

RUN ICD_NVIDIA="/vulkan-icd/nvidia_icd.json" && \
    mkdir -p /vulkan-icd && \
    touch /vulkan-icd/nvidia_icd.json \
    && echo '{' >> $ICD_NVIDIA \
    && echo '    "file_format_version" : "1.0.0",' >> $ICD_NVIDIA \
    && echo '    "ICD": {' >> $ICD_NVIDIA \
    && echo '        "library_path": "libGLX_nvidia.so.0",' >> $ICD_NVIDIA \
    && echo '        "api_version" : "1.4.321"' >> $ICD_NVIDIA \
    && echo '    }' >> $ICD_NVIDIA \
    && echo '}' >> /$ICD_NVIDIA

# Install vulkan dependencies
RUN apt-get update && apt-get install -y --install-recommends \
        libvulkan1 \
        libvulkan-dev \
        mesa-vulkan-drivers \
        vulkan-tools \
        libshaderc-dev \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Install system wide python
RUN apt-get update && apt-get install -y --install-recommends \
        python3.12-dev \
    && \
    # cleanup
    apt -qq clean && \
    apt -qq autoclean && \
    apt -qq remove && \
    apt -qq autoremove -y && \
    rm -rf /var/lib/apt/lists

# Install Python (UV)
COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /uvx /bin/
ENV UV_LINK_MODE=copy UV_NO_BUILD_ISOLATION=1
# Installed system wide packages because the uv python does not have some .so's available which we need for usd python bindings
#RUN uv python install 3.12

# Create Ubuntu User
ARG DEVELOPER_UID=1000
RUN deluser --remove-home ubuntu && \
useradd --create-home --user-group --groups sudo --uid ${DEVELOPER_UID} developer && \
printf "\ndeveloper ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER developer
ENV USER="developer" HOME="/home/developer"
WORKDIR $HOME

# Setup python environment
RUN --mount=type=cache,target=$HOME/.cache/uv,uid=${DEVELOPER_UID} \
    uv venv --python /usr/bin/python3.12 $HOME/py312 && \
    . $HOME/py312/bin/activate && \
    uv pip install uv_build==0.10.8
ENV PATH="$HOME/py312/bin:$PATH"
ENV VIRTUAL_ENV="$HOME/py312"

# Install Python Packages
RUN --mount=type=cache,target=$HOME/.cache/uv,uid=${DEVELOPER_UID} \
    uv pip install \
        PySide6==6.10.2 \
        PyOpenGL==3.1.10

# Install ZSH
RUN sudo apt install -y zsh && \
    sudo chsh -s /usr/bin/zsh && \
    # Install oh my zsh
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" && \
    # configure .zshrc
    cd ~ && \
    touch .zshrc && \
    sed -i 's/ZSH_THEME=.*/ZSH_THEME="eastwood"/' .zshrc && \
    echo "ZSH Installed"

# Install Emscripten SDK
RUN git clone https://github.com/emscripten-core/emsdk.git && \
    cd emsdk && \
    ./emsdk install latest && \
    ./emsdk activate latest

ENTRYPOINT ["/usr/bin/zsh"]