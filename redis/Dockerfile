FROM ubuntu:20.10

RUN apt-get update
RUN apt-get install redis-server redis-tools -y
COPY redis.conf /etc/redis/redis.conf

EXPOSE 6379

CMD [ "redis-server", "/etc/redis/redis.conf", "--bind", "0.0.0.0" ]
