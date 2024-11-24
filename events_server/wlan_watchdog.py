import os, sys
import json
import time
import re
import requests
import subprocess
import threading as th

from loguru import logger

with open('../config.json') as f:
    config = json.load(f)

with open("network_devices.json") as f:
    devices = json.load(f)

log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
logger.remove()
logger.add("log.txt", level=2, format=log_format)
logger.add(sys.stdout, level=10, format=log_format)

devices_states: dict[str:list[int, int]] = {}
status_quantity = config['wlan_watchdog']['status_quantity']
status_threshold = config['wlan_watchdog']['status_threshold']
status_list = []
server_url = f'http://{config['events']['server_ip']}:{config['events']['port']}/add'


def parse_nmap_output(output):
    """
    Parse Nmap output to extract IP and MAC addresses.
    """
    ip_mac_dict = {}
    # Regular expression for IP addresses
    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    # Regular expression for MAC addresses
    mac_pattern = r"MAC Address: ([0-9A-Fa-f:]{17})"

    # Split output into lines and process
    lines = output.splitlines()
    current_ip = None
    for line in lines:
        # Check for IP address
        ip_match = re.search(ip_pattern, line)
        if ip_match:
            current_ip = ip_match.group(1)
        # Check for MAC address
        mac_match = re.search(mac_pattern, line)
        if mac_match and current_ip:
            mac_address = mac_match.group(1)
            ip_mac_dict.update({mac_address: {'ip': current_ip}})
            current_ip = None  # Reset for the next host

    return ip_mac_dict


def wlan_scan(ip):
    result = subprocess.run(["sudo", "nmap", "-sn", ip + '/24'], text=True, capture_output=True)
    devs = parse_nmap_output(result.stdout)
    for mac in devs.keys():
        if devices['device_matching'].get(mac):
            devices['device_matching'][mac].update(devs[mac])
        else:
            devices['device_matching'].update({mac: devs[mac]})
    with open("network_devices.json", "w") as f:
        json.dump(devices, f, indent=2)


def ping(ip):
    command = ['ping', '-c', '1', ip]
    try:
        return 1 - subprocess.call(command, stdout=subprocess.DEVNULL,timeout=1)
    except subprocess.TimeoutExpired:
        return 0


def arp_scan():
    command = ['sudo', 'arp-scan', '--localnet']
    result=subprocess.run(command,stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')



def wlan_scan_daemon():
    while True:
        wlan_scan(devices['gateway'])
        time.sleep(30)


def ping_daemon():
    while True:
        for mac in devices['tracked_devices']:
            if not devices['device_matching'].get(mac):
                logger.warning(f'we dont have ip for {mac} yet')
                continue
            current_state = ping(devices['device_matching'][mac]["ip"])
            if not devices_states.get(mac):
                devices_states.update({mac: [[current_state], current_state, time.time()]})
            states = devices_states[mac][0] + [current_state]

            #removing old state
            if len(states) > status_quantity:
                states.pop(0)
            #calculation of ratio and determination of state
            connected_ratio = sum(states) / len(states)
            if connected_ratio >= status_threshold:
                stable_state = 1
            elif connected_ratio <= 1 - status_threshold:
                stable_state = 0
            else:
                stable_state = devices_states[mac][1]

            if config['wlan_watchdog']['debug']:
                logger.debug(f'device {mac} is now {current_state} with {connected_ratio} ratio')

            if stable_state != devices_states[mac][1]:
                name = devices['device_matching'][mac].get("name") or devices['device_matching'][mac]["ip"]
                action = f'device_{'dis' if stable_state == 0 else ''}connected'
                try:
                    requests.request(method='POST', url=server_url,
                                     json={
                                         "target": name,
                                         "action": action,
                                         'time': time.time(),
                                         'expiration_time': 10 * 60
                                     })
                    logger.info(f'device {name} performs {action}')
                except:
                    logger.error(f'error during request about {devices['device_matching'][mac]}')

            devices_states.update({mac: [states, stable_state, time.time()]})

        time.sleep(config['wlan_watchdog']['interval'])



wlan_scan_daemon_thread = th.Thread(target=wlan_scan_daemon, daemon=True)
wlan_scan_daemon_thread.start()

try:
    ping_daemon()
except KeyboardInterrupt:
    logger.warning('Shutting down...')
# arp_scan_daemon()
