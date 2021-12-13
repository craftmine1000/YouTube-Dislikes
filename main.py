# -*- coding: utf-8 -*-
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import googleapiclient.errors
import json
import time
import datetime
import os
import sys

### settings ###

bar_length = 10
char_seq = [ '█', '▓', '▒', '░', ]
banner_title = 'Likes/Dislikes'
banner_format = '{title}: 👍{likes}/👎{dislikes} {bar} updated: {date}'

ui_oauth = True
progress_bar_length = 80

### settings ###




newline = '\n'
batch_size = 50
scopes = ['https://www.googleapis.com/auth/youtube']

def tqdm(gen_object):
	l = len(list(gen_object))
	for k,v in enumerate(gen_object):
		print('\r' + '#' * int(((k+1) / l) * progress_bar_length) + ' ' + str(k+1) + '/' + str(l), end='')
		yield v

# stolen from https://stackoverflow.com/questions/1094841
def num_fmt(num, suffix=''):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            return f'{num:3.1f}{unit}{suffix}'
        num /= 1000.0
    return f'{num:.1f}Y{suffix}'

def test_bar():
	#print(0, 40)
	print(get_bar(0, 40))
	for i in range(bar_length*len(char_seq)):
		#print(i+1, bar_length*len(char_seq) - i-1)
		print(get_bar(i+1, bar_length*len(char_seq) - i-1))

def get_bar(likes, dislikes):
	total = likes + dislikes

	if total == 0:
		return char_seq[-1] * bar_length

	likes_norm = likes / total

	l = len(char_seq)
	likes_amnt = int(likes_norm * bar_length * l)
	dislikes_amnt = (bar_length - likes_amnt // l) - 1
	if dislikes_amnt == -1:
		return (char_seq[-1] * (likes_amnt // l))
	else:
		return (char_seq[-1] * (likes_amnt // l)) + char_seq[likes_amnt % l] + (char_seq[0] * dislikes_amnt)

def execute_wait(request):
	while True:
		try:
			return request.execute()
		except googleapiclient.errors.HttpError as e:
			if json.loads(e.content.decode())['error']['errors'][0]['reason'] == 'quotaExceeded':
				print('waiting an hour...')
				time.sleep(60 * 60)
			else:
				raise e
def main():
	# Disable OAuthlib's HTTPS verification when running locally.
	# *DO NOT* leave this option enabled in production.
	os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

	api_service_name = 'youtube'
	api_version = 'v3'
	client_secrets_file = 'client_secret2.json'
	token_file = 'token.json'

	# Get credentials and create an API client
	credentials = None
	if os.path.exists(token_file):
		credentials = Credentials.from_authorized_user_file(token_file, scopes)
	# If there are no (valid) credentials available, let the user log in.
	if not credentials and not credentials.valid:
		if credentials and credentials.expired and credentials.refresh_token:
			credentials.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file( client_secrets_file, scopes)
			if ui_oauth:
				credentials = flow.run_local_server()
			else:
				credentials = flow.run_console()
		# Save the credentials for the next run
		with open(token_file, 'w') as token:
			token.write(credentials.to_json())

	youtube = build(
		api_service_name, api_version, credentials=credentials)
	request = youtube.channels().list(
		part='contentDetails',
		mine=True,
		maxResults=batch_size
	)
	response = execute_wait(request)

	uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

	while True:
		videos = []
		token=None
		while True:
			request = youtube.playlistItems().list(
				part='contentDetails',
				playlistId=uploads_id,
				maxResults=batch_size,
				pageToken=token
			)
			response = execute_wait(request)
			videos.extend(list(map(lambda x: x['contentDetails']['videoId'], response['items'])))
			try:
				token = response['nextPageToken']
			except KeyError as e: break

		# aquire video stats
		for i in tqdm(range(0, len(videos), batch_size)):
			request = youtube.videos().list(
				part='snippet,statistics',
				id=','.join(videos[i : i + batch_size])
			)
			response = execute_wait(request)

			for item in response['items']:
				desc = item['snippet']['description'].split(newline)
				stats = item['statistics']
				bar = get_bar(int(stats['likeCount']), int(stats['dislikeCount']))
				inject = banner_format.format(
					title=banner_title,
					likes=num_fmt(int(stats['likeCount'])),
					dislikes=num_fmt(int(stats['dislikeCount'])),
					bar=bar,
					date=str(datetime.datetime.today().date())
				)

				if desc and len(desc) and desc[0] and desc[0][:len(banner_title)] == banner_title:
					desc = desc[1:]

				desc = [inject] + desc

				request = youtube.videos().update(
					part='snippet',
					body={
						'id': item['id'],
						'snippet': {
							'categoryId': item['snippet']['categoryId'],
							'description': newline.join(desc)[:5000],
							'title': item['snippet']['title']
						}
					}
				)
				response = execute_wait(request)

if __name__ == '__main__':
	main()