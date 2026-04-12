FROM rocker/r-ver:4.4.1

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

RUN R -e "install.packages(c('bnlearn','remotes'), repos='https://cloud.r-project.org/')"
RUN R -e "remotes::install_github('microsoft/LightGBM', subdir='R-package')"

COPY . /app

CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app