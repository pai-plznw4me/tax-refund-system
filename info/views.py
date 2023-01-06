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
        my_file = request.FILES.getlist('file')[0]
        dirpath = './media'
        fs = FileSystemStorage(location=dirpath)
        filename = fs.save(my_file.name, my_file)
        filepath = os.path.join(dirpath, filename)

        # 근무, 청년 근무 날짜 계산
        path = './data/사업장가입자명부_20221222 (상실자포함).xls'
        start_date = '2018-01-01'
        end_date = '2022-12-31'
        curr_date = pd.Timestamp.today()

        deduction_tax, refund_tax, calendar = deduction_and_tax(path, start_date, end_date, curr_date, True)
        htmls = calendar.to_html(table_id='workdate')
        context = {'htmls': htmls}

        return render(request, template_name='info/index.html', context=context)


def logout(request):
    return ""


def graph(request):
    context = {'segment' : 'graph'}
    html_template = loader.get_template('visualization/graph.html')
    return HttpResponse(html_template.render(context, request))