FROM docker.io/library/python@sha256:dfd0b1fcad1f056d853631413b1e1a3afff81105a27e5ae7839a6b87389f5db8
MAINTAINER Tina Cochet "tina.cochet@viaa.be"


RUN apt-get update && apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
   dh-autoreconf  autotools-dev git libpq-dev \
   libfreetype6-dev libfreetype6 libpng16-16 libpng-dev pkg-config && \
   pip3 install slackclient psycopg2 pandas numpy  matplotlib elastic-apm==4.0.3 && \
   apt-get -y remove dh-autoreconf  autotools-dev git libpq-dev libfreetype6 pkg-config && \
   apt-get -y clean ; apt-get -y auto-clean && \
   rm -rf /var/lib/apt/lists/*


RUN mkdir /app

ADD archsbot.py /app/ 
ADD archstats.py /app/
WORKDIR /app
ADD config.ini /app/
EXPOSE 8080 8080
ENV LANG=C.UTF-8
CMD http_proxy='' https_proxy='' python3 archsbot.py 
