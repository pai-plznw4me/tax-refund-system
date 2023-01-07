import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from parser import load_workdate, generate_workdate, get_deductions, calculate_deduction_sum, \
    calculate_tax_sum


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

        # 사업자가입자명부를 로드합니다.
        employee_df = load_workdate(filepath)
        name = employee_df.iloc[:, 1]  # 이름
        start_date = '2018-01-01'
        end_date = '2022-12-31'
        curr_date = pd.Timestamp.today()
        years = list(range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1))

        # 상시근로표, 청년근로표 를 생성해 반환합니다,
        workdate_df, workdate_sum_df, young_workdate_df, young_workdate_sum_df = \
            generate_workdate(employee_df, start_date, end_date, curr_date)

        #  상시근로, 청년근로 총 인원수를 계산합니다.
        table_df = pd.concat([name, workdate_sum_df, young_workdate_sum_df], axis=1)
        total = table_df.sum(axis=0)
        total.iloc[0] = '합계'
        total.name = '합계'
        table_df = table_df.append(total)

        # 청년 근로 및 기타 근로자 수를 계산합니다.
        n_workers = total[1:1 + 5].values
        n_youngs = total[1 + 5:1 + 5 + 5].values
        n_etc = n_workers - n_youngs

        # 공제, 추가 납부를 계산합니다.
        deductions = get_deductions(n_youngs, n_etc, True, years)

        # 총합 공제 금액 계산
        deduction = calculate_deduction_sum(deductions, year)

        # 공제 금액 반납
        tax = calculate_tax_sum(deductions, year)
        print('2022년 공제 받은 금액 : {} \n2022년 추가 납부 금액 : {}'.format(deduction, tax))

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
