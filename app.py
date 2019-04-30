from flask import Flask, request, redirect, url_for, session, g, flash,render_template
from flask_oauth import OAuth
import tweepy
from afinn import Afinn
from collections import Counter
# configuration
SECRET_KEY = 'development key'
DEBUG = True

# setup flask
app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()

consumer_key='RZV6wuWdTLJR3Af6sCnSif3NX'
consumer_secret='cXSEsK7eHZhUZYwpojVvNETgXw4Io7tUB6iUsY81wnrV73COHu'

twitter = oauth.remote_app('twitter',
base_url='https://api.twitter.com/1/',
# where flask should look for new request tokens
request_token_url='https://api.twitter.com/oauth/request_token',
# where flask should exchange the token with the remote application
access_token_url='https://api.twitter.com/oauth/access_token',
authorize_url='https://api.twitter.com/oauth/authenticate',
# the consumer keys from the twitter application registry.
consumer_key=consumer_key,
consumer_secret=consumer_secret
)

def cal_sentiment(sen):
	af = Afinn()
	pos = []
	neg = []
	neu = []
	for i in range(len(sen)):
		score=int(af.score(sen[i]))
		if(score>0):
			pos.append(score)
		if(score==0):
			neu.append(score)
		else:
			neg.append(score)
	return len(pos),len(neg),len(neu)

@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@app.route('/')
def index():
		access_token = session.get('access_token')
		return render_template('login.html')

@app.route('/logout')
def logout():
	session.clear()
	return render_template('login.html')

@app.route('/login')
def login():
	session.clear()
	return twitter.authorize(callback=url_for('oauth_authorized',next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
	next_url = request.args.get('next') or url_for('index')
	if resp is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)


	access_token = resp['oauth_token']
	session['access_token'] = access_token
	session['screen_name'] = resp['screen_name']
	session['user_id'] = resp['user_id']
	session['twitter_token'] = (
	resp['oauth_token'],
	resp['oauth_token_secret']
	)

	access_token = access_token[0]
	auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
	auth.set_access_token(resp['oauth_token'],resp['oauth_token_secret'])
	api = tweepy.API(auth)

	user = api.me()
	new_tweets = api.user_timeline(screen_name = resp['screen_name'],count=200, tweet_mode="extended")
	twe=[]
	l=[]
	retweet_c = 0
	for tweet in new_tweets:
		if tweet.retweeted:
			retweet_c = retweet_c + 1

		twe.append(str(tweet.full_text))
		ht=tweet.entities.get('hashtags')
		myvalues = [i['text'] for i in ht if 'text' in i]
		if(len(myvalues)>0):
			l.append(myvalues)
	hashtag_list = []
	for sublist in l:
		for item in sublist:
			hashtag_list.append(item)

	key = Counter(hashtag_list).keys() # equals to list(set(words))
	val = Counter(hashtag_list).values()
	dictionary = dict(zip(key, val))
	final_dict=sorted([(value,key) for (key,value) in dictionary.items()],reverse=True)
	top_hastag = []
	if(len(final_dict)>=3):
		top_hastag.append(final_dict[0][0])
		top_hastag.append(final_dict[1][0])
		top_hastag.append(final_dict[2][0])
		top_hastag_count =[]
		top_hastag_count.append("#"+final_dict[0][1])
		top_hastag_count.append("#"+final_dict[1][1])
		top_hastag_count.append("#"+final_dict[2][1])


	pos_one,neg_one,neu_one = cal_sentiment(twe)
	join_date = str(user.created_at)
	join_d= join_date[:9]
	join_l = join_d[26:29]
	join_date = join_d + " " + join_l


	labels = [
    'Positive','Negative','Neutral']

	values = [pos_one,neg_one,neu_one]

	maxnu = []
	maxnu.append(pos_one)
	maxnu.append(neg_one)
	maxnu.append(neu_one)
	maxr = max(maxnu)


	return render_template('index.html',join_date=join_date,tw=resp['screen_name'],loc=user.location,name=user.name,following=user.friends_count,followers=user.followers_count, max=(maxr+5), labels=labels, values=values,htags=top_hastag_count,tweets=twe,retweets=retweet_c,tt=len(new_tweets))

if __name__ == '__main__':
	app.run()
