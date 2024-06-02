FROM python:3.10-alpine

# COPY . /

# RUN python -m pip install -r requirements.txt

# CMD echo "Hello world"

COPY requirements.txt requirements.txt
RUN echo "**** install system packages ****" \
 && apk update \
 && apk upgrade \
 && apk add tini ncdu \
 && pip3 install --no-cache-dir --upgrade --requirement /requirements.txt
#  && apt-get --purge autoremove gcc g++ libxml2-dev libxslt-dev libz-dev -y \
#  && apt-get clean \
#  && apt-get update \
#  && apt-get check \
#  && apt-get -f install \
#  && apt-get autoclean \
#  && rm -rf /requirements.txt /tmp/* /var/tmp/* /var/lib/apt/lists/*

COPY . /

VOLUME /config

ENTRYPOINT ["/sbin/tini", "-s", "python3", "media-scripts.py", "--"]