from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData

         
#The declarative_base combines a metadata container and a mapper that maps our class to a
# database table.

# Explicit metadata specification
metadata = MetaData()
Base = declarative_base(metadata=metadata)