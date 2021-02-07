from sqlalchemy import Table, Column, Integer, String, Date, Unicode, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

therapists_methods_table = Table('therapists_methods', Base.metadata,
                                 Column('therapist_id', Integer, ForeignKey('therapists.id')),
                                 Column('method_id', Integer, ForeignKey('methods.id')),
                                 )


class Therapist(Base):
    __tablename__ = 'therapists'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), nullable=False)
    photo_url = Column(String(300), nullable=True)
    methods = relationship("Method", secondary=therapists_methods_table)


class Method(Base):
    __tablename__ = 'methods'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), nullable=False)


class DataHistory(Base):
    __tablename__ = 'data_history'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    raw_data = Column(UnicodeText, nullable=False)
