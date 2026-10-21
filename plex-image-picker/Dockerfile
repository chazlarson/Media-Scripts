FROM python:3.12-slim
ENV TINI_VERSION=v0.19.0

COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /uvx /bin/

WORKDIR /
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./

RUN echo "**** install system packages ****" \
 && apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get install -y tzdata --no-install-recommends \
 && apt-get install -y wget curl nano \
 && wget -O /tini https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-"$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
 && chmod +x /tini \
 && uv sync --frozen --no-dev --no-install-project \
 && apt-get clean \
 && apt-get update \
 && apt-get check \
 && apt-get -f install \
 && apt-get autoclean \
 && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*
COPY . /

ENV PATH="/.venv/bin:$PATH"

VOLUME /assets

EXPOSE 5000
ENV FLASK_APP=app.py
ENTRYPOINT ["/tini", "--"]

CMD ["flask", "run", "--host=0.0.0.0"]

