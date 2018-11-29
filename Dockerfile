# https://stackoverflow.com/questions/53449347/containerising-python-command-line-application/53450791?noredirect=1#comment93788536_53450791
# https://github.com/jfloff/alpine-python
#

#
# Release:
#
# docker login --username=miohtama
# docker tag miohtama/sto:latest miohtama/sto:0.1
# docker push miohtama/sto:latest
# docker push miohtama/sto:0.1
#


FROM jfloff/alpine-python:3.6
MAINTAINER Mikko Ohtamaa <mikko@tokenmarket.net>
ADD . /myapp
WORKDIR /myapp
RUN apk add libffi-dev openssl-dev sqlite-dev
RUN pip install -U pip
RUN pip install -r requirements.txt
RUN pip install -e .

ENTRYPOINT ["sto"]