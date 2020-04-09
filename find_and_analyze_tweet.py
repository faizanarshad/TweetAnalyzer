import argparse

import pandas as pd
from pandas import DataFrame
import tweepy
from twython import Twython

# This will get the auth tokens
def get_auth_token(file_name):
    global API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_SECRET
    f = open(file_name, 'r')
    ak = f.readlines()
    f.close()
    API_KEY = ak[0].replace("\n", "")
    API_SECRET_KEY = ak[1].replace("\n", "")
    ACCESS_TOKEN = ak[2].replace("\n", "")
    ACCESS_SECRET = ak[3].replace("\n", "")


def get_tweets_against_hashtag(target_num, hashtag):
    auth1 = tweepy.auth.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth1.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth1)

    id_str_list = []

    counter = 0
    for tweet in tweepy.Cursor(api.search, q=hashtag, lang="en", count=target_num).items():
        id_str_list.append(tweet.id_str)  # author/user ID#
        counter = counter + 1
        if (counter == target_num):
            break

    return id_str_list


def get_features(tweet_ids, filename):
    d = {'id': '', 'created_at': '', 'from_user': '', 'followers_count': '', 'friends_count': '', 'statuses_count': '',
         'verified': '', 'location': '', 'text': '', 'retweet_count': '', 'favorite_count': '', 'hashtag_count': '',
         'url_count': '', 'mentions_count': '', 'Fr_Fo_Ratio': '', 'St_Fo_Ratio': '', 'links': ''}

    length = len(tweet_ids)  # Getting the length of 'tweet_ids'.

    df = DataFrame(d, index=[0])  # Creating a DataFrame

    twitter = Twython(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_SECRET)

    for i in range(0, length):
        try:
            status = twitter.show_status(id=tweet_ids[i])
            d['id'] = status['id_str'].encode('utf-8')
            d['created_at'] = status['created_at'].encode('utf-8')
            d['from_user'] = status['user']['screen_name'].encode('utf-8')
            d['followers_count'] = status['user']['followers_count']
            d['friends_count'] = status['user']['friends_count']
            d['statuses_count'] = status['user']['statuses_count']
            d['verified'] = 1 if status['user']['verified'] else 0
            d['location'] = 0 if (len(status['user']['location'].encode('utf-8')) == 0) else 1
            d['text'] = status['text'].encode('utf-8')
            d['retweet_count'] = status['retweet_count']
            d['favorite_count'] = status['favorite_count']
            d['hashtag_count'] = len(status['entities']['hashtags'])
            d['url_count'] = len(status['entities']['urls'])
            d['mentions_count'] = len(status['entities']['user_mentions'])
            d['Fr_Fo_Ratio'] = status['Fr_Fo_Ratio'] if 'Fr_Fo_Ratio' in status else d['friends_count']/d['followers_count']
            d['St_Fo_Ratio'] = status['St_Fo_Ratio'] if 'St_Fo_Ratio' in status else d['statuses_count']/d['followers_count']
            if (len(status['entities']['urls']) > 0):
                for x in range(0, len(status['entities']['urls'])):
                    d['links'] += str(status['entities']['urls'][x]['expanded_url'].encode('utf-8')) + "  "
            d['links'] = 0 if d['links'] == '' else 1
            df = df.append(d, ignore_index=True)
            df.to_csv(filename, index=False)  # Saving file to disk
            d['links'] = ''
        except Exception as err:
            print(err)

    print("\nAll Done!")


def normalize_features(inputfile, outputfile):
    features = pd.read_csv(inputfile)
    normalized = pd.read_csv(inputfile)
    mean = features.mean()
    std = features.std()
    normalized['favorite_count'] = (features['favorite_count'] - mean[6])/std[6] if std[6] != 0 else 0
    normalized['followers_count'] = (features['followers_count'] - mean[0])/std[0]
    normalized['friends_count'] = (features['friends_count'] - mean[1])/std[1]
    normalized['statuses_count'] = (features['statuses_count'] - mean[2])/std[2]
    normalized['retweet_count'] = (features['retweet_count'] - mean[5])/std[5]
    normalized['Fr_Fo_Ratio'] = (features['Fr_Fo_Ratio'] - mean[10])/std[10]
    normalized['St_Fo_Ratio'] = (features['St_Fo_Ratio'] - mean[11])/std[11]
    normalized.to_csv(outputfile, columns=['followers_count', 'friends_count','statuses_count','mentions_count','retweet_count','favorite_count', 'hashtag_count','url_count','verified','location','Fr_Fo_Ratio','St_Fo_Ratio' ], index=False)

    return normalized


def do_formatting(filename, features):
    file = open(filename, 'w')
    for i in range(0, len(features)):
        # file1.write(str(features['label'][i]) + " qid:1" + " 1:"+str(features['followers_count'][i]) + " 2:"+str(features['friends_count'][i]) + " 3:"+str(features['statuses_count'][i]) + " 4:"+str(features['mentions_count'][i]) + " 5:"+str(features['retweet_count'][i]) + " 6:"+str(features['favorite_count'][i]) + " 7:"+str(features['hashtag_count'][i]) + " 8:"+str(features['url_count'][i]) + " 9:"+str(features['verified'][i]) + " 10:"+str(features['location'][i]) + "\n")
        file.write("qid:1" + " 1:" + str(features['followers_count'][i]) + " 2:" + str(
            features['friends_count'][i]) + " 3:" + str(features['statuses_count'][i]) + " 4:" + str(
            features['mentions_count'][i]) + " 5:" + str(features['retweet_count'][i]) + " 6:" + str(
            features['favorite_count'][i]) + " 7:" + str(features['hashtag_count'][i]) + " 8:" + str(
            features['url_count'][i]) + " 9:" + str(features['verified'][i]) + " 10:" + str(
            features['location'][i]) + "\n")

    file.close()


def main(args):
    get_auth_token(args.AuthFile)
    ids_str = get_tweets_against_hashtag(args.TweetCount, args.Hashtag)
    get_features(ids_str, args.Filename + '.csv')  # change this argument to new file
    normalized = normalize_features(args.Filename + '.csv', args.Filename + '_normalized.csv')
    do_formatting(args.Filename + '_formatted.txt', normalized)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search tweets on the basis of hashtag.')
    parser.add_argument('-Hashtag', default='#lockdowneffect', type=str, help='Hashtag')
    parser.add_argument('-Filename', default='lockdown_tweets', type=str, help='Filename')
    parser.add_argument('-AuthFile', default='auth.k.txt', type=str, help='Auth token file')
    parser.add_argument('-TweetCount', default=10, type=int, help='Total number of tweets to be searched')

    args = parser.parse_args()
    main(args)

