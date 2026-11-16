#!/bin/bash

MYIP='90.191.168.125'

# firewall shite
ufw --force reset
ufw allow from $MYIP to any port 22 proto tcp
ufw enable
# docker shite
sudo apt remove -y $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# install all the shite
sudo apt update
apt-get install -y ranger caca-utils highlight atool w3m poppler-utils mediainfo bat fzf ripgrep docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# helperz

adduser --gecos GECOS --disabled-password hmm
usermod -aG docker hmm

cat << 'EOF' >> /home/hmm/get_git_dir.sh
git clone --filter=blob:none --sparse https://github.com/sajjadium/ctf-archives.git .
git sparse-checkout add $1
EOF

chown -R hmm:hmm /home/hmm/get_git_dir.sh
chmod u+x get_git_dir.sh

mkdir /home/hmm/tseeteeeff
chown -R hmm:hmm /home/hmm/tseeteeeff

mkdir /home/hmm/.ssh
chmod 700 /home/hmm/.ssh
cat /root/.ssh/authorized_keys > /home/hmm/.ssh/authorized_keys
chmod 600 /home/hmm/.ssh/authorized_keys
chown -R hmm:hmm /home/hmm/.ssh
