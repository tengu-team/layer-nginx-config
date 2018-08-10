import os
import inspect
from enum import Enum
from pathlib import Path
from shutil import copyfile
from subprocess import CalledProcessError, run

from charmhelpers.core.hookenv import log, status_set
from charmhelpers.core import unitdata

import nginx


class NginxConfigError(Exception):
    """Exception to raise for errors in this module.
    """
    pass


class NginxModule(Enum):
    """Enum of the valid NGINX modules.

    Valid options are:
     * `NginxModule.HTTP`
     * `NginxModule.STREAM`
    """
    # note: values should correspond to Class types in the python-nginx lib
    HTTP = 'Http'
    STREAM = 'Stream'


# CAUTION ! You can only use this class after 
# the 'nginx-config.installed' flag is set !
class NginxBase(object):
    """NGINX base class.

     **CAUTION** You can only use this class after 
     the 'nginx-config.installed' flag is set !
    """

    def __init__(self):
        kv = unitdata.kv()
        self.config_path = kv.get('nginx_config_path')
        self._juju_app_name = kv.get('juju_app_name')
        self._juju_config_path = kv.get('nginx_juju_path')
        self._backup_path = kv.get('nginx_backups')
        self._streams_enabled_path = kv.get('nginx_streams_enabled')
        self._http_enabled_path = kv.get('nginx_http_enabled')

    @property
    def juju_app_name(self):
        """Name of the juju application with unit number.
        """
        return self._juju_app_name

    @property
    def http_enabled_path(self):
        """Path to the Http module include directory.
        """
        return self._http_enabled_path

    @property
    def streams_enabled_path(self):
        """Path to the Stream module include directory.
        """
        return self._streams_enabled_path

    @property
    def backup_path(self):
        """Path to the backup directory.
        """
        return self._backup_path

    def validate_nginx(self):
        """Validates the NGINX configuration. 
        Raises NginxConfigError when invalid.

        # Raises
        `NginxConfigError`
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

        # Raises
        `NginxConfigError`
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


class NginxMainConfig(NginxBase):
    """Represents the nginx.conf file.
    """

    def __init__(self):
        NginxBase.__init__(self)
        self._nginx_config = self.config_as_object()

    @property
    def nginx_config(self):
        """The nginx.conf file as a nginx.Conf object.
        """
        return self._nginx_config     

    def config_as_dict(self):
        """Returns the NGINX main config file as a dict.
        """
        return self._nginx_config.as_dict

    def config_as_object(self):
        """Returns the NGINX main config file as a nginx.Conf object.
        """
        return nginx.loadf(self.config_path)

    def add_include(self, include, nginx_module):
        """Adds an include value to the module.

        # Parameters
        `include` (str): Include string.
        `nginx_module` (NginxModule): NGINX module.
        """
        cfg = self._nginx_config
        m = self.load_module(cfg, nginx_module)
        # prevent duplicates
        includes = self.get_includes(nginx_module)
        if include not in includes:
            m.add(nginx.Key('include', include))
        return self

    def get_includes(self, nginx_module):
        """Return all includes values from a NGINX module.

        # Parameters
        `nginx_module` (NginxModule): NGINX module.

        # Returns
        `list`: A list containing all found include values.
        """
        cfg = self._nginx_config
        m = self.load_module(cfg, nginx_module)  
        includes = []
        for m_cfg in m.as_dict:
            if 'include' in m_cfg:
                includes.append(m_cfg['include'])
        return includes    

    def add_module(self, nginx_module):
        """Add a Http or Stream module to the NGINX config. If the module already
        exists, do nothing.

        # Parameters
        `nginx_module` (NginxModule): NGINX module.

        # Raises
        `NginxConfigError`
        """
        if (nginx_module != NginxModule.HTTP 
                and nginx_module != NginxModule.STREAM):
            raise NginxConfigError("Module should be either 'Http' or 'Stream'.")
        cfg = self._nginx_config
        try:
            self.load_module(cfg, nginx_module)
        except NginxConfigError: # Module does not exist yet
            if nginx_module == NginxModule.HTTP:
                cfg.add(nginx.Http())
            else:
                cfg.add(nginx.Stream())
        return self

    def load_module(self, nginx_cfg, nginx_module):
        """Return a module from the main NGINX config file.

        # Parameters
        `nginx_cfg` (nginx.Conf): NGINX object
        `nginx_module` (NginxModule): NGINX module.

        # Returns
        `nginx.Http or nginx.Stream`

        # Raises
        `NginxConfigError`
        """
        try:
            # There should only be one Http / Stream block
            m = nginx_cfg.filter(nginx_module.value)[0] 
            return m
        except IndexError:
            err_msg = 'Could not find module {} in nginx.conf' \
                        .format(nginx_module.value)
            raise NginxConfigError(err_msg)    
    
    def write_nginx_config(self):
        """Writes the _nginx_config object to the nginx.conf file.
        """
        nginx.dumpf(self._nginx_config, self.config_path)
        return self

    def backup_nginx_config(self, dst=None):
        """Creates a copy of the nginx.conf file to the destination. 
        Default to _backup_path if no destination is specified.

        # Parameters
        `dst` (str or None): Destination path.

        # Raises
        `NginxConfigError`
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


