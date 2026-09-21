import sys
from typing import List

from core.generator import MACGenerator
from core.validator import MACValidator
from platform.executor import WindowsAdapterController


def main() -> None:
    """Main orchestration function for the MAC spoofer CLI."""
    print("=" * 45)
    print("      WINDOWS PYTHON MAC SPOOFER")
    print("=" * 45)

    # Guard Clause: Script requires elevated administrator privileges
    if not WindowsAdapterController.is_admin():
        print("[-] ERROR: This application requires administrative privileges.")
        print("    Please run PowerShell or CMD as Administrator and try again.")
        sys.exit(1)

    # Retrieve all active network adapters
    adapters: List[str] = WindowsAdapterController.list_adapters()
    if not adapters:
        print("[-] ERROR: No active network adapters found on this system.")
        sys.exit(1)

    # Display available adapters to the user
    print("\nActive Network Adapters:")
    for idx, name in enumerate(adapters, 1):
        print(f"  [{idx}] {name}")

    # Prompt user selection
    choice: str = input("\nSelect adapter index to spoof: ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(adapters):
        print("[-] ERROR: Invalid selection.")
        sys.exit(1)

    target_adapter: str = adapters[int(choice) - 1]

    # Generate a locally administered unicast MAC address
    new_mac: str = MACGenerator.generate_random()

    # Guard Clause: Final safety validation before hardware configuration
    if not MACValidator.is_valid_spoof_mac(new_mac):
        print("[-] ERROR: Generated MAC failed validation checks. Aborting.")
        sys.exit(1)

    print(f"\n[+] Generated compliant MAC: {new_mac}")
    confirm: str = input(f"Apply this address to '{target_adapter}'? (y/n): ").strip().lower()

    if confirm != "y":
        print("[*] Operation canceled by user.")
        return

    # Execute registry alteration and adapter restart
    success: bool = WindowsAdapterController.set_mac_address(target_adapter, new_mac)
    if success:
        print("\n[+] MAC address spoofed successfully!")
        print("    Verify your new address using: Get-NetAdapter in PowerShell.")
    else:
        print("\n[-] Failed to configure MAC address.")


if __name__ == "__main__":
    main()