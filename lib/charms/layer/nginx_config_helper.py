import os
import inspect
from pathlib import Path
from shutil import copyfile
from subprocess import CalledProcessError, run

from charmhelpers.core.hookenv import log, status_set
from charmhelpers.core import unitdata

import nginx


class NginxConfigError(Exception):
    pass


# CAUTION ! You can only use this class after the 'nginx-config.installed' flag is set !
class NginxConfig(object):

    def __init__(self):
        kv = unitdata.kv()
        self._layer = _find_calling_layer()
        if not self.layer:
            raise NginxConfigError("Could not initialize NginxConfig, \
                                     no layer name found.")
        self._juju_app_name = kv.get('juju_app_name')        
        self.config_path = kv.get('nginx_config_path')
        self._juju_config_path = kv.get('nginx_juju_path')
        self._backup_path = kv.get('nginx_backups')
        self._streams_enabled_path = kv.get('nginx_streams_enabled')
        self._http_enabled_path = kv.get('nginx_http_enabled')       
        self._nginx_config = self.config_as_object()    
        self.ensure_unit_dir_exists()

    @property
    def layer(self):
        return self._layer

    @property
    def juju_app_name(self):
        return self._juju_app_name

    @property
    def http_available_path(self):
        path = os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer, 
                            "sites-available")
        return path

    @property
    def streams_available_path(self):
        path = os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer, 
                            "streams-available")
        return path

    @property
    def http_enabled_path(self):
        return self._http_enabled_path

    @property
    def streams_enabled_path(self):
        return self._streams_enabled_path

    @property
    def backup_path(self):
        return self._backup_path

    @property
    def nginx_config(self):
        return self._nginx_config

    def config_as_dict(self):
        """Returns the NGINX main config file as a dict.
        """
        return self._nginx_config.as_dict

    def config_as_object(self):
        """Returns the NGINX main config file as a nginx.Conf object.
        """
        return nginx.loadf(self.config_path)

    def get_includes(self, module='Http'):
        """Return all includes values from a module.

        Args:
            module (str): Should be one of the following options ['Http' || 'Stream'].   # TODO Enum?

        Returns:
            list: A list containing all found include values.
        """
        cfg = self._nginx_config
        m = self.load_module(cfg, module)       
        includes = []
        for m_cfg in m.as_dict:
            if 'include' in m_cfg:
                includes.append(m_cfg['include'])
        return includes

    def add_include(self, include, module='Http'):
        """Adds an include value to the module.

        Args:
            include (str): Include string.
            module (str): Should be one of the following options ['Http' || 'Stream'].
        """
        cfg = self._nginx_config
        m = self.load_module(cfg, module)
        # prevent duplicates
        includes = self.get_includes(module)
        if include not in includes:
            m.add(nginx.Key('include', include))
        return self

    def load_module(self, nginx_cfg, module='Http'):
        """Return a module from the main NGINX config file.

        Args:
            nginx_cfg (nginx.Conf): NGINX object
            module (str): Should be one of the following options ['Http' || 'Stream'].

        Returns:
            nginx.Http || nginx.Stream
        """
        try:
            m = nginx_cfg.filter(module)[0] # There should only be one Http / Stream block
            return m
        except IndexError:
            err_msg = 'Could not find module {} in nginx.conf'.format(module)
            raise NginxConfigError(err_msg)

    def validate_nginx(self):
        """Validates the NGINX configuration. 
        Raises NginxConfigError when invalid.
        """
        try:
            cmd = run(['nginx', '-t'])
            cmd.check_returncode()
        except CalledProcessError as e:
            err_msg = 'Invalid NGINX configuration.'
            log(e)
            status_set('blocked', err_msg)
            raise NginxConfigError(err_msg)
        return self

    def reload_nginx(self):
        """Reloads NGINX configuration.
        Raises NginxConfigError on error.
        """
        try:
            cmd = run(['nginx', '-s', 'reload'])
            cmd.check_returncode()
        except CalledProcessError as e:
            err_msg = 'Error reloading NGINX.'
            log(e)
            status_set('blocked', err_msg)
            raise NginxConfigError(err_msg)
        return self    

    def add_module(self, module): # Should module default to something?
        """Add a Http or Stream module to the NGINX config. If the module already
        exists, do nothing.

        Args:
            module (str): Should be one of the following options ['Http' || 'Stream'].
        """
        if module != "Http" and module != "Stream":
            raise NginxConfigError("Module should be either 'Http' or 'Stream'.")
        cfg = self._nginx_config
        try:
            self.load_module(cfg, module)
        except NginxConfigError: # Module does not exist yet
            if module == "Http":
                cfg.add(nginx.Http())
            else:
                cfg.add(nginx.Stream())
        return self


    def backup_nginx_config(self, dst=None):
        """Creates a copy of the nginx.conf file to the destination. 
        Default to _backup_path if no destination is specified.

        Args:
            dst (str): Destination path.
        """
        try:
            src = self.config_path
            if not dst:
                dst = "{}/nginx.conf.bak".format(self._backup_path)
            copyfile(src, dst)
        except IOError as e:
            err_msg = 'Error during nginx.conf backup.'
            log(e)
            status_set('blocked', err_msg)
            raise NginxConfigError(err_msg)
        return self

    def write_nginx_config(self):
        """Writes the _nginx_config object to the nginx.conf file.
        """
        nginx.dumpf(self._nginx_config, self.config_path)
        return self

    def write_http_config(self, http_config, file_name):  # Enum?
        """Writes the HTTP config to the sites-available dir.
        """
        path = os.path.join(self.http_available_path, file_name) 
        with open(path, "w") as f:
            f.write(http_config)
        return self

    def write_stream_config(self, stream_config, file_name):    # Enum?
        """Writes the stream config to the streams-available dir.
        """
        path = os.path.join(self.streams_available_path, file_name) 
        with open(path, "w") as f:
            f.write(stream_config)
        return self

    def enable_all_http(self):    # Enum?
        """Create symb links in sites-enabled to all files in sites-available.
        """
        for f in os.listdir(self.http_available_path):
            os.symlink(os.path.join(self.http_available_path, f),
                    os.path.join(self.http_enabled_path, f))
        return self

    def enable_all_stream(self):    # Enum?
        """Create symb links in sites-enabled to all files in sites-available.
        """
        for f in os.listdir(self.streams_available_path):
            os.symlink(os.path.join(self.streams_available_path, f),
                    os.path.join(self.streams_enabled_path, f))
        return self

    def delete_all_http(self):    # Enum?
        """Delete all symb links and configs from sites-available.
        """
        for f in os.listdir(self.http_available_path):
            if os.path.exists(os.path.join(self.http_enabled_path, f)):
                os.unlink(os.path.join(self.http_enabled_path, f))
            os.remove(os.path.join(self.http_available_path, f))
        return self
    
    def delete_all_streams(self):    # Enum?
        """Delete all symb links and configs from streams-available.
        """
        for f in os.listdir(self.streams_available_path):
            if os.path.exists(os.path.join(self.streams_enabled_path, f)):
                os.unlink(os.path.join(self.streams_enabled_path, f))
            os.remove(os.path.join(self.streams_available_path, f))
        return self

    def ensure_unit_dir_exists(self): # Find better name
        path = os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer)
        if not os.path.exists(path):
            os.makedirs(os.path.join(path, "sites-available"), exist_ok=True)
            os.makedirs(os.path.join(path, "streams-available"), exist_ok=True)
        

def _find_calling_layer(): # Class Method or not?
    for frame in inspect.stack():
        fn = Path(frame[1])
        if fn.parent.stem not in ('reactive', 'layer', 'charms'):
            continue
        layer_name = fn.stem
        if layer_name == 'nginx_config' or layer_name == 'nginx_config_helper':
            continue
        return layer_name
    return None


def what_layer_am_i(): # For Debugging purposes
        return _find_calling_layer()
