#!/bin/bash

linode-cli linodes create \
  --image 'linode/ubuntu24.04' \
  --interface_generation linode \
  --interfaces '[{"firewall_id":233159751,"public":{}}]' \
  --maintenance_policy linode/migrate \
  --region se-sto \
  --type g6-standard-4 \
  --label ubuntu-se-sto \
  --placement_group.id 860304 \
  --authorized_users jne \
  --disk_encryption enabled
