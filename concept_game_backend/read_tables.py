import argh
from concept_game_backend import db


def read_games():
    """Return all Games with Answers"""
    games = []
    for g in db.Game.select():
        answers = [(a.cluster_id, a.user, a.word, a.e_time) for a in g.answers.select()]
        games.append({'game': g, 'answers': answers})
    return games


def print_games():
    games = read_games()
    for gm in games:
        g = gm['game']
        answers = gm['answers']
        print(g.game_id, g.start_time, g.cluster_id, g.user1, g.user2, g.guess, answers)


def read_clusters():
    """Read all clusters"""
    clusters = {}
    for c in db.Cluster.select():
        clusters[c.cluster] = c.words
    return clusters


def print_clusters():
    clusters = read_clusters()
    for cid, words in clusters.items():
        print(cid, words)


if __name__ == '__main__':
    argh.dispatch_commands([print_games, print_clusters])