import argh
from argh import arg
from concept_game_backend import db


def read_games():
    """Return all Games with Answers"""
    games = []
    for g in db.Game.select():
        answers = [(a.cluster_id, a.user, a.word, a.e_time) for a in g.answers.select()]
        games.append({'game': g, 'answers': answers})
    return games


@arg('-fields', '--fields', nargs='+', type=str, default=None,
     help='Choose from {game_id, start_time, cluster_id, user1, user2, guess, answers}')
def print_games(fields=None):
    games = read_games()
    for gm in games:
        g = gm['game']
        gfileds = []
        for f in fields:
            if f == 'answers':
                a = gm['answers']
                gfileds.append('\n' + '\n'.join(map(lambda x: str(x[1:]), a)))
            else:
                gfileds.append(str(getattr(g, f)))
        print('\t'.join(gfileds))


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