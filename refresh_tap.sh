#!/bin/bash
#

rm -rf /home/ma/Documents/_mon/intel_feeds/
git clone --depth=1 https://github.com/CriticalPathSecurity/Zeek-Intelligence-Feeds.git /home/ma/Documents/_mon/intel_feeds
chown -R ma:ma /home/ma/Documents/_mon/intel_feeds
mv /home/ma/Documents/_mon/intel_feeds/abuse-ch* /home/ma/Documents/_mon/pcap-did-what/zeek-docker/intel/
mv /home/ma/Documents/_mon/intel_feeds/alienvault.intel /home/ma/Documents/_mon/pcap-did-what/zeek-docker/intel/
cd /home/ma/Documents/_mon/pcap-did-what && docker compose down && docker volume rm --force pcap-did-what_shared-data && docker compose up -d
