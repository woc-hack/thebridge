# this image provides REST access to GHTorrent database
FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip mysql-client libmysqlclient-dev && \
    pip3 install tornado mysqlclient sqlalchemy pandas

COPY app.py /

EXPOSE 9002

CMD python3 /app.py