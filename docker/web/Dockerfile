FROM python:3.5
ADD sources.list /etc/apt/sources.list
RUN apt-get update && apt-get install -y \
        libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev
ADD requirements.pip /tmp/requirements.pip
RUN pip install -r /tmp/requirements.pip \
    --trusted-host pypi.douban.com \
    --index-url http://pypi.douban.com/simple/