"""Manage aws sessions"""
import os
import time
import pickle
import sys

import boto3
import botocore

from . import constants as const
from .logs import logger

# pylint: disable=fixme

class Session:
    """AWS session caching and setting"""

    def __init__(self, project):
        self._credentials = None
        self.project = project

    @property
    def profile(self):
        """Return the profile to be used, looking up to:
        - cli
        - state.yml
        - environment"""
        if self.project.cfg.cli_args.get("profile"):
            return self.project.cfg.cli_args['profile']
        if self.project.cfg.state.get('profile'):
            return self.project.cfg.state['profile']
        return os.environ['AWS_PROFILE']

    @property
    def session_cache_file(self):
        """Temporary store credential"""
        return self.project.path.run / f'session_cache_{self.profile}.pickle'
        #return self.project.path.run / f'session_cache_{self.account}_{self.profile}.pickle'

    def _get_session(self):
        """Get or create boto cached session."""
        if self.session_cache_file.is_file() and \
                time.time() - os.stat(self.session_cache_file).st_mtime < 2700:
            with open(self.session_cache_file, 'rb') as _f:
                session_cache = pickle.load(_f)
            session = boto3.Session(aws_access_key_id=session_cache['credentials'].access_key,
                                    aws_secret_access_key=session_cache['credentials'].secret_key,
                                    aws_session_token=session_cache['credentials'].token,
                                    region_name=session_cache['region'])
        else:
            session_args = {"profile_name": self.profile}
            if 'region' in self.project.cfg.state:
                session_args['region_name'] = self.project.cfg.state['region']
            # TODO: add assume role
            try:
                session = boto3.Session(**session_args)
            except botocore.exceptions.ProfileNotFound:
                logger.error("Profile not found.")
                logger.error("No valid AWS session found. Exiting...")
                sys.exit(const.RC_KO)
            try:
                session_cache = {'credentials': session.get_credentials().get_frozen_credentials(),
                                 'region': session.region_name}
            except botocore.exceptions.ParamValidationError:
                logger.error('Error validating authentication. Maybe the wrong MFA code ?')
                sys.exit(const.RC_KO)
            except Exception:  # pylint: disable=broad-except
                logger.exception('Unknown error')
                sys.exit(const.RC_UNK)
            #with os.fdopen(os.open(self.session_cache_file, os.O_WRONLY | os.O_CREAT,
            #                       mode=0o600), 'wb') as _f:
            os.makedirs(self.project.path.run, exist_ok=True)
            with open(self.session_cache_file, 'wb') as _f:
                pickle.dump(session_cache, _f, pickle.HIGHEST_PROTOCOL)
        return session

    @property
    def credentials(self):
        """Retun AWS credentials"""
        if not self._credentials:
            self._credentials = self._get_session().get_credentials().get_frozen_credentials()
        return self._credentials

    @property
    def access_key(self):
        """AWS_ACCESS_KEY_ID"""
        return self.credentials.access_key
    @property
    def secret_key(self):
        """AWS_SECRET_ACCESS_KEY"""
        return self.credentials.secret_key
    @property
    def token(self):
        """AWS_SESSION_TOKEN"""
        return self.credentials.token

    def infect_environment(self):
        """Infect current environment with access attributes"""
        os.environ['AWS_ACCESS_KEY_ID'] = self.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret_key
        if self.token:
            os.environ['AWS_SESSION_TOKEN'] = self.token
