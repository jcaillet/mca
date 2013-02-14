from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

user = 'postgres'
password = 'postgres'
host = '127.0.0.1'
database = 'mca'
geometryColumn = 'geom'

address = 'postgresql://%s:%s@%s:5432/%s'%(user, password, host, database)

engine = create_engine(address, encoding='utf8')

Session = scoped_session(sessionmaker())

metadata = MetaData()
