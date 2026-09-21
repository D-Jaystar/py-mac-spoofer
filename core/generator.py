import random
from typing import Final, List


class MACGenerator:
    """Utility class to generate IEEE 802 compliant spoofable MAC addresses."""

    # Valid second hex characters enforcing Locally Administered Unicast bits
    VALID_SECOND_NIBBLES: Final[List[str]] = ["2", "6", "A", "E"]

    @staticmethod
    def generate_random() -> str:
        """Generates a random, valid locally administered unicast MAC address."""
        # First byte: random hex char + compliant second nibble
        first_nibble: str = random.choice("0123456789ABCDEF")
        second_nibble: str = random.choice(MACGenerator.VALID_SECOND_NIBBLES)
        first_byte: str = f"{first_nibble}{second_nibble}"

        # Remaining 5 bytes (octets): completely random between 0x00 and 0xFF
        remaining_bytes: List[str] = [
            f"{random.randint(0, 255):02X}" for _ in range(5)
        ]

        # Combine into standard colon-separated format (e.g., 02:AB:CD:12:34:56)
        return ":".join([first_byte] + remaining_bytes)