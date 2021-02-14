import os
import json
from collections import defaultdict
from db import *

if __name__ == '__main__':
    db.create_tables([Game, Answer, Cluster])

    # Insert cluster data into Cluster table with unique ids.
    with open('cluster_files.json', 'r') as f:
        cf = json.load(f)

    for clfile in cf['clfiles']:
        with open(os.path.join(cf['datapath'], clfile), 'r') as f:
            cl_dict = json.load(f)

        clusters = defaultdict(list)
        for w, c in cl_dict.items():
            clusters[int(c)].append(w)

        embid = clfile.split('.')[0]
        for cl, words in clusters.items():
            Cluster.create(cluster=f'{embid}_{cl}', words=', '.join(words))