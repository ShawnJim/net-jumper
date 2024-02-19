#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
INPUT_OPENRESTY_DOMAIN=$1
INPUT_V2RAY_ENDPOINT=$2

# 拉取容器
docker pull shawnjm/openresty

sed -i "s/DOMAIN_REPLACE/$INPUT_OPENRESTY_DOMAIN/g" "$DIR"/../../resource/openresty/nginx.conf
sed -i "s/V2RAY_ENDPOINT/$INPUT_V2RAY_ENDPOINT/g" "$DIR"/../../resource/openresty/nginx.conf

# 运行容器
docker run -e TZ="Asia/Shanghai" --net=host \
  -v /etc/localtime:/etc/localtime:ro \
  -v "$DIR"/../../resource/openresty:/etc/nginx/conf.d \
  -v /etc/v2ray/:/etc/v2ray/ \
  -v "$DIR"/../../resource/subscribe:/usr/local/openresty/nginx/html/ \
  --restart always --name nginx -d shawnjm/openresty:latest