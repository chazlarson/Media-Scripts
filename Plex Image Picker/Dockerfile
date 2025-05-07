FROM python:3.9-slim
ENV TINI_VERSION=v0.19.0

WORKDIR /
COPY requirements.txt requirements.txt

RUN echo "**** install system packages ****" \
 && apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get install -y tzdata --no-install-recommends \
 && apt-get install -y wget curl nano \
 && wget -O /tini https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-"$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
 && chmod +x /tini \
 && pip3 install --no-cache-dir --upgrade --requirement /requirements.txt \
 && apt-get clean \
 && apt-get update \
 && apt-get check \
 && apt-get -f install \
 && apt-get autoclean \
 && rm -rf /requirements.txt /tmp/* /var/tmp/* /var/lib/apt/lists/*
 COPY . /

VOLUME /assets

EXPOSE 5000
ENV FLASK_APP=app.py
ENTRYPOINT ["/tini", "--"]

CMD ["flask", "run", "--host=0.0.0.0"]

