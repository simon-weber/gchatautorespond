FROM python:3.7.9-slim-stretch

WORKDIR /app
EXPOSE 8000 50001 50002
ENV DJANGO_SETTINGS_MODULE=gchatautorespond.settings

COPY requirements.txt ./
RUN apt-get update \
  && apt-get install -y git \
  && pip install --no-cache-dir -r requirements.txt \
  && apt-get purge --auto-remove -y git \
  && rm -rf /var/lib/apt/lists/*

ADD docker-archive.tar ./

RUN groupadd --gid 499 gchatautorespond \
  && useradd --uid 497 --gid gchatautorespond --shell /bin/bash --create-home gchatautorespond
USER gchatautorespond:gchatautorespond
CMD ["gunicorn", "--worker-class", "gevent", "gchatautorespond.wsgi", "-b", "0.0.0.0:8000"]
