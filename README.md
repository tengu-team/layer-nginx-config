# (WIP) Layer NGINX-Config

This layer provides a lib for higher layers to access NGINX and setup configurations for the HTTP and Stream modules.

# Writing NGINX HTTP / Stream config
## How it works

The layer will create per juju application and per juju layer within the charm a separate directory where NGINX configuration will be written. The generated dirs will only be created for layers which actually create the NginxConfig object.
Each directory has two sub-directories `sites-available` and `streams-available` where respectively the HTTP and stream config is written. If needed you can create your own directorys within these.

```bash
/etc/nginx
    ├── juju
    │   ├── backups
    │   └── nginx-0
    │       └── nginx_tcp
    │           ├── sites-available
    │           └── streams-available
    │               └── amq-tcp
    ├── nginx.conf
    ├── sites-available
    │   └── default
    ├── sites-enabled
    ├── streams-enabled
    │   └── amq-tcp -> /etc/nginx/juju/nginx-10/nginx_tcp/streams-available/amq-tcp
    ├── ...
```

## Examples

TODO

# Reading / modifying the nginx.conf file

TODO