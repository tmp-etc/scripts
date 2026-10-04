import json

"""
Privacy-preserving discovery. Modern clients (recent iOS, Android, Windows, macOS) increasingly prefer wildcard probes specifically to avoid leaking their preferred network list (PNL). Older clients used to send directed probes naming each remembered SSID—"is HomeNetwork here? is CoffeeShop here?"—which let anyone sniffing the air fingerprint and track the device and infer where it had been. Wildcard probes reveal nothing about remembered networks, so they became the privacy-conscious default.

... according to Claude
"""

with open('jason.json', 'r') as j:
    ze_dict = json.load(j)
    
    for d in ze_dict:
        if d['kismet.device.base.type'] != 'Wi-Fi AP':
            if probez := d.get('dot11.device', {}).get('dot11.device.probed_ssid_map'):
                for p in probez:
                    if p['dot11.probedssid.ssid'] != '':
                        print(f"◉ TYPE → {d['kismet.device.base.type']}")
                        print(f"◉ MANUFACTURER → {d['kismet.device.base.manuf']}")
                        print(f"◉ MAC → {d['kismet.device.base.macaddr']}")
                        print('◉ PROBED SSIDs ')
                        print(f"    ∟ {p['dot11.probedssid.ssid']}")
                        print('-'*20)
