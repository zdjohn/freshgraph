import pandas
import networkx as nx

data_root_folder = "./data"

movie_directors = pandas.read_csv(
    f"{data_root_folder}/movie_directors.dat", sep="\t", encoding="ISO-8859-1")
movie_genres = pandas.read_csv(
    f"{data_root_folder}/movie_genres.dat", sep="\t", encoding="ISO-8859-1")
movie_actors = pandas.read_csv(
    f"{data_root_folder}/movie_actors.dat", sep="\t", encoding="ISO-8859-1")

all_movie_tags = pandas.read_csv(
    f"{data_root_folder}/movie_tags.dat", sep="\t", encoding="ISO-8859-1")
movie_tags = all_movie_tags[all_movie_tags['tagWeight'] > 1]

movie_meta = pandas.read_csv(
    f"{data_root_folder}/movies.dat", sep="\t", encoding="ISO-8859-1")


# top 3 actors of each movie
lead_actors = movie_actors[movie_actors['ranking'] <= 3]

# training set
movies_train = movie_meta[movie_meta['year'] < 2009]
# validation set 29 movies
movies_validate = movie_meta[movie_meta['year'] >= 2009]

# user movie interactions
movie_users = pandas.read_csv(
    f"{data_root_folder}/user_ratedmovies.dat", sep="\t", encoding="ISO-8859-1")
positive_ratings = movie_users[movie_users['rating'] >= 3]
negative_ratings = movie_users[movie_users['rating'] < 2]

# exclude validation user-movie tuples
user_item_tuple_train = positive_ratings[~positive_ratings['movieID'].isin(
    movies_validate['id'].values)].filter(['userID', 'movieID'], axis=1)


user_node_ids = ["u_" + str(user_node_id)
                 for user_node_id in set(positive_ratings['userID'].values)]
movie_node_ids = ["m_" + str(user_node_id)
                  for user_node_id in set(positive_ratings['movieID'].values)]

# pos_movie_user_edges = [("m_" + str(row['movieID']), "u_" + str(row['userID']))
#                         for _, row in positive_ratings.iterrows()]


def get_graph():
    movie_node_ids = ["m_" + str(movie_id)
                      for movie_id in set(movie_meta['id'].values)]

    genres_node_ids = ["g_" + str(genre_id)
                       for genre_id in set(movie_genres['genre'].values)]
    movie_genre_edges = [("m_" + str(row['movieID']), "g_" + str(row['genre']))
                         for _, row in movie_genres.iterrows()]

    actors_node_ids = ["a_" + str(actor_id)
                       for actor_id in set(lead_actors['actorID'].values)]
    movie_actor_edges = [("m_" + str(row['movieID']), "a_" +
                          str(row['actorID'])) for _, row in lead_actors.iterrows()]

    directors_node_ids = [
        "d_" + str(director_id) for director_id in set(movie_directors['directorID'].values)]
    movie_director_edges = [("m_" + str(row['movieID']), "d_" + str(row['directorID']))
                            for _, row in movie_directors.iterrows()]

    tag_node_ids = [
        "t_" + str(tag_id) for tag_id in set(movie_tags['tagID'].values)]
    movie_tag_edges = [("t_" + str(row['movieID']), "d_" + str(row['tagID']))
                       for _, row in movie_tags.iterrows()]

    g_nx = nx.Graph()  # create the graph

    g_nx.add_nodes_from(movie_node_ids, label="movie")

    g_nx.add_nodes_from(genres_node_ids, label="genre")
    g_nx.add_edges_from(movie_genre_edges, label="movie_genre")

    g_nx.add_nodes_from(actors_node_ids, label="actor")
    g_nx.add_edges_from(movie_actor_edges, label="movie_actor")

    g_nx.add_nodes_from(directors_node_ids, label="director")
    g_nx.add_edges_from(movie_director_edges, label="movie_director")

    g_nx.add_nodes_from(tag_node_ids, label="tag")
    g_nx.add_edges_from(movie_tag_edges, label="movie_tag")

    print("Number of nodes {} and number of edges {} in graph.".format(
        g_nx.number_of_nodes(), g_nx.number_of_edges()))

    return g_nx
