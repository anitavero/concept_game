import os
import json
from concept_game_backend.db import *


if __name__ == '__main__':
    db.create_tables([Game, Answer, Cluster])

    # Insert cluster data into Cluster table with unique ids.
    with open('concept_game_backend/cluster_files.json', 'r') as f:
        cf = json.load(f)

    for clfile in cf['clfiles']:
        with open(os.path.join(cf['datapath'], clfile), 'r') as f:
            clusters = json.load(f)

        embid = clfile.split('.')[0]
        for cl, words in clusters:
            if len(words) > 1:  # Leave out one word clusters
                Cluster.create(cluster=f'{embid}_{cl}', words=', '.join(words))