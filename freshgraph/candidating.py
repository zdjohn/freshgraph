from stellargraph.data import UniformRandomMetaPathWalk
from stellargraph import StellarGraph
from gensim.models import Word2Vec
import collections

METAPATHS = [
    ["movie", "genre", "movie"],
    ["movie", "actor", "movie"],
    ["movie", "director", "movie"],
    ["movie", "tag", "movie"],
]

WALK_DISTANCE = 100


def _metapath_randomwalk(graph):
    # Create the random walker
    rw = UniformRandomMetaPathWalk(StellarGraph(graph))

    # specify the metapath schemas as a list of lists of node types.

    walks = rw.run(nodes=list(graph.nodes()),  # root nodes
                   length=WALK_DISTANCE,  # maximum length of a random walk
                   n=1,        # number of random walks per root node
                   metapaths=METAPATHS  # the metapaths
                   )

    print("Number of random walks: {}".format(len(walks)))

    return walks


def _metapath2vec(metapath_walk):
    model = Word2Vec(metapath_walk, size=128, window=5,
                     min_count=0, sg=1, workers=4, iter=10)
    return model


def train_candidates_model(graph):
    return _metapath2vec(_metapath_randomwalk(graph))


def get_similar_items(model, source_id):
    # NOTE: consider refactoring the source_id
    # source_id = 3884
    similar_nodes = model.most_similar(f'm_{source_id}', topn=100)
    # similar_ids = [key[2:] for key, _ in similar_nodes if key.startswith('m_')]
    item_scores_dict = {key[2:]: value for key,
                        value in similar_nodes if key.startswith('m_')}

    return item_scores_dict


def sort_similar_item_by_score(item_scores_dict):
    sorted_item = [(x[0], x[1]) for x in sorted(
        item_scores_dict.items(), key=lambda kv: kv[1], reverse=True)]
    return sorted_item

    # validate similarity
    # movie_meta.loc[movie_meta['id'].isin(similar_ids)]


def get_ranked_candidates(user_item_tuple, item_scores_dict):
    similar_item_ids = list(item_scores_dict.keys())
    connected_users = user_item_tuple.loc[user_item_tuple['movieID'].isin(
        similar_item_ids)]
    user_scores = collections.defaultdict(float)
    for _, row in connected_users.iterrows():
        user_scores[int(row['userID'])
                    ] += item_scores_dict[str(int(row['movieID']))]
    return [(x[0], x[1]) for x in sorted(user_scores.items(),
                                         key=lambda kv: kv[1], reverse=True)]

    # ranked_candidate_item_pair = [
    #     [int(x[0]), validate_id] for x in sorted_users]
