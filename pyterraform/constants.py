"""Common project's constants"""
from pathlib import Path
import platform

# Pyterraform wrapper version
VERSION = '0.1.0'

def get_architecture():
    """Get system architecture name normalized for terraform."""
    platform_system = platform.machine()
    if 'arm' in platform_system:
        return 'arm'
    if platform_system in ('x86_64', 'darwin'):
        return 'amd64'
    return '386'

RC_OK = 0
RC_KO = 1
RC_UNK = 2

LIMIT_TERRAFORM_VERSION = 'v0.11.1'
LIMIT_GITHUB_RELEASES = 42
GITHUB_RELEASES = 'https://github.com/{}/releases'
ARCH_NAME = get_architecture()
PLATFORM_SYSTEM = platform.system().lower()

HOME_DIR = Path.home()
CONF_DIR = Path('pyterraform')

CWD = Path.cwd()
