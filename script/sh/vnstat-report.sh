#!/bin/bash

# 情况上报
# 使用docker exec执行vnstat命令，然后用awk处理输出，最后通过read命令赋值给变量
IFS=";" read -r date rx tx total <<< $(docker exec vnstat vnstat -d 1 --oneline | awk -F";" '{print $3";"$4";"$5";"$6}')

curl --location 'http://REPLACE_SERVER_ADDRESS/vnstat/report' \
--header 'Content-Type: application/json' \
--data "{\"name\":\"REPLACE_VMESS_NAME\",\"day\":\"$date\",\"rx\":\"$rx\", \"tx\":\"$tx\", \"total\":\"$total\"}" > /dev/null 2>&1 || true