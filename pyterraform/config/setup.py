"""Configuration object storage for pyterraform and stacks"""

# pylint: disable=too-few-public-methods,missing-function-docstring
class Setups:
    """Generic setup placeholder"""

    def __init__(self, datasource):
        self._data = dict()
        self.src = datasource

    def _get(self, path, default=None):
        data = self._data
        try:
            for item in path.split('.'):
                data = data[item]
            return data
        except KeyError:
            return default
    def _set(self, path, value):
        data = self._data
        for key in path.split('.')[:-1]:
            data = data.setdefault(key, dict())
        data[path.split('.')[-1]] = value


#STACK_FOLDER_STRUCTURE = ['stack', 'environment']
class Pyterraform(Setups):
    """Set up of pyterraform wrapper"""
    @property
    def plugin_cache_dir(self):
        """Where to cache tf plugins"""
        if not self._get('plugin_cache_dir'):
            self._set('plugin_cache_dir',
                      self.src.args.get('plugin_cache_dir') or \
                      self.src.environment.get('TF_plugin_cache_dir') or \
                      self.src.ftf.get('plugin_cache_dir'))
        return self._get('plugin_cache_dir')
    @property
    def confdir(self):
        """Where to cache tf plugins"""
        if not self._get('confdir'):
            self._set('confdir', self.src.args.get('confdir'))
        return self._get('confdir')


class Stack(Setups):
    """Setting of a single stack"""

    @property
    def stack(self):
        if not self._get('stack.name'):
            self._set('stack.name',
                      self.src.args.get('stack') or \
                      self.src.path.get('stack'))
        return self._get('stack.name')
    @property
    def environment(self):
        if not self._get('stack.env'):
            self._set('stack.env', self.src.args.get("environment") or \
                                   self.src.path['environment'])
        return self._get('stack.env')
    @property
    def tf_vars(self):
        if not self._get('stack.vars'):
            self._set('stack.vars', self.src.fstack.get("terraforms", dict()).get('vars', dict()))
        return self._get('stack.vars')
