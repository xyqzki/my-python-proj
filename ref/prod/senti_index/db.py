import sqlalchemy
import os
from sshtunnel import SSHTunnelForwarder


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NewsDatabase(metaclass=Singleton):
    def __init__(self):
        self.tunnel = SSHTunnelForwarder(
            (os.environ['NEWSDB_SSH_HOST'], int(os.environ['NEWSDB_SSH_PORT'])),
            ssh_username=os.environ['NEWSDB_SSH_USER'],
            ssh_password=os.environ['NEWSDB_SSH_PWD'],
            remote_bind_address=(os.environ['NEWSDB_MYSQL_HOST'], int(os.environ['NEWSDB_MYSQL_PORT'])),
        )
        self.tunnel.start()
        uri = 'mysql+pymysql://{}:{}@127.0.0.1:{}/?charset=utf8mb4'.format(
            os.environ['NEWSDB_MYSQL_USER'],
            os.environ['NEWSDB_MYSQL_PWD'],
            self.tunnel.local_bind_port
        )
        self._engine = sqlalchemy.create_engine(uri)

    @property
    def engine(self):
        return self._engine

