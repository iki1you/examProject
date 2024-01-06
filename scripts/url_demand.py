import re
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus.tables import Table
from reportlab.lib import colors


def get_medium(x):
    if x['salary_from'].equals(x['salary_to']):
        return x['salary_from']
    return (x['salary_from'] + x['salary_to']) / 2


def get_year_vacancy(s):
    for j in re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4}', s):
        s = s.replace(j, j[0:4])
    return int(s)


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


def parse_csv(csv):
    names = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
    vacancies = (pd.read_csv(csv, names=names)
                 .assign(salary_from=lambda x: x['salary_from'].fillna(x['salary_to']))
                 .assign(salary_to=lambda x: x['salary_to'].fillna(x['salary_from']))
                 .assign(published_at=lambda x: x['published_at'].apply(get_year_vacancy))
                 .assign(count=0)
                 .assign(medium_salary=get_medium))
    return vacancies


def create_plot():
    csv = 'vacancies.csv'
    vac = 'engineer|инженер программист|інженер|it инженер|инженер разработчик'
    vacancies = parse_csv(csv)
    data = []
    fig, sub = plt.subplots(2, 1, figsize=(8, 10))
    vac_by_years = get_vac_by_years(vacancies)['medium_salary'].to_dict()
    vac_by_years_filtered = get_vac_by_years(vacancies[vacancies['name']
                                             .str.contains(vac, na=False, case=False)])['medium_salary'].to_dict()
    vac_by_years = dict([(key, value) for key, value in vac_by_years.items() if key in vac_by_years_filtered])
    data.append((vac_by_years, vac_by_years_filtered))
    ax: Axes = sub[0]
    xlable = range(min(vac_by_years_filtered.keys()), max(vac_by_years_filtered.keys()) + 1)
    print(vac_by_years_filtered)
    x = np.arange(len(xlable))

    y = [i for i in vac_by_years.values()]
    y2 = [i for i in vac_by_years_filtered.values()]
    width = 0.3
    ax.bar(x - width/2, y, width, label='средняя з/п')
    ax.bar(x + width/2, y2, width, label=f'з/п {vac}')
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
    y2 = [i for i in vac_by_years_filtered.values()]
    ax.bar(x - width / 2, y, width, label='Количество вакансий')
    ax.bar(x + width / 2, y2, width, label=f'Количество вакансий {vac}')

    ax.set_title('Количество вакансий по годам')
    ax.set_xticks(x)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right')
    ax.set_xticklabels(xlable)
    set_font_size(ax, 8)
    ax.legend(fontsize=12)
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
    c = canvas.Canvas("Figures.pdf")
    fname = 'a010013l'

    # faceName - view a010013l.AFM file as a plain text and look at
    # row beginning with 'FontName' word (it's usually the fourth row).
    # The word after 'FontName' is the faceName ('URWGothicL-Book' in this case).
    faceName = 'URWGothicL-Book'

    # Define new Type 1 font
    cyrFace = pdfmetrics.EmbeddedType1Face(fname + '.afm', fname + '.pfb')

    # Create a new encoding called 'CP1251'
    cyrenc = pdfmetrics.Encoding('CP1251')

    # Fill in the tuple with Unicode glyphs in accordance with cp1251 (win1251)
    # encoding
    cp1251 = (
        'afii10051', 'afii10052', 'quotesinglbase', 'afii10100', 'quotedblbase',
        'ellipsis', 'dagger', 'daggerdbl', 'Euro', 'perthousand', 'afii10058',
        'guilsinglleft', 'afii10059', 'afii10061', 'afii10060', 'afii10145',
        'afii10099', 'quoteleft', 'quoteright', 'quotedblleft', 'quotedblright',
        'bullet', 'endash', 'emdash', 'tilde', 'trademark', 'afii10106',
        'guilsinglright', 'afii10107', 'afii10109', 'afii10108', 'afii10193',
        'space', 'afii10062', 'afii10110', 'afii10057', 'currency', 'afii10050',
        'brokenbar', 'section', 'afii10023', 'copyright', 'afii10053',
        'guillemotleft', 'logicalnot', 'hyphen', 'registered', 'afii10056',
        'degree', 'plusminus', 'afii10055', 'afii10103', 'afii10098', 'mu1',
        'paragraph', 'periodcentered', 'afii10071', 'afii61352', 'afii10101',
        'guillemotright', 'afii10105', 'afii10054', 'afii10102', 'afii10104',
        'afii10017', 'afii10018', 'afii10019', 'afii10020', 'afii10021',
        'afii10022', 'afii10024', 'afii10025', 'afii10026', 'afii10027',
        'afii10028', 'afii10029', 'afii10030', 'afii10031', 'afii10032',
        'afii10033', 'afii10034', 'afii10035', 'afii10036', 'afii10037',
        'afii10038', 'afii10039', 'afii10040', 'afii10041', 'afii10042',
        'afii10043', 'afii10044', 'afii10045', 'afii10046', 'afii10047',
        'afii10048', 'afii10049', 'afii10065', 'afii10066', 'afii10067',
        'afii10068', 'afii10069', 'afii10070', 'afii10072', 'afii10073',
        'afii10074', 'afii10075', 'afii10076', 'afii10077', 'afii10078',
        'afii10079', 'afii10080', 'afii10081', 'afii10082', 'afii10083',
        'afii10084', 'afii10085', 'afii10086', 'afii10087', 'afii10088',
        'afii10089', 'afii10090', 'afii10091', 'afii10092', 'afii10093',
        'afii10094', 'afii10095', 'afii10096', 'afii10097'
    )

    # Replace glyphs from code 128 to code 256 with cp1251 values
    for i in range(128, 256):
        cyrenc[i] = cp1251[i - 128]

    pdfmetrics.registerEncoding(cyrenc)

    # Register type face
    pdfmetrics.registerTypeFace(cyrFace)

    # Register the font with adding '1251' to its name
    pdfmetrics.registerFont(pdfmetrics.Font(faceName + '1251', faceName, 'CP1251'))

    # Use this font and set font size
    c.setFont(faceName + '1251', 90)

    c.setTitle("Figures")
    height = 6
    image = BytesIO()
    figure.savefig(image, format="png")
    image.seek(0)
    image = ImageReader(image)
    figure_size = figure.get_size_inches() * 2.54
    c.drawImage(image, (10.5 - figure_size[0] / 2) * cm, height * cm,
                figure_size[0] * cm, figure_size[1] * cm)

    data_year_keys = list(zip(*list(data[0][0].items())[::-1]))
    data_year_keys = [data_year_keys[0][::-1], data_year_keys[1][::-1]]

    text = c.beginText(10, 210)
    c.setFontSize(8)
    text.textLine("Динамика уровня зарплат по годам")
    c.drawText(text)

    table = Table(data_year_keys, colWidths=35, rowHeights=16, style=[
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ])
    table.wrapOn(c, 100, 100)
    table.drawOn(c, 20, 170)

    text = c.beginText(10, 110)
    c.setFontSize(8)
    text.textLine("Динамика уровня зарплат по годам для профессии инженер-программист")
    c.drawText(text)

    data_year_keys_filtered = tuple(zip(*list(data[0][1].items())[::-1]))
    data_year_keys_filtered = [data_year_keys_filtered[0][::-1], data_year_keys_filtered[1][::-1]]
    table = Table(data_year_keys_filtered, colWidths=35, rowHeights=16, style=[
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ])
    table.wrapOn(c, 0, 130)
    table.drawOn(c, 20, 70)

    text = c.beginText(10, 157)
    c.setFontSize(8)
    text.textLine("Динамика количества вакансий по годам")
    c.drawText(text)

    data_year_values = tuple(zip(*list(data[1][0].items())[::-1]))
    data_year_values = [data_year_values[0][::-1], data_year_values[1][::-1]]
    table = Table(data_year_values, colWidths=35, rowHeights=16, style=[
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ])
    table.wrapOn(c, 0, 130)
    table.drawOn(c, 20, 120)

    text = c.beginText(10, 60)
    c.setFontSize(8)
    text.textLine("Динамика количества вакансий по годам для профессии инженер-программист")
    c.drawText(text)

    data_year_values_filtered = tuple(zip(*list(data[1][1].items())[::-1]))
    data_year_values_filtered = [data_year_values_filtered[0][::-1], data_year_values_filtered[1][::-1]]
    table = Table(data_year_values_filtered, colWidths=35, rowHeights=16, style=[
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ])
    table.wrapOn(c, 0, 130)
    table.drawOn(c, 20, 20)

    c.save()


create_pdf()
