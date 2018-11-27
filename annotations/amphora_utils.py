import requests
from repository import auth
"""
Amphora helper functions.
"""

def retrieve_amphora_text(url, user):
    text_request = requests.get(url, headers=auth.jars_github_auth(user))
    text_json = text_request.json()
    #find the first text in content
    for content in text_json['content']:
        if content['content_resource']['content_type'] == 'text/plain':
            text_content = content['content_resource']['id']
            # Save time and stop the iteration
            return text_json, text_content