# YouTube-Dislikes
170 lines of code to remedy some very bad decisions on YouTubes part.

This script brings back public dislike count and the like/dislike bar for channels that use it.

This script takes the backend dislike count for videos and adds it to the description of said videos, with a bar also, i like the bar, i worked hard on that.

The script currently updates all videos as quickly as possible, so if you only have 10 videos they will update several times a second and eat your quota.

To setup and use you need a client_secret.json file with the https://www.googleapis.com/auth/youtube scope enabled, which means the project needs the youtube data api v3 enabled
The client_secret file and all other settings related to it can be located at https://console.developers.google.com/, detailed setup video coming soon
