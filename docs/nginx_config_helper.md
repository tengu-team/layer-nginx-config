<h1 id="charms.layer.nginx_config_helper.NginxModule">NginxModule</h1>

```python
NginxModule(self, /, *args, **kwargs)
```
Enum of the valid NGINX modules.

Valid options are:
 * `NginxModule.HTTP`
 * `NginxModule.STREAM`

<h1 id="charms.layer.nginx_config_helper.NginxConfigError">NginxConfigError</h1>

```python
NginxConfigError(self, /, *args, **kwargs)
```
Exception to raise for errors in this module.

<h1 id="charms.layer.nginx_config_helper.NginxBase">NginxBase</h1>

```python
NginxBase(self)
```
NGINX base class.

**CAUTION** You can only use this class after
the 'nginx-config.installed' flag is set !

<h2 id="charms.layer.nginx_config_helper.NginxBase.backup_path">backup_path</h2>

Path to the backup directory.

<h2 id="charms.layer.nginx_config_helper.NginxBase.http_enabled_path">http_enabled_path</h2>

Path to the Http module include directory.

<h2 id="charms.layer.nginx_config_helper.NginxBase.juju_app_name">juju_app_name</h2>

Name of the juju application with unit number.

<h2 id="charms.layer.nginx_config_helper.NginxBase.streams_enabled_path">streams_enabled_path</h2>

Path to the Stream module include directory.

<h2 id="charms.layer.nginx_config_helper.NginxBase.validate_nginx">validate_nginx</h2>

```python
NginxBase.validate_nginx(self)
```
Validates the NGINX configuration.
Raises NginxConfigError when invalid.

__Raises__

`NginxConfigError`

<h2 id="charms.layer.nginx_config_helper.NginxBase.reload_nginx">reload_nginx</h2>

```python
NginxBase.reload_nginx(self)
```
Reloads NGINX configuration.
Raises NginxConfigError on error.

__Raises__

`NginxConfigError`

<h1 id="charms.layer.nginx_config_helper.NginxMainConfig">NginxMainConfig</h1>

```python
NginxMainConfig(self)
```
Represents the nginx.conf file.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.nginx_config">nginx_config</h2>

The nginx.conf file as a nginx.Conf object.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.config_as_dict">config_as_dict</h2>

```python
NginxMainConfig.config_as_dict(self)
```
Returns the NGINX main config file as a dict.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.config_as_object">config_as_object</h2>

```python
NginxMainConfig.config_as_object(self)
```
Returns the NGINX main config file as a nginx.Conf object.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.add_include">add_include</h2>

```python
NginxMainConfig.add_include(self, include, nginx_module)
```
Adds an include value to the module.

__Parameters__

- __`include` (str)__: Include string.
- __`nginx_module` (NginxModule)__: NGINX module.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.get_includes">get_includes</h2>

```python
NginxMainConfig.get_includes(self, nginx_module)
```
Return all includes values from a NGINX module.

__Parameters__

- __`nginx_module` (NginxModule)__: NGINX module.

__Returns__

``list``: A list containing all found include values.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.add_module">add_module</h2>

```python
NginxMainConfig.add_module(self, nginx_module)
```
Add a Http or Stream module to the NGINX config. If the module already
exists, do nothing.

__Parameters__

- __`nginx_module` (NginxModule)__: NGINX module.

__Raises__

`NginxConfigError`

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.load_module">load_module</h2>

```python
NginxMainConfig.load_module(self, nginx_cfg, nginx_module)
```
Return a module from the main NGINX config file.

__Parameters__

- __`nginx_cfg` (nginx.Conf)__: NGINX object
- __`nginx_module` (NginxModule)__: NGINX module.

__Returns__

`nginx.Http or nginx.Stream`

__Raises__

`NginxConfigError`

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.write_nginx_config">write_nginx_config</h2>

```python
NginxMainConfig.write_nginx_config(self)
```
Writes the _nginx_config object to the nginx.conf file.

<h2 id="charms.layer.nginx_config_helper.NginxMainConfig.backup_nginx_config">backup_nginx_config</h2>

```python
NginxMainConfig.backup_nginx_config(self, dst=None)
```
Creates a copy of the nginx.conf file to the destination.
Default to _backup_path if no destination is specified.

__Parameters__

- __`dst` (str or None)__: Destination path.

__Raises__

`NginxConfigError`

<h1 id="charms.layer.nginx_config_helper.NginxConfig">NginxConfig</h1>

```python
NginxConfig(self)
```
Class for modifying NGINX configs.

<h2 id="charms.layer.nginx_config_helper.NginxConfig.base_path">base_path</h2>

Path to the layer directory.

<h2 id="charms.layer.nginx_config_helper.NginxConfig.http_available_path">http_available_path</h2>

Path to the sites-available directory.

<h2 id="charms.layer.nginx_config_helper.NginxConfig.layer">layer</h2>

Name of the layer creating the class.

<h2 id="charms.layer.nginx_config_helper.NginxConfig.streams_available_path">streams_available_path</h2>

Path to the streams-available directory.

<h2 id="charms.layer.nginx_config_helper.NginxConfig.write_config">write_config</h2>

```python
NginxConfig.write_config(self, nginx_module, config, filename, subdir=None)
```
Writes the config to the nginx_module available dir.

__Parameters__

- __`nginx_module` (NginxModule)__: NGINX module.
- __`config` (str)__: NGINX config to be written.
- __`filename` (str)__: Name of the config file.
- __`subdir` (str or None)__: If specified, the value of subdir will be appended
    to the available_path variable. Use this if you want to
    write the config to a self made directory.

__Raises__

`NginxConfigError`

<h2 id="charms.layer.nginx_config_helper.NginxConfig.enable_all_config">enable_all_config</h2>

```python
NginxConfig.enable_all_config(self, nginx_module, subdir=None)
```
Creates symb links in the nginx_module enabled dir for all files
in the available directory.

__Parameters__

- __`nginx_module` (NginxModule)__: NGINX module.
- __`subdir` (str or None)__: If specified, the value of subdir will be appended
    to the available_path variable. Use this if you wrote configs
    to a seperate directory.

__Raises__

`NginxConfigError`

<h2 id="charms.layer.nginx_config_helper.NginxConfig.delete_all_config">delete_all_config</h2>

```python
NginxConfig.delete_all_config(self, nginx_module, subdir=None)
```
Delete all symb links and configs from the nginx_module.

__Parameters__

- __`nginx_module` (NginxModule)__: NGINX module.
- __`subdir` (str or None)__: If specified, the value of subdir will be appended
    to the available_path variable. Use this if you don't want to
    delete all configs in the available directory but instead
    a self made subdir.

__Raises__

`NginxConfigError`

