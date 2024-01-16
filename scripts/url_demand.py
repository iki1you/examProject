import re
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
import json
from utils import get_currencies, change_data_format


def get_medium(x):
    if x['salary_from'].equals(x['salary_to']):
        return x['salary_from']
    return (x['salary_from'] + x['salary_to']) / 2


def get_year_vacancy(s):
    return int(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4}', s)[0][0:4])


def get_vac_by_years(data):
    d = data.groupby(['published_at']).agg({
        'medium_salary': 'mean',
        'count': 'count',
    }).assign(medium_salary=lambda x: np.round(x['medium_salary'])).astype('int32')
    return d


def get_vac_by_city(data):
    k = data.shape[0]
    d = (data.groupby(['area_name']).agg({
        'medium_salary': 'mean',
        'count': 'count',
    })
         .assign(count=lambda x: round(x['count'] / k * 100, 2))
         .query('count >= 1')
         .assign(medium_salary=lambda x: np.round(x['medium_salary'])))
    return (d.sort_values(['medium_salary', 'area_name'], ascending=(False, True))[:10]['medium_salary'],
            d.sort_values(['count', 'area_name'], ascending=(False, True))[:10]['count'])


def create_report():
    csv = 'vacancies.csv'
    vacancies = parse_csv(csv)
    d = get_vac_by_years(vacancies)
    salary_vac, count_vac = get_vac_by_city(vacancies)
    data = [d, salary_vac, count_vac]
    return data


def to_rub(salary, published_at, currency, hash_dict):
    date = change_data_format(published_at)
    medium_salary = salary
    if pd.isna(currency):
        return medium_salary
    if currency == 'RUR':
        return medium_salary
    if date in hash_dict.keys():
        if currency not in hash_dict[date].keys():
            return medium_salary
        return medium_salary * hash_dict[date][currency]
    print(published_at)
    currencies = get_currencies(date)
    hash_dict[date] = currencies
    if currency in currencies.keys():
        return medium_salary * currencies[currency]
    return medium_salary


def parse_csv(csv):
    hash_currencies = dict()
    names = ['Index', 'name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
    vacancies = (pd.read_csv(csv, names=names, low_memory=False)
                 .assign(salary_from=lambda x: x['salary_from'].fillna(x['salary_to']))
                 .assign(salary_to=lambda x: x['salary_to'].fillna(x['salary_from']))
                 .assign(count=0)
                 .assign(medium_salary=get_medium))
    vacancies['Index'] = range(0, len(vacancies))
    vacancies.set_index('Index', inplace=True)
    vacancies['medium_salary'] = vacancies.apply(lambda x: to_rub(
        x['medium_salary'], x['published_at'], x['salary_currency'], hash_currencies), axis=1)
    vacancies['published_at'] = vacancies['published_at'].apply(get_year_vacancy)
    return vacancies


def create_plot():
    csv = 'vacancies.csv'
    vac = 'engineer|инженер программист|інженер|it инженер|инженер разработчик'
    vacancies = parse_csv(csv)
    data = []
    fig, sub = plt.subplots(3, 1, figsize=(10, 15))
    vac_by_years = get_vac_by_years(vacancies)['medium_salary'].to_dict()
    vac_by_years_filtered = get_vac_by_years(vacancies[vacancies['name']
                                             .str.contains(vac, na=False, case=False)])['medium_salary'].to_dict()
    vac_by_years = dict([(key, value) for key, value in vac_by_years.items() if key in vac_by_years_filtered])
    data.append((vac_by_years, vac_by_years_filtered))
    ax: Axes = sub[0]
    xlable = range(min(vac_by_years_filtered.keys()), max(vac_by_years_filtered.keys()) + 1)
    x = np.arange(len(xlable))

    y = [i for i in vac_by_years.values()]
    y2 = [i for i in vac_by_years_filtered.values()]
    width = 0.3

    ax.bar(x - width/2, y, width, label='средняя з/п')
    ax.bar(x + width/2, y2, width, label=f'з/п инженер программист')
    ax.set_title('Уровень зарплат по годам', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')
    ax.set_xticklabels(xlable)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=12)
    ax.grid(axis='y')

    set_font_size(ax, 8)

    vac_by_years = get_vac_by_years(vacancies)['count'].to_dict()
    vac_by_years_filtered = get_vac_by_years(vacancies[vacancies['name']
                                             .str.contains(vac, na=False, case=False)])['count'].to_dict()

    vac_by_years = dict([(key, value) for key, value in vac_by_years.items() if key in vac_by_years_filtered])
    data.append((vac_by_years, vac_by_years_filtered))
    width = 0.3
    ax = sub[1]
    xlable = range(min(vac_by_years_filtered.keys()), max(vac_by_years_filtered.keys()) + 1)
    x = np.arange(len(xlable))
    y = [i for i in vac_by_years.values()]

    ax.bar(x, y, width)

    ax.set_title('Количество вакансий по годам')
    ax.set_xticks(x)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')
    ax.set_xticklabels(xlable)
    set_font_size(ax, 8)

    ax.grid(axis='y')

    width = 0.3
    ax = sub[2]
    xlable = range(min(vac_by_years_filtered.keys()), max(vac_by_years_filtered.keys()) + 1)
    x = np.arange(len(xlable))
    y2 = [i for i in vac_by_years_filtered.values()]
    ax.bar(x, y2, width)
    ax.set_title('Количество вакансий по годам для профессии инженер-программист')
    ax.set_xticks(x)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')
    ax.set_xticklabels(xlable)
    set_font_size(ax, 8)
    ax.grid(axis='y')

    return fig, sub, data


def set_font_size(ax, size):
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(size)
    dx = 0.06
    dy = 0
    fig = plt.figure()
    offset = matplotlib.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
    for label in ax.xaxis.get_majorticklabels():
        label.set_transform(label.get_transform() + offset)


def create_pdf():
    figure, sub, data = create_plot()
    figure.savefig('graphics.png')

    data_year_keys = list(zip(*list(data[0][0].items())[::-1]))
    data_year_keys = [data_year_keys[0][::-1], data_year_keys[1][::-1]]

    data_year_keys_filtered = tuple(zip(*list(data[0][1].items())[::-1]))
    data_year_keys_filtered = [data_year_keys_filtered[0][::-1], data_year_keys_filtered[1][::-1]]

    data_year_values = tuple(zip(*list(data[1][0].items())[::-1]))
    data_year_values = [data_year_values[0][::-1], data_year_values[1][::-1]]

    data_year_values_filtered = tuple(zip(*list(data[1][1].items())[::-1]))
    data_year_values_filtered = [data_year_values_filtered[0][::-1], data_year_values_filtered[1][::-1]]
    with open('tables.txt', 'w', encoding='utf-8') as file:
        print(*data_year_keys)
        print(*data_year_keys_filtered)
        print(*data_year_values)
        print(*data_year_values_filtered)
        print("Динамика уровня зарплат по годам:")
        file.write(json.dumps(dict(zip(*data_year_keys))))
        file.write('\n')
        print("Динамика уровня зарплат по годам для профессии инженер-программист:")
        file.write(json.dumps(dict(zip(*data_year_keys_filtered))))
        file.write('\n')
        print("Динамика количества вакансий по годам:")
        file.write(json.dumps(dict(zip(*data_year_values))))
        file.write('\n')
        print("Динамика количества вакансий по годам для профессии инженер-программист:")
        file.write(json.dumps(dict(zip(*data_year_values_filtered))))
        file.write('\n')


create_pdf()
