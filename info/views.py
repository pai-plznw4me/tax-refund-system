import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from parser import deduction_and_tax


@csrf_exempt
def index(request):
    if request.method == 'GET':
        return render(request, template_name='info/index.html')

    elif request.method == 'POST':
        # 파일 저장
        company_name = request.POST.get('company')
        year = request.POST.get('year')
        employee = request.FILES.getlist('employee')[0]
        disable = request.FILES.getlist('disable')
        army = request.FILES.getlist('army')
        executive = request.FILES.getlist('executive')

        # File 저장
        dirpath = './media'
        fs = FileSystemStorage(location=dirpath)
        file_paths = []
        filename = fs.save(employee.name, employee)
        filepath = os.path.join(dirpath, filename)
        file_paths.append(filepath)

        # 근무, 청년 근무 날짜 계산
        path = file_paths[0]
        start_date = '2018-01-01'
        end_date = '2022-12-31'
        curr_date = pd.Timestamp.today()

        # 세금 계산
        deduction, tax, table_df = deduction_and_tax(path, start_date, end_date, curr_date, True)
        table_df = table_df
        context = {'table_df': table_df,
                   'company_name': company_name,
                   'target_year': year,
                   'deduction': deduction,
                   'tax': tax, }

        return render(request, template_name='info/index.html', context=context)


def logout(request):
    return ""


def graph(request):
    context = {'segment': 'graph'}

    html_template = loader.get_template('visualization/graph.html')
    return HttpResponse(html_template.render(context, request))
