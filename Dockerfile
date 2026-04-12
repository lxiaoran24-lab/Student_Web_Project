FROM rocker/r-ver:4.4.1

# 设置环境变量，防止交互式弹窗阻塞安装
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（保留了你原有的全面配置，这很好）
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    git \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgit2-dev \
    libboost-dev \
    libboost-system-dev \
    libboost-filesystem-dev \
    zlib1g-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# 【关键修改】直接从 CRAN 安装 lightgbm 稳定版，删除了原来的 GitHub 安装命令
RUN R -e "install.packages(c('bnlearn', 'remotes', 'lightgbm'), repos='https://cloud.r-project.org/')"

# 复制项目所有文件
COPY . /app

# 启动命令
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app