#!/bin/bash

echo "请输入acme注册邮箱:"
read -r input_email
curl https://get.acme.sh | sh -s email="$input_email" || exit
sudo apt-get install openssl cron socat curl || exit

echo "请输入acme证书域名:"
read -r input_domain
/root/.acme.sh/acme.sh --issue -d "$input_domain" --standalone --keylength ec-256 --force || exit
/root/.acme.sh/acme.sh --installcert -d "$input_domain" --ecc \
                          --fullchain-file /etc/v2ray/v2ray.crt \
                          --key-file /etc/v2ray/v2ray.key || exit
(crontab -l 2>/dev/null; echo "/root/.acme.sh/acme.sh --renew -d $input_domain --force --ecc") | crontab -