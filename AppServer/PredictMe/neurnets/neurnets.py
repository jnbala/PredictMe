
import MySQLdb
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet
import os
import pickle
from PredictMe.ratingExtractor.ratingExtractor import get_cast_rating_for_neurnets


def fill_subdataset(db, movies_cur, actors_cur, directors_cur, writers_cur, actors_num, dataset, minrate, maxrate):
    movies_cur.execute("""select distinct(title_id), allMovies.rating, allMovies.production_year
                            from  allMovies
                            where rating >= {0} and rating <= {1} and
                            exists  (
                              select title_id from PersonsFULL
                              where (role_id = 1 or role_id = 2) and PersonsFULL.title_id = allMovies.title_id
                              group by title_id
                              having count(person_id) >= {2}
                            ) and exists (
                              select title_id from PersonsFULL
                              where role_id = 8 and PersonsFULL.title_id = allMovies.title_id
                            ) and exists (
                              select title_id from PersonsFULL
                              where role_id = 4 and PersonsFULL.title_id = allMovies.title_id
                            )
                            ORDER BY RAND()
                            LIMIT 25""".format(minrate, maxrate, actors_num))

    for movie in movies_cur:
        actors_cur.execute("""select ratedActors.actor_rating
                              from PersonsFULL inner join ratedActors
                                on PersonsFULL.person_id = ratedActors.person_id
                                  and (PersonsFULL.role_id = 1 or PersonsFULL.role_id = 2)
                                  and title_id = {0}
                              group by ratedActors.person_id
                              order by RAND() limit {1}""".format(movie[0], actors_num))
        directors_cur.execute("""select ratedDirectors.director_rating
                              from PersonsFULL inner join ratedDirectors
                                on PersonsFULL.person_id = ratedDirectors.person_id
                                  and PersonsFULL.role_id = 8
                                  and title_id = {0}
                              group by ratedDirectors.person_id
                              order by RAND() limit 1""".format(movie[0]))
        writers_cur.execute("""select ratedWriters.writer_rating
                              from PersonsFULL inner join ratedWriters
                                on PersonsFULL.person_id = ratedWriters.person_id
                                  and PersonsFULL.role_id = 4
                                  and title_id = {0}
                              group by ratedWriters.person_id
                              order by RAND() limit 1""".format(movie[0]))

        actors_rates = tuple(t[0] for t in actors_cur.fetchmany(actors_num))
        dataset.addSample(# (movie[2],) +
                          actors_rates +
                          (writers_cur.fetchone()[0], directors_cur.fetchone()[0],), (movie[1],))



def create_datasets():
    db = MySQLdb.connect(host="localhost",
                         user="imdb",
                         passwd="imdb",
                         db="imdb")

    movies_cur = db.cursor()
    actors_cur = db.cursor()
    directors_cur = db.cursor()
    writers_cur = db.cursor()

    for actors_num in range(1, 6):
        print actors_num

        dataset = SupervisedDataSet(2 + actors_num, 1)
        fill_subdataset(db, movies_cur, actors_cur, directors_cur, writers_cur, actors_num, dataset, 0, 2)
        fill_subdataset(db, movies_cur, actors_cur, directors_cur, writers_cur, actors_num, dataset, 2, 4.2)
        fill_subdataset(db, movies_cur, actors_cur, directors_cur, writers_cur, actors_num, dataset, 4.2, 8.6)
        fill_subdataset(db, movies_cur, actors_cur, directors_cur, writers_cur, actors_num, dataset, 8.6, 10)

        with open('dataset_' + str(actors_num) + '.data', 'wb') as f:
            pickle.dump(dataset, f, pickle.HIGHEST_PROTOCOL)

    movies_cur.close()
    actors_cur.close()
    directors_cur.close()
    writers_cur.close()


def trainNetwork(dataset, dim):
    net = buildNetwork(2 + dim, 12 + dim, 1)
    trainer = BackpropTrainer(net, dataset)
    trainer.trainEpochs(10)
    return net


def computeMovieRating(movie_year, actors, writers, directors):
    features, actor_dim = get_cast_rating_for_neurnets(actors, directors, writers)

    print features, actor_dim

    neuronet_file = os.path.join(os.path.dirname(__file__), 'neuronet_{0}.data'.format(str(actor_dim)))
    dataset_file = os.path.join(os.path.dirname(__file__), 'dataset_{0}.data'.format(str(actor_dim)))

    if os.path.isfile(neuronet_file):
        with open(neuronet_file, 'r') as f:
            net = pickle.load(f)
        movie_rating = net.activate(features)
    elif os.path.isfile(dataset_file):
        with open(dataset_file, 'r') as f:
            dataset = pickle.load(f)
        net = trainNetwork(dataset, actor_dim)
        with open(neuronet_file, 'wb') as f:
            pickle.dump(net, f)
        movie_rating = net.activate(features)
    else:
        print "Dataset for dimension " + str(actor_dim) + " doesn't exist."
        raise
    return movie_rating[0]

if __name__ == "__main__":
    print computeMovieRating(0, 0, 0, 0)


