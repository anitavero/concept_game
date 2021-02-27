from concept_game_backend import db


def read_games():
    """Return all Games with Answers"""
    games = []
    for g in db.Game.select():
        answers = [(a.cluster_id, a.user, a.word, a.e_time) for a in g.answers.select()]
        print(g.game_id, g.start_time, g.cluster_id, g.user1, g.user2, g.guess, answers)
        games.append({'game': g, 'answers': answers})
    return games


def read_clusters():
    """Read all clusters"""
    clusters = {}
    for c in db.Cluster.select():
        print(c.cluster, c.words)
        clusters[c.cluster] = c.words
    return clusters
