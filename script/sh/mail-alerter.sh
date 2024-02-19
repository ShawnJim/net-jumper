#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

export threshold=REPLACE_THRESHOLD                   # 流量阈值（GiB）
export sender_name="REPLACE_SENDER_NAME"
export sender_email="REPLACE_SENDER_EMAIL"  # 发件人邮箱
export sender_password="REPLACE_SENDER_PASSWORD"   # 发件人邮箱密码
export receiver_email="REPLACE_RECEIVER_EMAIL"     # 收件人邮箱

# 获取当日总流量（接收 + 发送）
total=$(docker exec vnstat vnstat -d 1 --oneline | awk -F";" '{print $6}' | awk '{if ($2 == "MiB") print $1 / 1024; else if ($2 == "KiB") print $1 / 1048576; else print $1}')

# 检查流量是否超过阈值
if (( $(echo "$total > $threshold" | bc -l) )); then
    # 发送告警邮件
    subject="流量告警：流量使用超过 ${threshold}GiB"
    message_body="警告：当日使用流量已达 ${total}GiB，超过了设定阈值 ${threshold}GiB。"
    if python3 "$DIR"/../python/mail/mail.py $sender_email $sender_name $sender_password $receiver_email "$subject" "$message_body"; then
        echo "邮件已发送"
    else
        echo "邮件发送失败"
    fi
fi