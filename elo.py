from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import csv

app = Flask(__name__)
DATABASE = 'subreddits.db'

# initialize database: create db file if it doesn't already exist. load list of subreddits into database
def init_db():
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS subreddits (
			id INTEGER PRIMARY KEY, 
			name TEXT UNIQUE, 
			elo REAL DEFAULT 1500
		)''')
	conn.commit()
	with open('subreddits.csv', 'r') as file:
		reader = csv.reader(file)
		for row in reader: 
			subreddit = row[0].strip()
			c.execute("INSERT OR IGNORE INTO subreddits (name) VALUES (?)", (subreddit,))
	conn.commit()
	conn.close()

#fetch two random subreddits to "compete" in matchup
def get_random_pair():
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute("SELECT * FROM subreddits ORDER BY RANDOM() LIMIT 2")
	pair = c.fetchall()
	conn.close()
	return pair

#update the elo of the winner and loser in the database. k=32 is default, can adjust more
def update_elo(winner_id, loser_id, k=32):
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute("SELECT elo FROM subreddits WHERE id = ?", (winner_id,))
	winner_elo = c.fetchone()[0]
	c.execute("SELECT elo FROM subreddits WHERE id = ?", (loser_id,))
	loser_elo = c.fetchone()[0]
# fetch existing elos for loser, winner from sqlite3 database

	expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
	expected_loser = 1-expected_winner

	
#update elo score
	new_winner_elo = winner_elo + k * (1 - expected_winner)
	new_loser_elo = loser_elo + k * (0 - expected_loser)
	c.execute("UPDATE subreddits SET elo = ? WHERE id = ?", (new_winner_elo, winner_id))
	c.execute("UPDATE subreddits SET elo = ? WHERE id = ?", (new_loser_elo, loser_id))
	conn.commit()
	conn.close()


#initialize flask app

@app.route('/')
def index():
	pair = get_random_pair()
	return render_template('index.html', pair=pair)

# voting code
@app.route('/vote', methods=['POST'])
def vote():
	winner_id = request.form['winner']
	loser_id = request.form['loser']
	update_elo(winner_id, loser_id)
	return redirect(url_for('index'))

@app.route('/rankings')
def rankings():
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute("SELECT name, elo FROM subreddits ORDER BY elo DESC")
	rankings = c.fetchall()
	conn.close()
	return render_template('rankings.html', rankings=rankings)

#initialize app if main
if __name__== '__main__':
	init_db()
	app.run(debug=True)


	

