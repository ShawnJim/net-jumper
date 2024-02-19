#!/bin/bash

# Check the system and set the package manager
if [ -f /etc/redhat-release ]; then
    PKG_MANAGER="yum"
    echo "System is CentOS"
elif [ -f /etc/lsb-release ]; then
    PKG_MANAGER="apt-get"
    echo "System is Ubuntu"
else
    echo "Unsupported system"
    exit 1
fi

# Check if /etc/v2ray/v2ray.key exists
if [ -f /etc/v2ray/v2ray.key ]; then
    echo "/etc/v2ray/v2ray.key already exists. Skipping..."
else
    echo "/etc/v2ray/v2ray.key does not exist. Performing necessary actions..."

    echo "请输入acme注册邮箱:"
    read -r input_email
    # Install packages
    if [ "$PKG_MANAGER" = "yum" ]; then
        sudo $PKG_MANAGER install -y openssl cronie socat curl || exit
    elif [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo $PKG_MANAGER update
        sudo $PKG_MANAGER install -y openssl cron socat curl || exit
    fi

    curl https://get.acme.sh | sh -s email="$input_email" || exit

    echo "请输入acme证书域名:"
    read -r input_domain
    /root/.acme.sh/acme.sh --issue -d "$input_domain" --standalone --keylength ec-256 --force || exit
    mkdir /etc/v2ray
    /root/.acme.sh/acme.sh --installcert -d "$input_domain" --ecc \
                              --fullchain-file /etc/v2ray/v2ray.crt \
                              --key-file /etc/v2ray/v2ray.key || exit
    (crontab -l 2>/dev/null; echo "0 0 1 * * /root/.acme.sh/acme.sh --renew -d $input_domain --force --ecc") | crontab -
fi
