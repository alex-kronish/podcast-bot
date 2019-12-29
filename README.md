# Podcastacular, the podcast bot.
A twitter/mastodon bot that generates random podcast titles/descriptions. You know, for comedy.
See it in action at: https://twitter.com/Podcastacular and https://botsin.space/@podcastacular

# Notes
* In the configuration directory, there is a file called api_keys.json. These are obviously not real API keys, posting those in public is generally not a good idea. What you need to do to use this, is copy that file as "api_keys_secret.json" and then fill it in with your mastodon and twitter API keys. 
* Don't use one of those two social media services? That's OK, just comment out the call to whichever method you dont use at the bottom of podcast_generator.py
* I realize the regex I used to clean the titles is very sloppy. For one, I probably should have iterated over an array instead of what I did but I started with two expressions and it kinda spiralled out of control from there.
