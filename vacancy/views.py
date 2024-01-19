import json2html
from django.shortcuts import render
from vacancy.models import *


def index_page(request):
    return render(request, 'index.html')


def demand(request):
    try:
        tables = [(json2html.json2html.convert(json=i.table_content), i.name) for i in DemandTables.objects.all()]
        graph = Graphics.objects.get(name='demand').image
        return render(request, 'demand.html', {'data': tables, 'graph': graph})

    except Exception as e:
        print(e)
        return render(request, 'index.html')


def geography(request):
    try:
        tables = [(json2html.json2html.convert(json=i.table_content), i.name) for i in GeographyTables.objects.all()]
        graph = Graphics.objects.get(name='geography').image
        return render(request, 'geography.html', {'data': tables, 'graph': graph})

    except Exception as e:
        print(e)
        return render(request, 'index.html')


def skills(request):
    try:
        tables = [(json2html.json2html.convert(json=i.table_content), i.name) for i in SkillsTables.objects.all()]
        graph_skills = Graphics.objects.get(name='skills').image
        graph_skills_filtered = Graphics.objects.get(name='skills_filtered').image
        return render(request, 'skills.html', {
            'data': tables, 'graph_skills': graph_skills, 'graph_skills_filtered': graph_skills_filtered})

    except Exception as e:
        print(e)
        return render(request, 'skills.html')


def last_vacancies(request):
    return render(request, 'last_vacancies.html')
