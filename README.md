# (WIP) Layer NGINX-Config

This layer provides a lib for higher layers to access NGINX and setup configurations for the HTTP and Stream modules.

For more information see the [documentation](docs/nginx_config_helper.md).

# Writing NGINX HTTP / Stream config
## How it works

The layer will create per juju application and per juju layer within the charm a separate directory where NGINX configuration will be written. The generated dirs will only be created for layers which actually create the NginxConfig object.
Each layer-directory has two default subdirectories `sites-available` and `streams-available` where respectively the HTTP and stream config is written to. If needed you can create your own directorys within these.

```bash
/etc/nginx/
    ├── juju/
    │   ├── backups/
    │   └── nginx-0/         # Juju unit 
    │       └── nginx_tcp/   # Calling layer
    │           ├── sites-available/
    │           └── streams-available/
    │               └── amq-tcp
    ├── nginx.conf
    ├── sites-available/
    │   └── default
    ├── sites-enabled/
    ├── streams-enabled/
    │   └── amq-tcp -> /etc/nginx/juju/nginx-0/nginx_tcp/streams-available/amq-tcp
    ├── ...
```

## Examples
**Writing some config with the default directories**
```python
from charms.layer.nginx_config_helper import (
    NginxConfig, 
    NginxConfigError, 
    NginxModule,
)

@when('nginx-config.installed',
      'endpoint.tcp.update')
def tcp_update():
    # Generate the tcp config
    tcp_config = ...
    tcp_filename = ...
    # Create a NginxConfig instance

    try:
        nginxCfg = NginxConfig()
        
                # Remove symb links and delete old stream configs
        nginxCfg.delete_all_config(NginxModule.STREAM) \ 
                # Write the new config to the streams-available dir
                .write_config(NginxModule.STREAM, tcp_config, tcp_filename) \ 
                # Create symb links to streams-enabled
                .enable_all_config(NginxModule.STREAM) \ 
                # Run a NGINX validation check
                .validate_nginx() \ 
                # Reload the NGINX config for all workers
                .reload_nginx() 
    except NginxConfigError as e:
        status_set('blocked', e)
        log(e)
        return
    clear_flag('endpoint.tcp.update')
```

**Using custom directories**

In some cases it can be helpful if you could split the NGINX configuration in more than one directory. For example if we have a charm that is setting up tcp and udp proxies from multiple interfaces, we might want seperate directories for tcp and udp. Our `streams-available` dir would look like this:
```
/etc/nginx/
    ├── juju/
    │   └── nginx-0/     
    │       └── nginx_tcp/
    │           └── streams-available/
    |               ├── tcp/
    |               |   └── amq-tcp
    │               └── udp/
```
In this case we need to do the following steps:
- Manually create the desired directory structure.
- use `delete_all_config()` with the optional `subdir` argument pointing to the `tcp` or `udp` directory.
- use `write_config()` with the optional `subdir` argument pointing to the `tcp` or `udp` directory.
- use `enable_all_config()` with the optional `subdir` argument pointing to the `tcp` or `udp` directory.

You can access the generated dirs via the following NginxConfig attributes (example with dir structure above):
- `NginxConfig.base_path`: Path to the layer directory. Ex. `/etc/nginx/juju/nginx-0/nginx_tcp`
- `NginxConfig.http_available_path`: Path to the sites-available directory. Ex `/etc/nginx/juju/nginx-0/nginx_tcp/sites-available`
- `NginxConfig.streams_available_path`: Path to the sites-available directory. Ex `/etc/nginx/juju/nginx-0/nginx_tcp/streams-available`


# Reading / modifying the nginx.conf file

You can access and modify the nginx.conf file via the `NginxMainConfig` class. You can use this class to add modules (only stream and http are currently supported) and add include key-values to these modules. Checking the config file is easy via the `NginxMainConfig.config_as_dict()` method. If you are only interested in checking the includes use `NginxMainConfig.get_includes(NginxModule)`.