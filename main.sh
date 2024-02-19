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


# 检查当前执行用户是否为root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root" >&2
    exit 1
fi

echo "Running as root, continue with the script..."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Asia/Shanghai" > /etc/timezone
# 调整时间
rm -rf /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# dependencies
# python
# Check if Python 3.11 is installed
if python3.11 --version 2>/dev/null; then
    echo "Python 3.11 is already installed."
else
    echo "Python 3.11 is not installed. Installing..."
    # Install Python 3.11
    if [ "$PKG_MANAGER" = "yum" ]; then
        sudo $PKG_MANAGER install -y epel-release
        sudo $PKG_MANAGER install -y python3.11
    elif [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo $PKG_MANAGER update
        sudo $PKG_MANAGER install -y python3.11
    fi
fi

# Check if pip is installed
if command -v pip &>/dev/null; then
    echo "pip is already installed."
else
    echo "pip is not installed. Installing..."

    # Install pip
    if [ -f /etc/redhat-release ]; then
        sudo yum install -y python3-pip
    elif [ -f /etc/lsb-release ]; then
        sudo apt-get install -y python3-pip
    else
        echo "Unsupported system"
        exit 1
    fi
fi

pip install Flask PyYAML || exit

echo "python install  done."

# docker
# Check if Docker is installed
if command -v docker &>/dev/null; then
    echo "Docker is already installed."
else
    echo "Docker is not installed. Installing..."
    echo "docker install  ..."
    if [ "$PKG_MANAGER" = "yum" ]; then
        sudo $PKG_MANAGER remove docker \
                        docker-client \
                        docker-client-latest \
                        docker-common \
                        docker-latest \
                        docker-latest-logrotate \
                        docker-logrotate \
                        docker-engine
        sudo $PKG_MANAGER install -y yum-utils
        sudo $PKG_MANAGER-config-manager \
            --add-repo \
            https://download.docker.com/linux/centos/docker-ce.repo
    elif [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo $PKG_MANAGER remove docker docker-engine docker.io containerd runc
        sudo $PKG_MANAGER update
        sudo $PKG_MANAGER install -y \
             apt-transport-https \
             ca-certificates \
             curl \
             gnupg-agent \
             software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository \
             "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
             $(lsb_release -cs) \
             stable"
    fi
    sudo $PKG_MANAGER install docker-ce docker-ce-cli containerd.io

    sudo systemctl start docker
    sudo systemctl enable docker
    echo "docker install done."
fi

# acme
echo "acme install ..."
chmod +x ./script/sh/acme.sh
"$DIR"/script/sh/acme.sh || exit


echo "请输入 v2ray 包装域名:"
read -r INPUT_OPENRESTY_DOMAIN
echo "请输入 v2ray endpoint:"
read -r INPUT_V2RAY_ENDPOINT
echo "请输入 v2ray uuid:"
read -r INPUT_V2RAY_UUID

# openresty
# Check if there is a container named openresty
if docker ps -a --format '{{.Names}}' | grep -q '^nginx$'; then
    echo "Container named nginx already exists. Skipping..."
else
    echo "Container named nginx does not exist. Performing necessary actions..."
    echo "openresty install ..."
    chmod +x "$DIR"/script/sh/openresty.sh
    "$DIR"/script/sh/openresty.sh "$INPUT_OPENRESTY_DOMAIN" "$INPUT_V2RAY_ENDPOINT" || exit
fi

# v2ray
# Check if there is a container named v2ray
if docker ps -a --format '{{.Names}}' | grep -q '^v2ray$'; then
    echo "Container named v2ray already exists. Skipping..."
else
    echo "Container named v2ray does not exist. Performing necessary actions..."
    echo "v2ray install ..."
    chmod +x "$DIR"/script/sh/v2ray.sh
    "$DIR"/script/sh/v2ray.sh "$INPUT_V2RAY_ENDPOINT" "$INPUT_V2RAY_UUID" || exit
fi


# iptables & refresher
echo "iptables & refresher install ..."
echo "请输入 vmess 协议名称:"
read -r INPUT_VMESS_NAME
echo "请输入 管理系统地址 (ip:port):"
read -r INPUT_SYSTEM_ADDRESS
sed -i "s/REPLACE_VMESS_NAME/$INPUT_VMESS_NAME/g" "$DIR"/script/sh/refresher.sh
sed -i "s/REPLACE_SYSTEM_ADDRESS/$INPUT_SYSTEM_ADDRESS/g" "$DIR"/script/sh/refresher.sh

chmod +x "$DIR"/script/sh/refresher.sh
"$DIR"/script/sh/refresher.sh || exit
(crontab -l 2>/dev/null; echo "0 0 * * * $DIR/script/sh/refresher.sh") | crontab -

# subscriber & manager_system
echo "是否安装管理web系统? (y/n)"
read -r answer
if [ "$answer" = "y" ]; then
    echo "run subscriber & manager_system"
    nohup python3 "$DIR"/script/python/backend/app.py "$DIR/resource/sqlite/vmess.sqlite" "$DIR/script/sh/refresher.sh" &
    PID=$!
    sleep 2  # 等待几秒以确保进程启动

    if ps -p $PID > /dev/null; then
        echo "进程启动成功"
    else
        exit 1
    fi
elif [ "$answer" = "n" ]; then
    echo "跳过安装."
else
    echo "Invalid input. Please enter 'y' or 'n'."
fi


# alerter
echo "vnstat install.."
docker pull vergoh/vnstat:2.12
docker run -d \
    --restart=unless-stopped \
    --network=host \
    -e HTTP_PORT=8685 \
    -v /etc/localtime:/etc/localtime:ro \
    -v /etc/timezone:/etc/timezone:ro \
    --name vnstat \
    vergoh/vnstat:2.12
echo "请输入监听的网卡："
read -r INPUT_INTERFACE
docker exec vnstat vnstat -i "$INPUT_INTERFACE" -d

echo "邮件配置开始..."
echo "请输入发件人："
read -r INPUT_SENDER_NAME
echo "请输入发件人邮箱："
read -r INPUT_SENDER_EMAIL
echo "请输入发件人邮箱密码："
read -r INPUT_SENDER_PASSWORD
echo "请输入收件人邮箱："
read -r INPUT_RECEIVER_EMAIL
echo "请输入告警阈值（GiB）："
read -r INPUT_THRESHOLD

alert_script="$DIR"/script/sh/mail-alerter.sh
sed -i "s/REPLACE_THRESHOLD/$INPUT_THRESHOLD/g" "$alert_script"
sed -i "s/REPLACE_SENDER_NAME/$INPUT_SENDER_NAME/g" "$alert_script"
sed -i "s/REPLACE_SENDER_EMAIL/$INPUT_SENDER_EMAIL/g" "$alert_script"
sed -i "s/REPLACE_SENDER_PASSWORD/$INPUT_SENDER_PASSWORD/g" "$alert_script"
sed -i "s/REPLACE_RECEIVER_EMAIL/$INPUT_RECEIVER_EMAIL/g" "$alert_script"
echo "邮件配置结束..."

"$DIR"/script/sh/mail-alerter.sh || exit
(crontab -l 2>/dev/null; echo "*/5 * * * * $alert_script") | crontab -

echo "安装完成"