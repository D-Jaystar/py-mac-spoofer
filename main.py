import ctypes
import os
import random
import re
import subprocess
import sys
from typing import Final, List, Optional, Pattern

MAC_PATTERN: Final[Pattern[str]] = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
)


class MACValidator:
    @staticmethod
    def is_valid_format(mac: str) -> bool:
        if not mac or not isinstance(mac, str):
            return False
        return bool(MAC_PATTERN.match(mac.strip()))

    @staticmethod
    def is_valid_spoof_mac(mac: str) -> bool:
        if not MACValidator.is_valid_format(mac):
            return False
        first_byte: int = int(mac.replace("-", ":").split(":")[0], 16)
        # Unicast (b0 = 0) and Locally Administered (b1 = 1)
        return (first_byte & 0b00000001) == 0 and (first_byte & 0b00000010) != 0


class MACGenerator:
    @staticmethod
    def generate_random() -> str:
        # Second hex character must be 2, 6, A, or E for locally administered unicast
        valid_second_nibbles: List[str] = ["2", "6", "A", "E"]
        first_byte: str = (
            f"{random.choice('0123456789ABCDEF')}{random.choice(valid_second_nibbles)}"
        )
        remaining_bytes: List[str] = [
            f"{random.randint(0, 255):02X}" for _ in range(5)
        ]
        return ":".join([first_byte] + remaining_bytes)


class WindowsAdapterController:
    REG_PATH: Final[str] = (
        r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
    )

    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def run_powershell(command: str) -> str:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @classmethod
    def list_adapters(cls) -> List[str]:
        cmd = "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -ExpandProperty Name"
        output = cls.run_powershell(cmd)
        if not output:
            return []
        return [line.strip() for line in output.splitlines() if line.strip()]

    @classmethod
    def find_adapter_sub_key(cls, adapter_name: str) -> Optional[str]:
        # Zoek het juiste 000X subsleutel-nummer van de adapter
        cmd = f"(Get-NetAdapter -Name '{adapter_name}').DeviceID"
        device_id = cls.run_powershell(cmd)
        if not device_id:
            return None

        # Format device ID to 4-digit key (e.g. 0001)
        try:
            key_index = int(device_id)
            return f"{key_index:04d}"
        except ValueError:
            return None

    @classmethod
    def set_mac_address(cls, adapter_name: str, new_mac: str) -> bool:
        clean_mac = new_mac.replace(":", "").replace("-", "").upper()
        sub_key = cls.find_adapter_sub_key(adapter_name)

        if not sub_key:
            print(f"[-] Kan registerindex voor {adapter_name} niet vinden.")
            return False

        full_reg_key = f"{cls.REG_PATH}\\{sub_key}"

        print(f"[*] Register bijwerken: {full_reg_key} -> NetworkAddress = {clean_mac}")
        reg_cmd = f'Set-ItemProperty -Path "Registry::{full_reg_key}" -Name "NetworkAddress" -Value "{clean_mac}"'
        cls.run_powershell(reg_cmd)

        print(f"[*] Adapter '{adapter_name}' herstarten om nieuw MAC-adres te activeren...")
        restart_cmd = f"Restart-NetAdapter -Name '{adapter_name}'"
        cls.run_powershell(restart_cmd)
        return True


def main() -> None:
    print("=" * 45)
    print("      WINDOWS PYTHON MAC SPOOFER")
    print("=" * 45)

    # Guard Clause: Admin check
    if not WindowsAdapterController.is_admin():
        print("[-] FOUT: Dit script moet als Administrator worden uitgevoerd!")
        print("    Open PowerShell / CMD als Administrator en voer het opnieuw uit.")
        sys.exit(1)

    adapters = WindowsAdapterController.list_adapters()
    if not adapters:
        print("[-] Geen actieve netwerkadapters gevonden.")
        sys.exit(1)

    print("\nActieve adapters:")
    for idx, name in enumerate(adapters, 1):
        print(f"  [{idx}] {name}")

    keuze = input("\nKies een adapter nummer: ").strip()
    if not keuze.isdigit() or int(keuze) < 1 or int(keuze) > len(adapters):
        print("[-] Ongeldige keuze.")
        sys.exit(1)

    gekozen_adapter = adapters[int(keuze) - 1]

    # Genereren en valideren
    nieuw_mac = MACGenerator.generate_random()
    while not MACValidator.is_valid_spoof_mac(nieuw_mac):
        nieuw_mac = MACGenerator.generate_random()

    print(f"\n[+] Gegenereerd MAC-adres: {nieuw_mac}")
    bevestiging = input(f"Wil je '{gekozen_adapter}' wijzigen naar dit adres? (y/n): ").strip().lower()

    if bevestiging == "y":
        succes = WindowsAdapterController.set_mac_address(gekozen_adapter, nieuw_mac)
        if succes:
            print("\n[+] Succesvol voltooid! Controleer met: Get-NetAdapter")
    else:
        print("[*] Actie geannuleerd.")


if __name__ == "__main__":
    main()