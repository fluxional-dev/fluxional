# > 3.18 will break pip install
# https://github.com/pypa/pip/issues/12429
FROM alpine:3.18
RUN apk -v --no-cache --update add \
# Docker 23.0.6
docker \
# Nodejs 18.18.2
nodejs \
npm \
# Python 3.11
python3 \ 
py3-pip \
ca-certificates \
groff \
less \
bash \
make \
curl \
wget \
zip \
git \
aws-cli \
&& \
update-ca-certificates && \
# CDK 2.115.0
npm install -g aws-cdk@2.115.0
# CDK LIB 2.114.1
RUN pip install aws-cdk-lib==2.114.1
RUN pip install fluxional[all]