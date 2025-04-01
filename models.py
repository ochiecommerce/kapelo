from datetime import datetime
import pathlib
import os
from peewee import (
    CharField,
    DateTimeField,
    IntegerField,
    Model,
    SqliteDatabase,
    AutoField,
    ForeignKeyField,
)

HOME = str(pathlib.Path.home())

db = SqliteDatabase(os.sep.join((HOME, "tbx-db.sqlite3")))


class BaseModel(Model):
    class Meta:
        database = db


class Submission(BaseModel):
    profile = CharField()
    submissions = IntegerField()
    time = DateTimeField(default=datetime.now)

class Archive(Submission):
    profile = CharField(unique=True)
# Profiles Table
class Profile(BaseModel):
    profile_id = AutoField()
    name = CharField(unique=True)


class ProblematicTask(BaseModel):
    task_id = CharField(unique=True)
    created_on = DateTimeField(default=datetime.now)

class ProblematicVideo(BaseModel):
    vid = CharField(unique=True)
    created_on = DateTimeField(default=datetime.now)


# Create tables
db.connect()
db.create_tables([Archive, Submission, ProblematicTask, ProblematicVideo])
