import ctypes
import subprocess
from typing import Final, List, Optional


class WindowsAdapterController:
    """Manages Layer 2 network adapter configurations on Windows platforms."""

    REG_PATH: Final[str] = (
        r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
    )

    @staticmethod
    def is_admin() -> bool:
        """Checks if the script is executing with elevated administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def run_powershell(command: str) -> str:
        """Executes a PowerShell command safely via a subprocess call."""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @classmethod
    def list_adapters(cls) -> List[str]:
        """Queries and returns names of all active (Up) physical network adapters."""
        cmd: str = "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -ExpandProperty Name"
        output: str = cls.run_powershell(cmd)
        if not output:
            return []
        return [line.strip() for line in output.splitlines() if line.strip()]

    @classmethod
    def find_adapter_sub_key(cls, adapter_name: str) -> Optional[str]:
        """Resolves the 4-digit registry subkey identifier (e.g. 0001) for a target adapter."""
        cmd: str = (
            f"$devId = (Get-NetAdapter -Name '{adapter_name}').DeviceID; "
            f"Get-ChildItem -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{{4d36e972-e325-11ce-bfc1-08002be10318}}\\????' -ErrorAction SilentlyContinue | "
            f"ForEach-Object {{ "
            f"if ((Get-ItemProperty -Path $_.PSPath -Name NetCfgInstanceId -ErrorAction SilentlyContinue).NetCfgInstanceId -eq $devId) "
            f"{{ $_.PSChildName }} "
            f"}}"
        )
        sub_key: str = cls.run_powershell(cmd)
        return sub_key if sub_key else None

    @classmethod
    def set_mac_address(cls, adapter_name: str, new_mac: str) -> bool:
        """Writes the new MAC address to the registry and restarts the network interface."""
        # Standardize MAC format for Windows registry (12 continuous uppercase characters)
        clean_mac: str = new_mac.replace(":", "").replace("-", "").upper()
        sub_key: Optional[str] = cls.find_adapter_sub_key(adapter_name)

        if not sub_key:
            print(f"[-] Registry subkey could not be identified for '{adapter_name}'.")
            return False

        full_reg_key: str = f"{cls.REG_PATH}\\{sub_key}"

        print(f"[*] Updating registry: {full_reg_key}")
        reg_cmd: str = (
            f'Set-ItemProperty -Path "Registry::{full_reg_key}" -Name "NetworkAddress" -Value "{clean_mac}"'
        )
        cls.run_powershell(reg_cmd)

        print(f"[*] Restarting network adapter '{adapter_name}' to apply changes...")
        restart_cmd: str = f"Restart-NetAdapter -Name '{adapter_name}'"
        cls.run_powershell(restart_cmd)
        return True