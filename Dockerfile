FROM debian:9
MAINTAINER Tina Cochet "tina.cochet@viaa.be"

RUN apt-get update && apt-get install -y python3-pip 

RUN apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
    python3-virtualenv virtualenv  dh-autoreconf  autotools-dev sudo git libpq-dev

RUN mkdir /app

RUN virtualenv -p /usr/bin/python3 /app/venv
RUN . /app/venv/bin/activate; pip3 install --upgrade pip3 ;pip3 install slackclient  pandas numpy psycopg2 
RUN apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false  libfreetype6-dev libfreetype6 libpng16-16 libpng-dev pkg-config

RUN . /app/venv/bin/activate; pip3 install matplotlib



ADD archsbot.py /app/ 
ADD archstats.py /app/
WORKDIR /app
ADD config.ini /app/
EXPOSE 8080 8080
ENV LANG=C.UTF-8
CMD http_proxy='' https_proxy='' . /app/venv/bin/activate; python3 archsbot.py 
