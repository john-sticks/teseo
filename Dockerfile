FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DB_HOST=172.17.0.1 \
    DB_PORT=3306 \
    DB_NAME=teseo \
    CERBERUS_DB_NAME=usuarios \
    CERBERUS_HOST=172.17.0.1 \
    CERBERUS_PORT=8004 \
    DEBUG=False

EXPOSE 8007

CMD ["gunicorn", "ref_system.wsgi:application", "--bind", "0.0.0.0:8007", "--workers", "3"]
