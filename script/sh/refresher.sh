#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

vmess_name=REPLACE_VMESS_NAME
system_address=REPLACE_SYSTEM_ADDRESS

current_v2ray_port_path="$DIR"/../../resource/iptables/current_v2ray_port.txt

# 获取当前维护端口
current_v2ray_port=$(cat "$current_v2ray_port_path")
echo "当前维护端口: $current_v2ray_port"

# 将当前维护端口+1创建更新端口
((upgrade_port=current_v2ray_port+1))
echo "替换端口为: $upgrade_port"

# 删除旧 iptables 转发规则
#sudo iptables -t nat -L --line-numbers | grep "$current_v2ray_port" | awk '{print $1}' | xargs -I {} sudo iptables -t nat -D PREROUTING {}
rule_numbers=$(sudo iptables -t nat -L PREROUTING --line-numbers | grep "$current_v2ray_port" | awk '{print $1}' | sort -r)
for num in $rule_numbers; do
    sudo iptables -t nat -D PREROUTING $num
done

# iptables 转发调整
sudo iptables -t nat -A PREROUTING -p tcp --dport "$upgrade_port" -j REDIRECT --to-port 443

# 调整当前端口维护地址
sed -i "s/$current_v2ray_port/$upgrade_port/g" "$current_v2ray_port_path"

curl --location "https://$system_address/refresh_port" \
    --form "name=$vmess_name" \
    --form "port=$upgrade_port" > /dev/null 2>&1 || true