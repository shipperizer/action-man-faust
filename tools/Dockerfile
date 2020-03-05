FROM python:3.8-slim

RUN sed -i 's/httpredir.debian.org/cloudfront.debian.net/g' /etc/apt/sources.list

RUN apt-get update \
    && apt-get -y --no-install-recommends install build-essential libsnappy-dev zlib1g-dev libbz2-dev libgflags-dev liblz4-dev git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U pipenv

WORKDIR /var/app

COPY . .

RUN useradd -ms /bin/bash dude

RUN chown -R dude /var/app

RUN chmod 755 /var/app

USER dude

RUN pipenv update

CMD ["bash"]
