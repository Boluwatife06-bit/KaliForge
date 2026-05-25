#!/usr/bin/env python3
"""
KALIFORGE - Universal Kali Linux Tools Installer
Author: boluwatife06-bit (GitHub)
Description: Detects your Linux distribution, adds the Kali repository if
             required, checks which Kali tools are already installed, and
             automatically downloads and installs any missing tools.
Disclaimer: FOR EDUCATIONAL USE ONLY. Always obtain proper authorisation
            before testing any system.
License: MIT
"""

import sys
import os
import shutil
import subprocess
import platform
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── ANSI Color Helpers ──────────────────────────────────────────────
class Color:
    """Terminal ANSI escape sequences."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_RED  = "\033[41m"

def cprint(text: str, color: str = "", bold: bool = False) -> None:
    """Print coloured text to the terminal."""
    prefix = Color.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Color.RESET}")

def banner() -> None:
    """Display the KaliForge ASCII banner with author credit."""
    art = f"""
{Color.CYAN}{Color.BOLD}
 ██╗  ██╗ █████╗ ██╗     ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
 ██║ ██╔╝██╔══██╗██║     ██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
 █████╔╝ ███████║██║     ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
 ██╔═██╗ ██╔══██║██║     ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
 ██║  ██╗██║  ██║███████╗██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
 ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{Color.ENDC}
{Color.BOLD}>>> KaliForge – Universal Kali Linux Tools Installer <<<{Color.RESET}
{Color.YELLOW}Author: boluwatife06-bit (GitHub){Color.RESET}
{Color.RED}⚠ Educational Use Only! ⚠{Color.RESET}
"""
    print(art)

# ── OS & Package Manager Detection ──────────────────────────────────
def detect_os() -> Dict[str, str]:
    """
    Detect the Linux distribution and return a dictionary with
    'name', 'version', 'id', and 'id_like' fields.
    """
    info: Dict[str, str] = {}
    # Try the freedesktop.org standard first
    os_release = Path("/etc/os-release")
    if os_release.exists():
        with open(os_release, "r") as fh:
            for line in fh:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    value = value.strip('"').strip("'")
                    info[key.lower()] = value
    # Fallback for older distros
    if not info:
        try:
            info["id"] = platform.freedesktop_os_release().get("ID", "unknown")
        except Exception:
            info["id"] = platform.system().lower()
    return info

def detect_package_manager() -> Dict[str, str]:
    """
    Return a dict with 'name', 'install_cmd', 'update_cmd', and 'list_installed'
    for the system's native package manager.
    """
    managers = {
        "apt": {
            "name": "apt",
            "install_cmd": "sudo apt install -y {packages}",
            "update_cmd": "sudo apt update",
            "list_installed": "dpkg-query -W -f='${Package}\\n'",
        },
        "dnf": {
            "name": "dnf",
            "install_cmd": "sudo dnf install -y {packages}",
            "update_cmd": "sudo dnf check-update",
            "list_installed": "rpm -qa --qf '%{NAME}\\n'",
        },
        "pacman": {
            "name": "pacman",
            "install_cmd": "sudo pacman -S --noconfirm {packages}",
            "update_cmd": "sudo pacman -Sy",
            "list_installed": "pacman -Qq",
        },
        "zypper": {
            "name": "zypper",
            "install_cmd": "sudo zypper install -y {packages}",
            "update_cmd": "sudo zypper refresh",
            "list_installed": "rpm -qa --qf '%{NAME}\\n'",
        },
    }
    # Check which binary is available
    for binary, cfg in managers.items():
        if shutil.which(binary):
            return cfg
    # Ultimate fallback
    return managers["apt"]

# ── Kali Repository Management (Debian/Ubuntu) ─────────────────────
KALI_REPO_FILE = "/etc/apt/sources.list.d/kali.list"
KALI_KEY_FILE  = "/usr/share/keyrings/kali-archive-keyring.gpg"
KALI_REPO_LINE = "deb https://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware"
KALI_KEY_URL   = "https://archive.kali.org/archive-keyring.gpg"

def kali_repo_added() -> bool:
    """Check if the Kali repository has already been added."""
    if not Path(KALI_REPO_FILE).exists():
        return False
    with open(KALI_REPO_FILE, "r") as fh:
        content = fh.read()
    return "kali-rolling" in content

def add_kali_repository() -> bool:
    """
    Add the official Kali Linux repository and GPG signing key.
    Returns True on success, False on failure.
    """
    cprint("[*] Adding Kali Linux repository...", Color.CYAN)
    try:
        # Download signing key
        subprocess.run(
            ["sudo", "wget", "-q", KALI_KEY_URL, "-O", KALI_KEY_FILE],
            check=True, stdout=subprocess.DEVNULL
        )
        # Add repository line
        subprocess.run(
            f'echo "{KALI_REPO_LINE}" | sudo tee {KALI_REPO_FILE} > /dev/null',
            shell=True, check=True
        )
        # Update package lists
        subprocess.run(["sudo", "apt", "update"], check=True)
        cprint("[✓] Kali repository added successfully.", Color.GREEN)
        return True
    except subprocess.CalledProcessError as err:
        cprint(f"[✗] Failed to add Kali repository: {err}", Color.RED)
        return False

def remove_kali_repository() -> None:
    """Remove the Kali repository and its signing key."""
    if Path(KALI_REPO_FILE).exists():
        subprocess.run(["sudo", "rm", "-f", KALI_REPO_FILE], check=False)
    if Path(KALI_KEY_FILE).exists():
        subprocess.run(["sudo", "rm", "-f", KALI_KEY_FILE], check=False)
    subprocess.run(["sudo", "apt", "update"], check=False)
    cprint("[✓] Kali repository removed.", Color.GREEN)

# ── Tool Database (Organised by Kali Metapackage) ──────────────────
KALI_TOOLS: Dict[str, Dict[str, List[str]]] = {
    "Information Gathering": {
        "metapackage": "kali-tools-information-gathering",
        "tools": [
            "nmap", "masscan", "zenmap", "dmitry", "dnsenum", "dnsrecon",
            "fierce", "theharvester", "maltego", "recon-ng", "spiderfoot",
            "whois", "whatweb", "amass", "sherlock", "metagoofil",
            "theHarvester", "gobuster", "dirb", "dirbuster", "wfuzz",
            "skipfish", "nikto", "uniscan", "sn0int", "osrframework",
            "intrigue-core", "gasmask", "urlcrazy", "netdiscover",
        ]
    },
    "Vulnerability Analysis": {
        "metapackage": "kali-tools-vulnerability",
        "tools": [
            "nikto", "lynis", "wpscan", "joomscan", "sqlmap", "sqlninja",
            "openvas", "golismero", "unix-privesc-check", "nmap", "nessus",
            "legion", "sparta", "armitage", "bed", "jsql-injection",
            "sidguesser", "oscanner", "tnscmd10g", "cisco-auditing-tool",
            "cisco-global-exploiter", "cisco-ocs", "cisco-torch",
            "copy-router-config", "merge-router-config", "metasploit-framework",
        ]
    },
    "Web Application Analysis": {
        "metapackage": "kali-tools-web",
        "tools": [
            "burpsuite", "zaproxy", "sqlmap", "sqlninja", "wpscan",
            "joomscan", "dirb", "dirbuster", "gobuster", "wfuzz",
            "nikto", "skipfish", "whatweb", "owasp-mantra", "vega",
            "webscarab", "commix", "xsrfprobe", "sslyze", "sslscan",
            "testssl.sh", "ffuf", "feroxbuster", "paros", "skipfish",
            "uniscan", "webscarab", "httrack", "owasp-zsc",
        ]
    },
    "Database Assessment": {
        "metapackage": "kali-tools-database",
        "tools": [
            "sqlmap", "sqlninja", "jsql-injection", "bbqsql", "hexorbase",
            "mdb-tools", "oscanner", "sidguesser", "tnscmd10g",
            "bbqsql", "inguma", "sqlsus", "safe3si",
        ]
    },
    "Password Attacks": {
        "metapackage": "kali-tools-passwords",
        "tools": [
            "hydra", "john", "hashcat", "medusa", "ncrack", "cewl",
            "crunch", "wordlists", "hash-identifier", "ophcrack",
            "ophcrack-cli", "rainbowcrack", "rcracki-mt", "rsmangler",
            "truecrack", "fcrackzip", "pdfcrack", "samdump2",
            "chntpw", "ophcrack", "crunch", "johnny", "kwprocessor",
        ]
    },
    "Wireless Attacks": {
        "metapackage": "kali-tools-wireless",
        "tools": [
            "aircrack-ng", "airgeddon", "kismet", "wifite", "reaver",
            "bully", "cowpatty", "pyrit", "asleap", "airdecloak-ng",
            "mdk3", "mdk4", "pixiewps", "fern-wifi-cracker",
            "wifi-honey", "eapmd5pass", "genkeys", "genpmk",
            "kalibrate-rtl", "freeradius-wpe", "hostapd-wpe",
        ]
    },
    "Reverse Engineering": {
        "metapackage": "kali-tools-reverse-engineering",
        "tools": [
            "radare2", "ghidra", "apktool", "dex2jar", "jadx-gui",
            "jd-gui", "ollydbg", "edb-debugger", "valgrind", "ltrace",
            "strace", "binutils", "nasm", "yasm", "clang", "gdb",
            "metasploit-framework", "msfvenom", "nasm-shell",
        ]
    },
    "Exploitation Tools": {
        "metapackage": "kali-tools-exploitation",
        "tools": [
            "metasploit-framework", "armitage", "beef-xss", "exploitdb",
            "searchsploit", "set", "setoolkit", "shellnoob", "sqlmap",
            "termineter", "websploit", "yersinia", "routersploit",
            "commix", "jboss-autopwn", "linux-exploit-suggester",
            "windows-exploit-suggester", "evil-winrm", "crackmapexec",
            "impacket-scripts", "powershell-empire", "starkiller",
        ]
    },
    "Sniffing & Spoofing": {
        "metapackage": "kali-tools-sniffing-spoofing",
        "tools": [
            "wireshark", "tcpdump", "ettercap-graphical", "ettercap-text-only",
            "dsniff", "arpspoof", "dnschef", "mitmproxy", "burpsuite",
            "responder", "ntlmrelayx", "evilgrade", "hamster-sidejack",
            "ferret-sidejack", "hexinject", "netsniff-ng", "sslsniff",
            "sslsplit", "tcpreplay", "ettercap", "bettercap", "net-creds",
        ]
    },
    "Post Exploitation": {
        "metapackage": "kali-tools-post-exploitation",
        "tools": [
            "powershell-empire", "starkiller", "crackmapexec", "evil-winrm",
            "impacket-scripts", "mimikatz", "proxychains4", "proxytunnel",
            "weevely", "webacoo", "laudanum", "nishang", "powersploit",
            "exe2hex", "shellter", "veil", "unicorn", "powershell", "psexec",
        ]
    },
    "Forensics": {
        "metapackage": "kali-tools-forensics",
        "tools": [
            "autopsy", "foremost", "scalpel", "bulk-extractor", "guymager",
            "ddrescue", "dcfldd", "safecopy", "binwalk", "magicrescue",
            "recoverjpeg", "testdisk", "photorec", "volatility3",
            "volatility", "extundelete", "sleuthkit", "galleta", "rifiuti2",
            "pasco", "regripper", "chkrootkit", "rkhunter",
        ]
    },
    "Reporting Tools": {
        "metapackage": "kali-tools-reporting",
        "tools": [
            "dradis-ce", "faraday", "pipal", "casefile", "keepnote",
            "cherrytree", "cutycapt", "recordmydesktop", "maltego",
            "metagoofil", "eyewitness", "faraday-client",
        ]
    },
    "Social Engineering": {
        "metapackage": "kali-tools-social-engineering",
        "tools": [
            "set", "setoolkit", "beef-xss", "backdoor-factory",
            "ghost-phisher", "maltego", "msfpc", "se-toolkit",
        ]
    },
    "VoIP Tools": {
        "metapackage": "kali-tools-voip",
        "tools": [
            "siparmyknife", "sipcrack", "sipdump", "sipflanker",
            "sippts", "sipsak", "sipvicious", "smap", "svcrack",
            "svcrash", "svmap", "svreport", "svwar", "voiphopper",
        ]
    },
    "RFID / SDR Tools": {
        "metapackage": "kali-tools-rfid",
        "tools": [
            "gnuradio", "gqrx-sdr", "hackrf", "rtl-sdr", "kalibrate-rtl",
            "chirp", "proxmark3", "rfidiot", "mfcuk", "mfoc",
        ]
    },
    "Bluetooth Tools": {
        "metapackage": "kali-tools-bluetooth",
        "tools": [
            "bluelog", "blueranger", "bluesnarfer", "bluez",
            "bluez-hcidump", "btscanner", "crackle", "redfang",
            "spooftooph", "ubertooth", "blue-hydra",
        ]
    },
    "Cryptography & Steganography": {
        "metapackage": "kali-tools-crypto-stego",
        "tools": [
            "steghide", "stegosuite", "stegsnow", "outguess",
            "jsteg", "mp3stego", "openstego", "cloakify",
            "aesfix", "aeskeyfind", "ccrypt", "certtool",
            "gnupg", "john", "hashcat", "ophcrack",
        ]
    },
    "Hardware Hacking": {
        "metapackage": "kali-tools-hardware",
        "tools": [
            "arduino", "binwalk", "flashrom", "openocd",
            "minicom", "picocom", "avrdude", "smbus-tools",
            "i2c-tools", "spi-tools", "python3-smbus",
        ]
    },
    "Fuzzing Tools": {
        "metapackage": "kali-tools-fuzzing",
        "tools": [
            "afl", "aflplusplus", "honggfuzz", "libfuzzer",
            "radamsa", "zzuf", "sfuzz", "spike", "boofuzz",
            "peach", "sulley", "american-fuzzy-lop",
        ]
    },
}

# Additional meta‑metapackages
KALI_META_META = {
    "Kali Top 10": "kali-tools-top10",
    "Kali Default": "kali-linux-default",
    "Kali Large": "kali-linux-large",
    "Kali Everything": "kali-linux-everything",
}

# ── Tool Installation Checker ──────────────────────────────────────
def is_tool_installed(tool: str) -> bool:
    """
    Check if a given tool is installed by searching for its
    executable in the system PATH using shutil.which.
    """
    return shutil.which(tool) is not None

def get_installed_packages(pm: Dict[str, str]) -> set:
    """Retrieve a set of all installed package names."""
    try:
        result = subprocess.run(
            pm["list_installed"], shell=True, capture_output=True,
            text=True, timeout=30
        )
        return set(line.strip() for line in result.stdout.splitlines() if line.strip())
    except Exception:
        return set()

# ── Package Installation ───────────────────────────────────────────
def run_command(cmd: str, realtime: bool = True) -> int:
    """
    Execute a shell command, optionally printing stdout in real time.
    Returns the return code.
    """
    if realtime:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            print(line, end="")
        process.wait()
        return process.returncode
    else:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            cprint(f"  [✗] Error: {result.stderr.strip()}", Color.RED)
        return result.returncode

def install_packages(packages: List[str], pm: Dict[str, str]) -> Tuple[int, int]:
    """
    Install a list of packages using the detected package manager.
    Returns (success_count, fail_count).
    """
    if not packages:
        return 0, 0

    # Non‑interactive frontend for Debian‑based systems
    env_prefix = ""
    if pm["name"] == "apt":
        env_prefix = "DEBIAN_FRONTEND=noninteractive "

    cmd = pm["install_cmd"].format(packages=" ".join(packages))
    full_cmd = f"{env_prefix}{cmd}"
    cprint(f"  [→] Installing {len(packages)} package(s)...", Color.YELLOW)
    ret = run_command(full_cmd, realtime=True)
    if ret == 0:
        cprint(f"  [✓] Successfully installed {len(packages)} package(s).", Color.GREEN)
        return len(packages), 0
    else:
        cprint(f"  [✗] Installation failed for some packages.", Color.RED)
        return 0, len(packages)

# ── Interactive Menu System ────────────────────────────────────────
def show_categories() -> None:
    """Display all tool categories with their indices."""
    cprint("\n── Kali Linux Tool Categories ──", Color.CYAN, bold=True)
    for idx, cat in enumerate(KALI_TOOLS.keys(), 1):
        tool_count = len(KALI_TOOLS[cat]["tools"])
        print(f"  {Color.GREEN}{idx:>2}{Color.RESET}. {cat:<35} ({tool_count} tools)")
    # Add meta‑metapackages
    offset = len(KALI_TOOLS)
    for idx, (name, _) in enumerate(KALI_META_META.items(), offset + 1):
        print(f"  {Color.YELLOW}{idx:>2}{Color.RESET}. {name} (full metapackage)")

def check_category(category_name: str) -> Tuple[List[str], List[str]]:
    """
    Check which tools in a category are installed vs missing.
    Returns (installed, missing).
    """
    if category_name in KALI_META_META:
        # For meta‑metapackages we just print info
        cprint(f"\n[*] {category_name} is a meta‑metapackage: {KALI_META_META[category_name]}", Color.CYAN)
        return [], []

    tools = KALI_TOOLS[category_name]["tools"]
    installed = []
    missing = []
    cprint(f"\n── Checking {category_name} ({len(tools)} tools) ──", Color.CYAN)
    for tool in tools:
        if is_tool_installed(tool):
            installed.append(tool)
            print(f"  {Color.GREEN}[✓]{Color.RESET} {tool}")
        else:
            missing.append(tool)
            print(f"  {Color.RED}[✗]{Color.RESET} {tool}")
    cprint(f"\n  Installed: {len(installed)} | Missing: {len(missing)}", Color.BOLD)
    return installed, missing

def install_metapackage(meta_name: str, pm: Dict[str, str]) -> None:
    """Install an entire Kali metapackage."""
    if meta_name not in KALI_META_META:
        cprint(f"[✗] Unknown metapackage: {meta_name}", Color.RED)
        return
    pkg = KALI_META_META[meta_name]
    cprint(f"\n[*] Installing metapackage: {pkg}", Color.CYAN)
    cprint(f"[!] WARNING: This may require 10-35 GB of disk space!", Color.YELLOW)
    confirm = input(f"{Color.BOLD}Proceed? (y/N): {Color.RESET}").strip().lower()
    if confirm == "y":
        run_command(pm["install_cmd"].format(packages=pkg), realtime=True)
    else:
        cprint("[*] Installation cancelled.", Color.YELLOW)

def install_category(category_name: str, pm: Dict[str, str]) -> None:
    """Install all missing tools from a given category."""
    if category_name in KALI_META_META:
        install_metapackage(category_name, pm)
        return

    installed, missing = check_category(category_name)
    if not missing:
        cprint("[✓] All tools already installed!", Color.GREEN)
        return

    cprint(f"\n[*] {len(missing)} tool(s) missing.", Color.YELLOW)
    if len(missing) > 10:
        choice = input(f"{Color.BOLD}Install all {len(missing)} missing tools? (y/N): {Color.RESET}").strip().lower()
        if choice == "y":
            install_packages(missing, pm)
        else:
            cprint("[*] Skipped.", Color.YELLOW)
    else:
        cprint("[*] Installing missing tools...", Color.CYAN)
        install_packages(missing, pm)

def install_all(pm: Dict[str, str]) -> None:
    """Scan every category and install all missing tools."""
    total_installed = 0
    total_missing = 0
    all_missing = []

    cprint("\n[*] Scanning all categories...", Color.CYAN)
    for cat in KALI_TOOLS:
        _, missing = check_category(cat)
        total_missing += len(missing)
        total_installed += len(KALI_TOOLS[cat]["tools"]) - len(missing)
        all_missing.extend(missing)

    cprint(f"\n── Summary ──", Color.BOLD)
    cprint(f"  Total tools: {total_installed + total_missing}", Color.WHITE)
    cprint(f"  Already installed: {total_installed}", Color.GREEN)
    cprint(f"  Missing: {total_missing}", Color.RED)

    if all_missing:
        cprint(f"\n[!] This will install {len(all_missing)} packages.", Color.YELLOW)
        cprint("[!] WARNING: This could use significant disk space!", Color.YELLOW)
        confirm = input(f"{Color.BOLD}Proceed with full installation? (y/N): {Color.RESET}").strip().lower()
        if confirm == "y":
            # Install in batches of 20 to avoid overwhelming the package manager
            for i in range(0, len(all_missing), 20):
                batch = all_missing[i:i+20]
                install_packages(batch, pm)
            cprint("[✓] All installations completed!", Color.GREEN)
        else:
            cprint("[*] Full installation cancelled.", Color.YELLOW)

def search_tools(query: str) -> None:
    """Search for tools by keyword across all categories."""
    cprint(f"\n[*] Searching for '{query}'...", Color.CYAN)
    found = []
    for cat, data in KALI_TOOLS.items():
        for tool in data["tools"]:
            if query.lower() in tool.lower():
                installed = "✓" if is_tool_installed(tool) else "✗"
                found.append((cat, tool, installed))
    if found:
        cprint(f"\nFound {len(found)} match(es):", Color.GREEN)
        for cat, tool, status in found:
            color = Color.GREEN if status == "✓" else Color.RED
            print(f"  {color}[{status}]{Color.RESET} {tool:<25} ({cat})")
    else:
        cprint("[✗] No tools found matching your query.", Color.RED)

def export_report() -> None:
    """Export installed/missing tool status to JSON and log files."""
    report = {}
    for cat, data in KALI_TOOLS.items():
        installed = [t for t in data["tools"] if is_tool_installed(t)]
        missing  = [t for t in data["tools"] if not is_tool_installed(t)]
        report[cat] = {"installed": installed, "missing": missing}

    with open("kaliforge_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    cprint("[✓] Report saved to kaliforge_report.json", Color.GREEN)

    # Also write a simple installed.log
    all_installed = []
    all_missing = []
    for cat, data in KALI_TOOLS.items():
        all_installed.extend([t for t in data["tools"] if is_tool_installed(t)])
        all_missing.extend([t for t in data["tools"] if not is_tool_installed(t)])

    with open("installed.log", "w") as fh:
        fh.write("\n".join(sorted(set(all_installed))))
    with open("skipped.log", "w") as fh:
        fh.write("\n".join(sorted(set(all_missing))))
    cprint("[✓] Logs saved to installed.log and skipped.log", Color.GREEN)

# ── Main Menu ──────────────────────────────────────────────────────
def main_menu() -> None:
    """Display the main interactive menu and handle user input."""
    pm = detect_package_manager()
    os_info = detect_os()

    cprint(f"  OS: {os_info.get('name', os_info.get('id', 'Unknown'))}", Color.BLUE)
    cprint(f"  Package Manager: {pm['name']}", Color.BLUE)

    # On Debian‑based systems, offer to add Kali repos
    if pm["name"] == "apt" and not kali_repo_added():
        cprint("\n[!] Kali repository not detected on this Debian‑based system.", Color.YELLOW)
        choice = input(f"{Color.BOLD}Add Kali repository? (y/N): {Color.RESET}").strip().lower()
        if choice == "y":
            add_kali_repository()

    while True:
        cprint("\n" + "═" * 60, Color.CYAN)
        cprint("  KALIFORGE MAIN MENU", Color.BOLD)
        cprint("═" * 60, Color.CYAN)
        print(f"  {Color.GREEN}1{Color.RESET}. List all tool categories")
        print(f"  {Color.GREEN}2{Color.RESET}. Check & install a category")
        print(f"  {Color.GREEN}3{Color.RESET}. Install ALL missing tools")
        print(f"  {Color.GREEN}4{Color.RESET}. Install a Kali metapackage")
        print(f"  {Color.GREEN}5{Color.RESET}. Search for a tool")
        print(f"  {Color.GREEN}6{Color.RESET}. Export report to JSON")
        print(f"  {Color.GREEN}7{Color.RESET}. Add Kali repository (Debian/Ubuntu)")
        print(f"  {Color.GREEN}8{Color.RESET}. Remove Kali repository")
        print(f"  {Color.GREEN}9{Color.RESET}. Exit")
        print("─" * 60)

        choice = input(f"{Color.BOLD}>> {Color.RESET}").strip()

        if choice == "1":
            show_categories()
        elif choice == "2":
            show_categories()
            try:
                idx = int(input(f"\n{Color.BOLD}Enter category number: {Color.RESET}"))
                cats = list(KALI_TOOLS.keys())
                if 1 <= idx <= len(cats):
                    install_category(cats[idx - 1], pm)
                elif idx > len(cats):
                    # User chose a meta‑metapackage
                    meta_names = list(KALI_META_META.keys())
                    meta_idx = idx - len(cats) - 1
                    if 0 <= meta_idx < len(meta_names):
                        install_metapackage(meta_names[meta_idx], pm)
                    else:
                        cprint("[✗] Invalid category number.", Color.RED)
                else:
                    cprint("[✗] Invalid category number.", Color.RED)
            except ValueError:
                cprint("[✗] Please enter a valid number.", Color.RED)
        elif choice == "3":
            install_all(pm)
        elif choice == "4":
            cprint("\n── Available Metapackages ──", Color.CYAN)
            for idx, (name, pkg) in enumerate(KALI_META_META.items(), 1):
                print(f"  {Color.GREEN}{idx}{Color.RESET}. {name} ({pkg})")
            try:
                idx = int(input(f"\n{Color.BOLD}Choose metapackage: {Color.RESET}"))
                meta_names = list(KALI_META_META.keys())
                if 1 <= idx <= len(meta_names):
                    install_metapackage(meta_names[idx - 1], pm)
                else:
                    cprint("[✗] Invalid choice.", Color.RED)
            except ValueError:
                cprint("[✗] Please enter a valid number.", Color.RED)
        elif choice == "5":
            query = input(f"{Color.BOLD}Enter search keyword: {Color.RESET}").strip()
            if query:
                search_tools(query)
        elif choice == "6":
            export_report()
        elif choice == "7":
            if pm["name"] == "apt":
                add_kali_repository()
            else:
                cprint("[✗] Repository management only supported on Debian/Ubuntu.", Color.RED)
        elif choice == "8":
            if pm["name"] == "apt":
                remove_kali_repository()
            else:
                cprint("[✗] Repository management only supported on Debian/Ubuntu.", Color.RED)
        elif choice == "9":
            cprint("\n[✓] Goodbye! Stay ethical. 🛡️", Color.GREEN)
            sys.exit(0)
        else:
            cprint("[✗] Invalid option, try again.", Color.RED)

# ── Entry Point ────────────────────────────────────────────────────
if __name__ == "__main__":
    # Check for root privileges (recommended but not mandatory)
    if os.geteuid() != 0:
        cprint("[!] Warning: Running without root privileges. Some installations may fail.", Color.YELLOW)
        cprint("[!] Consider running with: sudo python3 kali_forge.py", Color.YELLOW)

    banner()
    try:
        main_menu()
    except KeyboardInterrupt:
        cprint("\n\n[!] Interrupted. Exiting.", Color.YELLOW)
        sys.exit(0)
