import requests


BASE_URL = ("https://api.hh.ru/vacancies?search_field=name&text=':(инженер AND "
            "программист)'&order_by=publication_time&per_page=10")
response = requests.get(BASE_URL)
vacancies = response.json()
for i in vacancies['items']:
    print(i['name'], i['published_at'])