class NginxConfig(NginxBase):
    """Class for modifying NGINX configs.
    """

    def __init__(self):
        """Initializes the NginxConfig class by creating the
        necessary directories.
        
        # Raises
        `NginxConfigError`
        """
        NginxBase.__init__(self)
        self._layer = _find_calling_layer()
        if not self.layer:
            raise NginxConfigError("Could not initialize NginxConfig, \
                                     no layer name found.")        
        self._ensure_unit_dir_exists()

    @property
    def layer(self):
        """Name of the layer creating the class.
        """
        return self._layer

    @property
    def base_path(self):
        """Path to the layer directory.
        """
        return os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer)

    @property
    def http_available_path(self):
        """Path to the sites-available directory.
        """
        path = os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer, 
                            "sites-available")
        return path

    @property
    def streams_available_path(self):
        """Path to the streams-available directory.
        """
        path = os.path.join(self._juju_config_path,
                            self._juju_app_name, 
                            self._layer, 
                            "streams-available")
        return path  

    def write_config(self, nginx_module, config, filename, subdir=None): # TODO catch filename collision
        """Writes the config to the nginx_module available dir.

        # Parameters
        `nginx_module` (NginxModule): NGINX module. 
        `config` (str): NGINX config to be written.
        `filename` (str): Name of the config file.
        `subdir` (str or None): If specified, the value of subdir will be appended
            to the available_path variable. Use this if you want to 
            write the config to a self made directory.

        # Raises
        `NginxConfigError`
        """
        available_path = self._available_path_nginx_module(nginx_module)

        if subdir:
            available_path += '/' + subdir.lstrip('/')

        config_path = os.path.join(available_path, filename)
        with open(config_path, 'w') as f:
            f.write(config)
        return self

    def enable_all_config(self, nginx_module, subdir=None):
        """Creates symb links in the nginx_module enabled dir for all files
        in the available directory.

        # Parameters
        `nginx_module` (NginxModule): NGINX module. 
        `subdir` (str or None): If specified, the value of subdir will be appended
            to the available_path variable. Use this if you wrote configs
            to a seperate directory.

        # Raises
        `NginxConfigError`
        """    
        available_path = self._available_path_nginx_module(nginx_module)
        enabled_path = self._enabled_path_nginx_module(nginx_module)

        if subdir:
            available_path += '/' + subdir.lstrip('/')

        for f in os.listdir(available_path):
            os.symlink(os.path.join(available_path, f),
                    os.path.join(enabled_path, f))
        return self

    def delete_all_config(self, nginx_module, subdir=None):
        """Delete all symb links and configs from the nginx_module.

        # Parameters
        `nginx_module` (NginxModule): NGINX module.
        `subdir` (str or None): If specified, the value of subdir will be appended
            to the available_path variable. Use this if you don't want to
            delete all configs in the available directory but instead 
            a self made subdir.

        # Raises
        `NginxConfigError`
        """
        available_path = self._available_path_nginx_module(nginx_module)
        enabled_path = self._enabled_path_nginx_module(nginx_module)  
        
        if subdir:
            available_path += '/' + subdir.lstrip('/')

        for f in os.listdir(available_path):
            if os.path.exists(os.path.join(enabled_path, f)):
                os.unlink(os.path.join(enabled_path, f))
            os.remove(os.path.join(available_path, f))
        return self

    def _ensure_unit_dir_exists(self):
        """Creates two paths for the calling layer, one for http 
        configs and the other for stream configs.

        # Raises
        `NginxConfigError`
        """
        path = os.path.join(self._juju_config_path,
                                self._juju_app_name, 
                                self._layer)
        try:            
            if not os.path.exists(path):
                os.makedirs(os.path.join(path, "sites-available"), exist_ok=True)
                os.makedirs(os.path.join(path, "streams-available"), exist_ok=True)
        except OSError as e:
            log(e)
            raise NginxConfigError("Could not create path ({})".format(path))
    
    def _available_path_nginx_module(self, nginx_module):
        """Returns the path to the available dir for the nginx_module.

        # Parameters
        `nginx_module` (NginxModule): NGINX module.

        # Raises
        `NginxConfigError`
        """
        if nginx_module == NginxModule.HTTP:
            return self.http_available_path
        elif nginx_module == NginxModule.STREAM:
            return self.streams_available_path
        else:
            raise NginxConfigError("Invalid NginxModule found.")
    
    def _enabled_path_nginx_module(self, nginx_module):
        """Returns the path to the enabled dir for the nginx_module.

        # Parameters
        `nginx_module` (NginxModule): NGINX module.

        # Raises
        `NginxConfigError`
        """
        if nginx_module == NginxModule.HTTP:
            return self.http_enabled_path
        elif nginx_module == NginxModule.STREAM:
            return self.streams_enabled_path
        else:
            raise NginxConfigError("Invalid NginxModule found.")
        

def _find_calling_layer():
    for frame in inspect.stack():
        fn = Path(frame[1])
        if fn.parent.stem not in ('reactive', 'layer', 'charms'):
            continue
        layer_name = fn.stem
        if layer_name == 'nginx_config' or layer_name == 'nginx_config_helper':
            continue
        return layer_name
    return None
