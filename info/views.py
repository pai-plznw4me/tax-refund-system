import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from parser import load_workdate, generate_workdate, get_deductions, calculate_deduction_sum, \
    calculate_tax_sum, extend_workdate_sum, filter_valid_deductions, df2excel, filter_valid_tax, deductio_and_tax


@csrf_exempt
def index(request):
    if request.method == 'GET':
        return render(request, template_name='info/index.html')

    elif request.method == 'POST':

        # 파일 저장
        company_name = request.POST.get('company')
        year = int(request.POST.get('year'))
        employee = request.FILES.getlist('employee')[0]

        # File 저장
        dirpath = './media'
        fs = FileSystemStorage(location=dirpath)
        filename = fs.save(employee.name, employee)
        filepath = os.path.join(dirpath, filename)

        deduction, tax, table_df = deductio_and_tax(filepath, None)

        context = {'table_df': table_df,
                   'company_name': company_name,
                   'target_year': year,
                   'deduction': deduction,
                   'tax': tax,
                   'filename': filename}
        return render(request, template_name='info/index.html', context=context)


def logout(request):
    return ""


def graph(request):
    context = {'segment': 'graph'}

    html_template = loader.get_template('visualization/graph.html')
    return HttpResponse(html_template.render(context, request))


@csrf_exempt
def download(request):
    # 파일 저장
    company_name = request.POST.get('company')
    year = int(request.POST.get('year'))
    employee = request.FILES.getlist('employee')[0]

    # 사업자 가 명부 파일 저장
    dirpath = './media'
    fs = FileSystemStorage(location=dirpath)
    filename = fs.save(employee.name, employee)
    filename_ext = os.path.splitext(filename)[-1]
    filepath = os.path.join(dirpath, filename)

    #
    save_name = company_name + '{}'.format(filename_ext)
    save_path = os.path.join(dirpath, save_name)
    deduction, tax, table_df = deductio_and_tax(filepath, save_path=save_path)
    fs = FileSystemStorage(dirpath)
    response = FileResponse(fs.open(save_name, 'rb'), content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(save_name).encode('utf-8')
    return response
