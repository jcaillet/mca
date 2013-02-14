from sqlalchemy import Column
from sqlalchemy.types import Integer
from sqlalchemy.ext.declarative import declarative_base

from meta import engine

''' Because the application database is updated dynamically, the use of SQLAlchemy requires the models to be loaded only when one want to compute an mca analysis. 
    Most data models are defined in centrality.py
'''

Base = declarative_base(bind=engine)

class Spatial_ref(Base):
    __tablename__ = 'spatial_ref_sys'
    __table_args__ = ({'schema': 'public', 'autoload': True})
    srid = Column('srid', Integer, primary_key=True)
