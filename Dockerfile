FROM python:3.10-slim AS compile-image
RUN apt-get update &&  apt-get install -y --no-install-recommends libpq-dev build-essential gcc libpng-dev libfreetype6-dev  pkg-config autoconf libtool automake git
RUN python -m venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install git+https://github.com/viaacode/chassis.py.git@development &&\
    pip install -r requirements.txt

FROM python:3.10-slim AS build-image
COPY --from=compile-image /opt/venv /opt/venv
RUN apt update && apt install -y libpq-dev libpng-dev libfreetype6-dev && rm -rf /var/lib/apt/lists/*
EXPOSE 8080 8080
ENV LANG=C.UTF-8
WORKDIR /app
COPY . .
RUN groupadd -r app && useradd -b / -r -g app app
RUN chown app:app /opt && chmod g+wx /opt
RUN chown -R app:0 /app && chmod -R g+rwx /app
USER app
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
CMD http_proxy='' https_proxy='' python3 archsbot.py
