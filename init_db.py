import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Base

os.makedirs('instance', exist_ok=True)
engine = create_engine('sqlite:///instance/secure_login.db')
Base.metadata.create_all(bind=engine)
print('Database initialized at instance/secure_login.db')
