# https://stackoverflow.com/questions/53449347/containerising-python-command-line-application/53450791?noredirect=1#comment93788536_53450791
# https://github.com/jfloff/alpine-python
#

#
# Release:
#
# docker login --username=ilyaliko
# docker tag ilyaliko/tokfetch:latest ilyaliko/tokfetch:0.0.1
# docker push ilyaliko/tokfetch:latest
# docker push ilyaliko/tokfetch:0.0.1
#


FROM python:3.9-alpine
MAINTAINER Illia Likhoshva <ilyaliko64@gmail.com>
ADD . /tokfetch
WORKDIR /tokfetch
RUN apk add build-base libffi-dev openssl-dev sqlite-dev
RUN pip install -U pip
RUN pip install -r requirements.txt
RUN pip install -e .

ENTRYPOINT ["tokfetch"]