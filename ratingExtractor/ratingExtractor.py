#!/usr/bin/env python2

import MySQLdb
import pickle

db = MySQLdb.connect(host="localhost"
                     , user="root"
                     , passwd="1kchtp7"
                     , db="ratings")

#def getRatings( actors, writers, directs):
#	for act in 

def handleActors(actors):
	ans = []
	ratings = db.cursor()
	for act in actors:
		params = act.split(" ")
		ratings.execute("""select
		  ratedActors.actor_rating
		from allNames
		  inner join ratedActors on allNames.person_id = ratedActors.person_id 
		where allNames.name like %s and allNames.name like %s;""", ("%"+params[0]+"%", "%"+params[1]+"%"))		
		res =	ratings.fetchone()
		if res is not None:
			ans.append(res[0])
			if len(ans)==5:
				return ans
	if len(ans) == 0:
		return [5.0]
	return ans


def handleWriters(actors):
	ans = []
	ratings = db.cursor()
	for act in actors:
		params = act.split(" ")
		ratings.execute("""select
		  ratedWriters.writer_rating
		from allNames
		  inner join ratedWriters on allNames.person_id = ratedWriters.person_id 
		where allNames.name like %s and allNames.name like %s;""", ("%"+params[0]+"%", "%"+params[1]+"%"))		
		res =	ratings.fetchone()
		if res is not None:
			ans.append(res[0])
	if len(ans) == 0:
		return 5.0
	return sum(ans)/len(ans)



def handleDirectors(actors):
	ans = []
	ratings = db.cursor()
	for act in actors:
		params = act.split(" ")
		ratings.execute("""select
		  ratedDirectors.director_rating
		from allNames
		  inner join ratedDirectors on allNames.person_id = ratedDirectors.person_id 
		where allNames.name like %s and allNames.name like %s;""", ("%"+params[0]+"%", "%"+params[1]+"%"))		
		res =	ratings.fetchone()
		if res is not None:
			ans.append(res[0])
	if len(ans) == 0:
		return 5.0
	return sum(ans)/len(ans)


def ratingsExtractor(actors, directors, writers):			
	ans = handleActors(actors)
	length = len(ans) 
	directorsRating = handleDirectors(directors)
	writersRating = handleWriters(writers)
	ans.append(directorsRating)
	ans.append(writersRating)
	return (ans, length)

#actors = ["Keanu Reeves",  "Rosamund Pike", "Neil Patrick Harris", "Ben Affleck"] 
#directors = ["David Fincher"]
#writers = ["David Fincher"]
#print getRatings(actors, directors, writers)
	

