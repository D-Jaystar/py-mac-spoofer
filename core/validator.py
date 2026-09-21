from typing import Final, Pattern
import re


class MACValidator:
    """Utility class for validating MAC addresses"""

    MAC_PATTERN: Final[Pattern[str]] = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

    @staticmethod
    def is_valid_format(mac_address: str) -> bool:
        """checks syntax if there are 6 Hexedecimal bytes """
        #Guard Clause for handeling
        if not mac_address or not isinstance(mac_address, str):
            return False

        clean_mac: str = mac_address.strip()
        return bool(MACValidator.MAC_PATTERN.match(clean_mac))

    @staticmethod
    def is_valid_spoof_mac(mac_address: str) -> bool:
        """Validates if the MAC address is safe for spoofing (Unicast & Locally Administered)."""
        #guardclause for syntax
        if not MACValidator.is_valid_format(mac_address):
            return False

        # Extract first byte and pase hex to int
        first_byte_hex: str = mac_address.replace("-", ":").split(":")[0]
        first_byte: int = int(first_byte_hex, 16)

        # Bitwise check
        is_unicast: bool = (first_byte & 0b00000001) == 0

        # Bitwise check: b1 must be 1 (Locally Administered)
        is_local: bool = (first_byte & 0b00000010) != 0

        return is_unicast and is_local