# 🛡️ KaliForge – Universal Kali Linux Tools Installer

**Author:** [boluwatife06-bit](https://github.com/boluwatife06-bit)

A powerful Python CLI tool that detects your Linux distribution, adds the
official Kali Linux repository when required, checks which penetration‑testing
tools are already installed, and automatically downloads & installs any
missing tools.

## 🚀 Features

- **17 tool categories** covering Information Gathering, Vulnerability
  Analysis, Web App, Password Attacks, Wireless, Exploitation, Forensics,
  Reverse Engineering, and more.
- **Multi‑distro**: Works on Debian/Ubuntu, Fedora, Arch, openSUSE.
- **Smart detection**: Uses `shutil.which` to check for installed tools.
- **Automatic installation**: Installs missing tools via `apt`, `dnf`,
  `pacman`, or `zypper`.
- **Bulk metapackage support**: Install `kali-tools-top10`,
  `kali-linux-everything`, etc.
- **Search & report**: Search for tools by keyword; export JSON reports.

## ⚙️ Installation

```bash
git clone https://github.com/boluwatife06-bit/KaliForge.git
cd KaliForge
# No external dependencies required (Python 3.8+)
python3 kali_forge.py
