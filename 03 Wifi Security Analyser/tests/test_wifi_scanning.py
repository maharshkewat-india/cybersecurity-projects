"""Hardware-independent parser tests for Windows netsh WLAN discovery."""
import unittest

from modules.wifi_scanning import (mark_connected_networks, normalize_security,
                                   parse_interface_output, parse_netsh_output,
                                   vendor_from_bssid)


class NetshParserTests(unittest.TestCase):
    def test_multiple_ssids_and_bssids(self) -> None:
        text = """SSID 1 : Home Network
 Authentication : WPA2-Personal
 Encryption : CCMP
 BSSID 1 : 3c:84:6a:91:04:11
 Signal : 76%
 Channel : 6
 BSSID 2 : 3C-84-6A-91-04-12
 Signal : 70 %
 Channel : 11
SSID 2 : Public WiFi
 Authentication : Open
 BSSID 1 : a4:5e:60:22:19:02
 Signal : 64%
 Channel : 1
"""
        rows = parse_netsh_output(text)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["ssid"], "Home Network")
        self.assertEqual(rows[1]["bssid"], "3c:84:6a:91:04:12")
        self.assertEqual(rows[2]["security_type"], "Open")
        self.assertEqual(rows[0]["vendor"], "TP-Link")

    def test_hidden_missing_fields_and_malformed_lines(self) -> None:
        text = """SSID 1 :
 Authentication : WEP
 BSSID 1 : 00:14:22:71:90:33
 Signal : unknown
 nonsense without separator
SSID 2 : NoBssid
 Authentication : WPA3-Personal
"""
        rows = parse_netsh_output(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["ssid"], "Hidden network")
        self.assertIsNone(rows[0]["signal_strength"])
        self.assertIsNone(rows[0]["channel"])
        self.assertEqual(rows[0]["security_type"], "WEP")
        self.assertEqual(rows[1]["bssid"], "Unknown")

    def test_localized_labels_and_security_variants(self) -> None:
        text = """SSID 1 : Oficina
 Authentification : WPA2/WPA3-Personal
 Chiffrement : CCMP
 BSSID 1 : f4:f5:d8:02:77:10
 Signal : 85 %
 Canal : 44
"""
        row = parse_netsh_output(text)[0]
        self.assertEqual(row["signal_strength"], 85)
        self.assertEqual(row["channel"], 44)
        self.assertEqual(row["security_type"], "WPA2/WPA3")
        self.assertEqual(row["vendor"], "Aruba")

    def test_empty_and_security_normalization(self) -> None:
        self.assertEqual(parse_netsh_output(""), [])
        self.assertEqual(normalize_security("WPA3-Enterprise", "CCMP"), "WPA3-Enterprise")
        self.assertEqual(normalize_security("Open", "None"), "Open")
        self.assertEqual(vendor_from_bssid("7a:2e:71:9c:c5:d3"), "Unknown")

    def test_connected_interface_is_matched_without_dropping_available_networks(self) -> None:
        networks = [
            {"ssid": "Home", "bssid": "aa:bb:cc:00:00:01"},
            {"ssid": "Cafe", "bssid": "aa:bb:cc:00:00:02"},
        ]
        mark_connected_networks(networks, "Home", "AA:BB:CC:00:00:01")
        self.assertEqual([row["connected"] for row in networks], [True, False])
        self.assertEqual(len(networks), 2)

    def test_interface_parser_only_reports_connected_ssid(self) -> None:
        output = """Name : Wi-Fi
Description : Example Wireless Adapter
State : connected
SSID : Home Network
BSSID : 3c:84:6a:91:04:11
"""
        self.assertEqual(parse_interface_output(output), (
            "Example Wireless Adapter", "Home Network", "3c:84:6a:91:04:11"))
        self.assertEqual(parse_interface_output("State : disconnected\nSSID : Old Network"),
                         ("Unknown", "", ""))

    def test_connected_network_is_retained_when_missing_from_nearby_results(self) -> None:
        networks = [{"ssid": "Cafe", "bssid": "aa:bb:cc:00:00:02"}]
        mark_connected_networks(networks, "Hidden Home", "aa:bb:cc:00:00:01")
        self.assertEqual(len(networks), 2)
        self.assertEqual(networks[0]["connected"], False)
        self.assertEqual(networks[1]["ssid"], "Hidden Home")
        self.assertEqual(networks[1]["connected"], True)


if __name__ == "__main__":
    unittest.main()
