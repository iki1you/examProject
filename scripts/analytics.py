import re
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
import json
from utils import get_currencies, change_data_format
from collections import Counter


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
    return (d.sort_values(['medium_salary', 'area_name'], ascending=(False, True))[:10]['medium_salary'].to_dict(),
            d.sort_values(['count', 'area_name'], ascending=(False, True))[:10]['count'].to_dict())


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
    names = ['name', 'skills', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
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
    return vacancies.query('medium_salary < 10000000000')


def demand_create_plot(vacancies, vac):
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
    ax.bar(x - width / 2, y, width, label='средняя з/п')
    ax.bar(x + width / 2, y2, width, label=f'з/п инженер программист')
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


def geography_create_plot(vacancies, vac):
    data = []
    fig, sub = plt.subplots(4, 1, figsize=(15, 40))
    margins = {
        "left": 0.1,
        "bottom": 0.020,
        "right": 0.990,
        "top": 0.98
    }

    fig.subplots_adjust(**margins)
    level_sal_city, count_sal_city = get_vac_by_city(vacancies)
    level_sal_city_filtered, count_sal_city_filtered = get_vac_by_city(vacancies[vacancies['name']
                                                                       .str.contains(vac, na=False, case=False)])
    data.append((level_sal_city, count_sal_city))
    data.append((level_sal_city_filtered, count_sal_city_filtered))

    ax: Axes = sub[0]
    x = [i for i in level_sal_city.keys()]
    y = [i for i in level_sal_city.values()]

    width = 0.3

    ylable = range(0, int(max(y)) + 19999, 20000)
    ax.barh(x, y, width)
    ax.set_xticks(ylable)
    ax.set_title('Уровень зарплат по городам')

    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    set_font_size(ax, 8)

    ax: Axes = sub[1]
    x = [i for i in level_sal_city_filtered.keys()]
    y = [i for i in level_sal_city_filtered.values()]

    width = 0.3

    ylable = range(0, int(max(y)) + 19999, 20000)
    ax.barh(x, y, width)
    ax.set_xticks(ylable)
    ax.set_title('Уровень зарплат по городам для профессии программист-инженер')

    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    set_font_size(ax, 8)

    ax: Axes = sub[2]
    x = [i for i in count_sal_city.keys()]
    y = np.array([i for i in count_sal_city.values()])

    ax.pie(y, labels=x)
    ax.set_title('Доля вакансий по городам')
    set_font_size(ax, 8)

    ax: Axes = sub[3]
    x = [i for i in count_sal_city_filtered.keys()]
    y = np.array([i for i in count_sal_city_filtered.values()])

    ax.pie(y, labels=x)
    ax.set_title('Доля вакансий по городам для профессии программист-инженер')
    set_font_size(ax, 8)
    return fig, sub, data


def skills_format(line):
    return '\n'.join(line.split(', '))


def update_counter(x, counter):
    if isinstance(x, str):
        x = x.replace('\r', '')
        return counter.update(Counter(x.strip().split('\n')))


def get_skills_by_years(vacancies, years):
    skills_by_years = dict()
    counter = Counter()
    vacancies['skills'].apply(lambda x: update_counter(x, counter))
    top_skills = dict(counter.most_common(20))
    for year in years:
        counter = Counter()
        vacancies[vacancies['published_at'] == year]['skills'].apply(lambda x: update_counter(x, counter))
        if len(counter) != 0:
            skills_by_years[year] = dict(counter.most_common(20))
    return top_skills, skills_by_years


def skills_create_plot(vacancies, vac, data_year_keys):
    data = []
    top_skills, skills_by_years = get_skills_by_years(vacancies, data_year_keys[0])
    print(top_skills, skills_by_years)
    plt.rcParams.update({'figure.max_open_warning': 0})
    fig, sub = plt.subplots(len(skills_by_years.items()) + 1, 1, figsize=(10, (len(skills_by_years.items()) + 1) * 5))
    margins = {
        "left": 0.3,
        "bottom": 0.020,
        "right": 0.990,
        "top": 0.98
    }
    fig.subplots_adjust(**margins)
    data.append(top_skills)
    data.append(skills_by_years)
    ax: Axes = sub[0]
    x = [i for i in reversed(top_skills.keys())]
    y = [i for i in reversed(top_skills.values())]
    width = 0.3
    ylable = np.arange(0, max(y) + 1, max(max(y) // 10, 1))
    ax.barh(x, y, width)
    ax.set_xticks(ylable)
    ax.set_title(f'Топ 20 навыков за все время{vac}')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    set_font_size(ax, 8)

    for i, year in enumerate(skills_by_years.keys()):
        ax: Axes = sub[i + 1]
        x = [i for i in reversed(skills_by_years[year].keys())]
        y = [i for i in reversed(skills_by_years[year].values())]
        width = 0.3
        try:
            ylable = np.arange(0, max(y) + 1, max(max(y) // 10, 1))
            ax.barh(x, y, width)
            ax.set_xticks(ylable)
            ax.set_title(f'Топ 20 навыков за {year}{vac}')
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            set_font_size(ax, 8)
        except Exception as e:
            print(x, y)
            print(e)

    return fig, sub, data


def save_results(vacancies, vac):
    figure, sub, data = demand_create_plot(vacancies, vac)
    figure.savefig('graphs/demand.png')

    data_year_keys = list(zip(*list(data[0][0].items())[::-1]))
    data_year_keys = [data_year_keys[0][::-1], data_year_keys[1][::-1]]

    data_year_keys_filtered = tuple(zip(*list(data[0][1].items())[::-1]))
    data_year_keys_filtered = [data_year_keys_filtered[0][::-1], data_year_keys_filtered[1][::-1]]

    data_year_values = tuple(zip(*list(data[1][0].items())[::-1]))
    data_year_values = [data_year_values[0][::-1], data_year_values[1][::-1]]

    data_year_values_filtered = tuple(zip(*list(data[1][1].items())[::-1]))
    data_year_values_filtered = [data_year_values_filtered[0][::-1], data_year_values_filtered[1][::-1]]

    figure, sub, data = geography_create_plot(vacancies, vac)
    figure.savefig('graphs/geography.png')

    level_sal_city = list(zip(*list(data[0][0].items())[::-1]))
    level_sal_city = [level_sal_city[0][::-1], level_sal_city[1][::-1]]

    count_sal_city = tuple(zip(*list(data[0][1].items())[::-1]))
    count_sal_city = [count_sal_city[0][::-1], count_sal_city[1][::-1]]

    level_sal_city_filtered = tuple(zip(*list(data[1][0].items())[::-1]))
    level_sal_city_filtered = [level_sal_city_filtered[0][::-1], level_sal_city_filtered[1][::-1]]

    count_sal_city_filtered = tuple(zip(*list(data[1][1].items())[::-1]))
    count_sal_city_filtered = [count_sal_city_filtered[0][::-1], count_sal_city_filtered[1][::-1]]

    figure, sub, data = skills_create_plot(vacancies, '', data_year_keys)
    figure.savefig('graphs/skills.png')
    top_skills = data[0]
    skills_by_years = data[1]

    figure, sub, data = skills_create_plot(
        vacancies[vacancies['name'].str.contains(vac, na=False, case=False)],
        ' для профессии инженер-программист', data_year_keys)
    figure.savefig('graphs/skills_filtered.png')
    top_skills_filtered = data[0]
    skills_by_years_filtered = data[1]

    with open('tables.txt', 'w', encoding='utf-8') as file:
        file.write("Динамика уровня зарплат по годам:\n")
        file.write(json.dumps(dict(zip(*data_year_keys))))
        file.write('\n')
        file.write("Динамика уровня зарплат по годам для профессии инженер-программист:\n")
        file.write(json.dumps(dict(zip(*data_year_keys_filtered)), ensure_ascii=False))
        file.write('\n')
        file.write("Динамика количества вакансий по годам:\n")
        file.write(json.dumps(dict(zip(*data_year_values))))
        file.write('\n')
        file.write("Динамика количества вакансий по годам для профессии инженер-программист:\n")
        file.write(json.dumps(dict(zip(*data_year_values_filtered))))
        file.write('\n')

        file.write('\n')
        file.write("Динамика уровня зарплат по городам:\n")
        json.dump(dict(zip(*level_sal_city)), file, ensure_ascii=False)
        file.write('\n')
        file.write("Доля вакансий по городам:\n")
        json.dump(dict(zip(*count_sal_city)), file, ensure_ascii=False)
        file.write('\n')
        file.write("Динамика уровня зарплат по городам для профессии инженер-программист:\n")
        json.dump(dict(zip(*level_sal_city_filtered)), file, ensure_ascii=False)
        file.write('\n')
        file.write("Доля вакансий по городам для профессии инженер-программист:\n")
        json.dump(dict(zip(*count_sal_city_filtered)), file, ensure_ascii=False)
        file.write('\n')

        file.write('\n')
        file.write("Топ 20 навыков:\n")
        json.dump(top_skills, file, ensure_ascii=False)
        file.write('\n')
        file.write("Топ 20 навыков по годам:\n")
        json.dump(skills_by_years, file, ensure_ascii=False)
        file.write('\n')

        file.write('\n')
        file.write("Топ 20 навыков для профессии инженер-программист:\n")
        json.dump(top_skills_filtered, file, ensure_ascii=False)
        file.write('\n')
        file.write("Топ 20 навыков по годам для профессии инженер-программист:\n")
        json.dump(skills_by_years_filtered, file, ensure_ascii=False)
        file.write('\n')


def create_analytics():
    csv = 'vacancies.csv'
    vac = ('engineer|инженер программист|інженер|it инженер|инженер '
           'разработчик|программист-инженер|инженер-программист|инженер-разработчик')
    vacancies = parse_csv(csv)
    save_results(vacancies, vac)


create_analytics()
