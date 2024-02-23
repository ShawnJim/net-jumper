#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

export max_threshold=REPLACE_THRESHOLD                   # 流量阈值（GiB）
export sender_name="REPLACE_SENDER_NAME"
export sender_email="REPLACE_SENDER_EMAIL"  # 发件人邮箱
export sender_password="REPLACE_SENDER_PASSWORD"   # 发件人邮箱密码
export receiver_email="REPLACE_RECEIVER_EMAIL"     # 收件人邮箱

# 获取当日总流量（接收 + 发送）
total=$(docker exec vnstat vnstat -d 1 --oneline | awk -F";" '{print $6}' | awk '{if ($2 == "MiB") print $1 / 1024; else if ($2 == "KiB") print $1 / 1048576; else print $1}')

# 根据curl 获取流量阈值
system_address=REPLACE_SYSTEM_ADDRESS
vmess_name=REPLACE_VMESS_NAME
threshold=$(curl --location "http://$system_address/vnstat/threshold/$vmess_name/get" || echo "0")
# 检查获取的数据是否为空，如果为空，也将threshold设置为0
if [ -z "$threshold" ]; then
    threshold=max_threshold
fi

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

    current_v2ray_port_path="$DIR"/../../resource/iptables/current_v2ray_port.txt
    current_v2ray_port=$(cat "$current_v2ray_port_path")
    # 移除旧的 iptables 转发规则, 防止流量继续增加
    rule_numbers=$(sudo iptables -t nat -L PREROUTING --line-numbers | grep "$current_v2ray_port" | awk '{print $1}' | sort -r)
    for num in $rule_numbers; do
        sudo iptables -t nat -D PREROUTING "$num"
    done
fi