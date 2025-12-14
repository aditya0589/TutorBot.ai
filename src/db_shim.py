import pymysql
from flask import current_app, g
import ssl

class MySQL:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('MYSQL_HOST', 'localhost')
        app.config.setdefault('MYSQL_USER', None)
        app.config.setdefault('MYSQL_PASSWORD', None)
        app.config.setdefault('MYSQL_DB', None)
        app.config.setdefault('MYSQL_PORT', 3306)
        app.config.setdefault('MYSQL_UNIX_SOCKET', None)
        app.config.setdefault('MYSQL_CONNECT_TIMEOUT', 10)
        app.config.setdefault('MYSQL_READ_DEFAULT_FILE', None)
        app.config.setdefault('MYSQL_USE_UNICODE', True)
        app.config.setdefault('MYSQL_CHARSET', 'utf8')
        app.config.setdefault('MYSQL_SQL_MODE', None)
        app.config.setdefault('MYSQL_CURSORCLASS', None)
        app.config.setdefault('MYSQL_SSL_CA', None)
        app.config.setdefault('MYSQL_SSL_DISABLED', False)

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)

    def connect(self):
        kwargs = {}
        if current_app.config['MYSQL_HOST']:
            kwargs['host'] = current_app.config['MYSQL_HOST']
        if current_app.config['MYSQL_USER']:
            kwargs['user'] = current_app.config['MYSQL_USER']
        if current_app.config['MYSQL_PASSWORD']:
            kwargs['password'] = current_app.config['MYSQL_PASSWORD']
        if current_app.config['MYSQL_DB']:
            kwargs['db'] = current_app.config['MYSQL_DB']
        if current_app.config['MYSQL_PORT']:
            kwargs['port'] = int(current_app.config['MYSQL_PORT'])
        if current_app.config['MYSQL_UNIX_SOCKET']:
            kwargs['unix_socket'] = current_app.config['MYSQL_UNIX_SOCKET']
        if current_app.config['MYSQL_CONNECT_TIMEOUT']:
            kwargs['connect_timeout'] = current_app.config['MYSQL_CONNECT_TIMEOUT']
        if current_app.config['MYSQL_READ_DEFAULT_FILE']:
            kwargs['read_default_file'] = current_app.config['MYSQL_READ_DEFAULT_FILE']
        if current_app.config['MYSQL_USE_UNICODE']:
            kwargs['use_unicode'] = current_app.config['MYSQL_USE_UNICODE']
        if current_app.config['MYSQL_CHARSET']:
            kwargs['charset'] = current_app.config['MYSQL_CHARSET']
        if current_app.config['MYSQL_SQL_MODE']:
            kwargs['sql_mode'] = current_app.config['MYSQL_SQL_MODE']
        if current_app.config['MYSQL_CURSORCLASS']:
            kwargs['cursorclass'] = current_app.config['MYSQL_CURSORCLASS']
        
        # SSL Configuration
        if not current_app.config.get('MYSQL_SSL_DISABLED'):
            ssl_config = {}
            if current_app.config.get('MYSQL_SSL_CA'):
                ssl_config['ca'] = current_app.config['MYSQL_SSL_CA']
            
            # TiDB requires SSL. If no CA is provided (common in local dev), we still need to enable SSL.
            # We enable it with check_hostname=False to avoid verification issues if system CAs aren't perfect.
            host = current_app.config.get('MYSQL_HOST') or ''
            if 'tidbcloud' in host and not ssl_config:
                ssl_config['check_hostname'] = False

            # If we have any SSL config, pass it
            if ssl_config:
                kwargs['ssl'] = ssl_config
        
        return pymysql.connect(**kwargs)

    @property
    def connection(self):
        if 'mysql_db' not in g:
            g.mysql_db = self.connect()
        return g.mysql_db

    def teardown(self, exception):
        db = g.pop('mysql_db', None)
        if db is not None:
            db.close()
