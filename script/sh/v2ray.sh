#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

INPUT_V2RAY_ENDPOINT=$1
INPUT_V2RAY_UUID=$2

sed -i "s/V2RAY_ENDPOINT/$INPUT_V2RAY_ENDPOINT/g" "$DIR"/../../resource/v2ray/config.json
sed -i "s/V2RAY_UUID/$INPUT_V2RAY_UUID/g" "$DIR"/../../resource/v2ray/config.json

# 安装
docker run \
    -v "$DIR"/../../resource/v2ray/config.json:/usr/local/etc/v2ray/config.json \
    -p 13792:13792 \
    --restart always \
    --name v2ray -d shawnjm/v2ray:v1.0