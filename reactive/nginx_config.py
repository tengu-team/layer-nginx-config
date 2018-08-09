import os
from charms.reactive import when, when_not, set_flag
from charmhelpers.core.hookenv import log, status_set
from charmhelpers.core import unitdata
from charms.layer.nginx_config_helper import NginxConfig, NginxConfigError

@when('nginx.available')
@when_not('nginx-config.installed')
def install_nginx_config():
    config_path = '/etc/nginx/nginx.conf'
    juju_config_path = '/etc/nginx/juju'
    if not os.path.exists(config_path):
        message = 'Could not find NGINX config file at {}'.format(config_path)
        log(message)
        status_set('blocked', message)
        return

    juju_app_name = os.environ['JUJU_UNIT_NAME'].replace('/', '-')
    # nginx_http_available = '{}/{}/sites-available' \
    #                            .format(juju_config_path, juju_app_name)
    # nginx_streams_available = '{}/{}/streams-available' \
    #                            .format(juju_config_path, juju_app_name)
    nginx_streams_enabled = '/etc/nginx/streams-enabled'
    nginx_http_enabled = '/etc/nginx/sites-enabled'
    nginx_backups = '{}/backups'.format(juju_config_path)

    os.makedirs(nginx_backups, exist_ok=True)
    os.makedirs(nginx_streams_enabled, exist_ok=True)
    # os.makedirs(nginx_http_available, exist_ok=True)
    # os.makedirs(nginx_streams_available, exist_ok=True)

    unitdata.kv().set('juju_app_name', juju_app_name)
    #unitdata.kv().set('nginx_http_available', nginx_http_available)
    unitdata.kv().set('nginx_http_enabled', nginx_http_enabled)
    #unitdata.kv().set('nginx_streams_available', nginx_streams_available)
    unitdata.kv().set('nginx_streams_enabled', nginx_streams_enabled)
    unitdata.kv().set('nginx_backups', nginx_backups)
    unitdata.kv().set('nginx_config_path', config_path)
    unitdata.kv().set('nginx_juju_path', juju_config_path)

    # Ensure http / stream module exists and includes the right dirs
    try:
        nginxcfg = NginxConfig()
        nginxcfg \
            .add_module('Http') \
            .add_module('Stream') \
            .add_include('/etc/nginx/sites-enabled/*', 'Http') \
            .add_include('{}/*'.format(nginx_streams_enabled), 'Stream') \
            .write_nginx_config() \
            .validate_nginx() \
            .reload_nginx()
    except NginxConfigError as e:
        log(e) # TODO better error handling, juju status
        return
    
    set_flag('nginx-config.installed')
