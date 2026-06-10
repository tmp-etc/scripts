#!/bin/bash

MYIP=`curl -s https://ipinfo.io/what-is-my-ip | jq -r .ip`
sed -i -e "s/^MYIP.*/MYIP=\'${MYIP}\'/g" ./droplet-startup.sh

doctl compute droplet create \
    --image ubuntu-24-04-x64 \
    --size s-1vcpu-512mb-10gb \
    --region fra1 \
    --vpc-uuid 4d5cd72e-bd78-473b-9c88-9c05d62c0885 \
    --tag-names '' \
    --ssh-keys '56507237' \
    --user-data-file ./droplet-startup.sh \
    a
