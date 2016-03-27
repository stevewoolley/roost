from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
toggles = Table('toggles', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('title', String(length=100), nullable=False),
    Column('refkey', String(length=50), nullable=False),
    Column('on_str', String(length=50), nullable=False),
    Column('off_str', String(length=50), nullable=False),
    Column('thing_id', Integer, nullable=False),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['toggles'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['toggles'].drop()
