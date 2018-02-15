FROM debian:8.9
MAINTAINER Tina Cochet "tina.cochet@viaa.be"

RUN apt-get update && apt-get install -y python3-pip 

RUN apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
    python3-virtualenv virtualenv  dh-autoreconf  autotools-dev sudo git libpq-dev

RUN mkdir /app

RUN virtualenv -p /usr/bin/python3 /app/venv
RUN . /app/venv/bin/activate; pip3 install --upgrade pip3 ;pip3 install slackclient  pandas numpy psycopg2 
RUN apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false  libfreetype6-dev libfreetype6 libpng12-0 libpng12-dev pkg-config

RUN . /app/venv/bin/activate; pip3 install matplotlib



ADD archsbot.py /app/ 
ADD archstats.py /app/

RUN mkdir -p /home/tina && \
    echo "tina:x:1001:1001:Developer,,,:/home/tina:/bin/bash" >> /etc/passwd && \
    echo "tina:x:1001:" >> /etc/group && \
    echo "tina ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/tina && \
    chmod 0440 /etc/sudoers.d/tina && \
    chown tina:tina -R /home/tina && \
    chown root:root /usr/bin/sudo && chmod 4755 /usr/bin/sudo

USER tina
ENV HOME /home/tina
WORKDIR /app
EXPOSE 8080 8080
ENV LANG=C.UTF-8
CMD http_proxy='' https_proxy='' . /app/venv/bin/activate; python3 archsbot.py 
