import re
import requests
from bs4 import BeautifulSoup


def change_data_format(s):
    a = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4}', s)[0][:10]
    m = a[-5:-3]
    y = a[:4]
    return m + '/' + y


def get_currencies(date):
    base_url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req=01/{date}'
    response = requests.get(base_url).content
    x = BeautifulSoup(response, "xml")
    valutes = [(i.find('CharCode').text, float(i.find('VunitRate').text.replace(',', '.')))
               for i in x.select('ValCurs > Valute')]
    return dict(valutes)
