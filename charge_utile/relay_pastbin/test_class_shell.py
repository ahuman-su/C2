import requests

API_KEY = "API"

data = {
    'api_dev_key': API_KEY,
    'api_option': 'paste',
    'api_paste_code': 'Hello Pastebin',
    'api_paste_private': '2',       # 0=public, 1=non listé, 2=privé
    'api_paste_name': 'Titre test',
    'api_paste_expire_date': '10M'  # expire dans 10 minutes
}

r = requests.post("https://pastebin.com/api/api_post.php", data=data)
print(r.text)  # retourne l'URL du paste