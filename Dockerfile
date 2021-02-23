# docker build -t death-code .
# docker run -d --restart unless-stopped --name death-code -p 2020:80 death-code
# curl 127.0.0.1:2020

FROM tiangolo/uwsgi-nginx-flask:python3.8
LABEL maintainer="Andrew Dinh <death-code@andrewkdinh.com>"
LABEL version="0.3.0"

EXPOSE 80

ADD ./requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip && python3 -m pip install -r /app/requirements.txt

ADD ./templates /app/templates/
ADD ./main.py /app/main.py

HEALTHCHECK CMD curl http://localhost