"""Manage binaries requirements (like terraform blob and providers)."""
import os
import stat
import shutil
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
import requests

from .. import constants as const
from ..logs import logger
from ..utils import error


def search_on_github(repo, minor_version, patch_regex, patch, terraform=True):
    """Search release on github."""
    # Start search from the next incremented minor version
    # Note: the github UI serves the first page if the requested version does not exist
    release = 'v{}{}.0'.format(minor_version[:-1], int(minor_version[-1])+1)
    releases_count = 0
    while True:
        result = requests.get('{}?after={}'.format(const.GITHUB_RELEASES.format(repo), release))
        releases = re.findall(r'<a href=\"/{}/releases/tag/.*\">(.*)</a>'.format(repo), result.text)
        releases_count += len(releases)
        for release in releases:
            if re.match(r'^v{}\.{}$'.format(minor_version, patch if patch else patch_regex),
                        release):
                patch = patch or release.split('.')[-1]
                return patch
            # hard limit or it will takes too long time and terraform versions older
            # than 0.7 do not respect naming convention
            if terraform and any(const.LIMIT_TERRAFORM_VERSION in r for r in releases):
                return None
            if releases_count > const.LIMIT_GITHUB_RELEASES:
                return None
        if len(releases) < 1:
            # no more versions available
            break

        release = releases[-1:][0]
    return None

class Utils:
    """Utility for binary management"""
    def __init__(self, project):
        self.project = project

    @property
    def _tf_binary_cache(self):
        """Where tf binary versions are stored"""
        return Path(self.project.cfg.pyt.get('config.tf_binary_cache'))

    def tf_cached_version(self, version):
        """Cached file binary location"""
        return self._tf_binary_cache / 'versions' / version / 'terraform'

    def tf_download(self, version):
        """Download the wanted version"""
        if not self.tf_cached_version(version).is_file():
            os.makedirs(self.tf_cached_version(version).parent, exist_ok=True)

            # Download and extract in user's home if needed
            logger.warning("Version does not exist locally, downloading it")
            _, tmp_file = tempfile.mkstemp(prefix='terraform-', suffix='.zip')
            get = requests.get(
                f'https://releases.hashicorp.com/terraform/{version}/'
                f'terraform_{version}_{const.PLATFORM_SYSTEM}_{const.ARCH_NAME}.zip',
                stream=True)
            with open(tmp_file, 'wb') as _fd:
                for chunk in get.iter_content(chunk_size=128):
                    _fd.write(chunk)
            with zipfile.ZipFile(tmp_file, 'r') as zip_:
                zip_.extractall(path=self.tf_cached_version(version).parent)
            # Permissions not preserved on extract https://bugs.python.org/issue15795
            os.chmod(self.tf_cached_version(version),
                     stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            os.remove(tmp_file)

    def update_tf_symlink(self, version):
        """Create local link to cached one"""
        # Doing symlink
        if self.project.path.terraform().is_symlink():
            self.project.path.terraform().unlink()
        if not self.tf_cached_version(version).is_file():
            self.tf_download(version)
        self.project.path.terraform().symlink_to(self.tf_cached_version(version))
        logger.warning("Switch done, current terraform version is %s", version)

    def tf_align_version(self, version):
        """Align the tf binary to the one of the wanted version"""
        regex_version = r'(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)'
        match = re.match(regex_version, version)
        if not match:
            print(match)
            error('The terraform version seems not correct, '
                  'it should be a version number like "X.Y.Z"')
        # Getting current version
        try:
            pr_ = subprocess.run([self.project.path.terraform(), '-v'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            current_version = re.match(r'^Terraform v(.+)',
                                       pr_.stdout.decode('ascii')).group(1)
        except FileNotFoundError:
            current_version = 'not installed'

        if current_version == version:
            logger.debug("Terraform is already on version %s", version)
            return

        logger.warning("Current terraform version is %s, switching to version %s",
                       current_version, version)
        self.tf_download(version)
        self.update_tf_symlink(version)


def download_custom_provider(provider_name, provider_version, extension="zip"):
    """Download Terraform custom provider."""
    logger.info("Checking custom Terraform provider '%s' at version '%s'",
                provider_name, provider_version)
    github_base = 'https://github.com/'
    github_endpoint = f"{github_base}{provider_name}"
    supported_extensions = ["zip", "tar.gz", "tar.bz2"]

    if extension not in supported_extensions:
        error(f"Extension {extension} is not supported. "
              f"Only {', '.join(supported_extensions)} are.")

    req = requests.get(github_endpoint)
    if req.status_code != 200:
        error(f"The terraform provider {provider_name} does not exist ({github_endpoint})")

    match = re.match(r'^v?([0-9]+.[0-9]+).?([0-9]+)?(-[a-z]+)?$', provider_version)
    if not match:
        error('The provider version does not seem correct, it should be a version number like '
              '"X.Y", "X.Y.Z" or "X.Y.Z-custom"')
    minor_version, patch, custom = match.groups()

    patch = search_on_github(provider_name, minor_version, r'[0-9]+(-[a-z_-]+)?',
                             patch, terraform=False)

    if not patch:
        error(f"The provider version '{provider_name}-{provider_version}' does not exist")

    full_version = f"{minor_version}.{patch}"
    # Getting current version

    plugins_path = os.path.expanduser(
        f'~/.terraform.d/plugins/{const.PLATFORM_SYSTEM}_{const.ARCH_NAME}')
    os.makedirs(plugins_path, exist_ok=True)
    provider_short_name = provider_name.split('/', 1)[1]
    bin_name = f'{provider_short_name}_{full_version}'
    if provider_version.startswith('v'):
        # Do it now so we keep full_version clean for building url
        bin_name = '{n}_v{v}'.format(n=provider_short_name, v=full_version)
    else:
        bin_name = '{n}_{v}'.format(n=provider_short_name, v=full_version)
    tf_bin_path = os.path.join(plugins_path, f'{provider_short_name}_v{full_version}')

    if not os.path.isfile(tf_bin_path):
        # Download and extract in user's home if needed
        logger.warning("Provider version does not exist locally, downloading it")
        handle, tmp_file = tempfile.mkstemp(prefix='terraform-', suffix="." + extension)
        req = requests.get(
            f'https://github.com/{provider_name}/releases/download/v{full_version}/'
            f'{bin_name}_{const.PLATFORM_SYSTEM}_{const.ARCH_NAME}.{extension}',
            stream=True)
        with open(tmp_file, 'wb') as fd_:
            for chunk in req.iter_content(chunk_size=128):
                fd_.write(chunk)
        shutil.unpack_archive(tmp_file, plugins_path)
        # Permissions not preserved on extract https://bugs.python.org/issue15795
        os.chmod(tf_bin_path,
                 os.stat(tf_bin_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.remove(tmp_file)
        logger.info("Download done, current provider version is %s", full_version)
    else:
        logger.debug("Current provider version is already %s", full_version)
