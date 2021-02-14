"""
Example:

from datetime import timedelta
import db

g = db.Game.create(game_id=0, cluster=1, user1='100.100.100', user2='200.200.200', guess='PASS')
a1 = db.Answer.create(game=g, user='100.100.100', word='apple', e_time=timedelta(seconds=3000, microseconds=10))
a2 = db.Answer.create(game=g, user='200.200.200', word='river', e_time=timedelta(seconds=2000, microseconds=10))
for a in db.Answer.select().join(db.Game).where(db.Game.game_id == 0):
    print(a.user)
> 100.100.100
> 200.200.200

List all clusters:
for c in db.Cluster.select():
    print(c.cluster, c.words)
"""
from peewee import *

db = SqliteDatabase('concept.db')

class Game(Model):
    game_id = IntegerField()
    cluster = TextField()
    user1 = TextField()
    user2 = TextField()
    guess = TextField()

    class Meta:
        database = db


class Answer(Model):
    game = ForeignKeyField(Game, backref='answers')
    user = TextField()
    word = TextField()
    e_time = TimeField()  # Elapsed Time

    class Meta:
        database = db


class Cluster(Model):
    cluster = TextField()
    words = TextField()

    class Meta:
        database = db


db.connect()
