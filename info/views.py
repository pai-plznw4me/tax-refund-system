import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from parser import load_workdate, generate_workdate, get_deductions, calculate_deduction_sum, \
    calculate_tax_sum, extend_workdate_sum


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
        # 상시근로표, 청년근로표, 기타근로표를 생성해 반환합니다,
        workdate_df, workdate_sum_df, young_workdate_df, young_workdate_sum_df = \
            generate_workdate(employee_df, start_date, end_date, curr_date)
        etc_workdate_sum_df = pd.DataFrame(workdate_sum_df.values - young_workdate_sum_df.values,
                                           index=workdate_df.index,
                                           columns=['(기타)' + str(year) for year in years])

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

        # 최초 공제 별 1. 공제 적용 여부 테이블, 2. 최초 공제 정보 추출
        deduction_tables, first_deduction_info_df = get_deductions(n_youngs, n_etc, True, years)

        # 최초 공제별 청년 근로자, 기타 근로자 연도별 근무 달(month)
        deduction_yng_workdate_sums = []
        deduction_etc_workdate_sums = []
        extend_yng_workdate_sums = []
        extend_etc_workdate_sums = []

        # 총합 공제 금액 계산
        target_year = years[-1]
        deduction = calculate_deduction_sum(deduction_tables, target_year)

        # 최초 공제 중 해당년도(2022)와 2년전(2020) 사이 최초 공제를 찾아 반환합니다.
        target_mask = first_deduction_info_df['year'] >= target_year - 2
        target_deduction_index = target_mask[target_mask].index  # 타겟 공제 인덱스 추출
        target_info_df = first_deduction_info_df.loc[target_mask]

        # 해당 (2020, 2021, 2022) 최초 공제 별 청년 / 기타 유예
        for (_, row), deduction_index in zip(target_info_df.iterrows(), target_deduction_index):
            year = row['year']
            year_index = row['year_index']

            # 최초 공제별 청년 유예 근로자 연도별 근무 달 수
            deduction_yng_workdate_sum = young_workdate_sum_df.iloc[:, year_index:]
            deduction_yng_workdate_sums.append(deduction_yng_workdate_sum)

            # 최초 공제별 기타 유예 근로자 연도별 근무 달 수
            deduction_etc_workdate_sum = etc_workdate_sum_df.iloc[:, year_index:]
            deduction_etc_workdate_sums.append(deduction_etc_workdate_sum)

            # 청년, 기타 유예 연도별 근 무 달수
            extend_young_workdate_sum_df, extend_etc_workdate_sum_df = extend_workdate_sum(deduction_yng_workdate_sum,
                                                                                           deduction_etc_workdate_sum)
            extend_yng_workdate_sums.append(extend_young_workdate_sum_df)
            extend_etc_workdate_sums.append(extend_etc_workdate_sum_df)

            # 최초 공제 받은 시기보다 청년 근로 달수가 감소 했는지를 check 합니다.
            mask = extend_young_workdate_sum_df.sum() - extend_young_workdate_sum_df.sum()[0] >= 0
            # 청년 근로 달(Month) 수 감소시 if 구문 수행
            if not mask.all():
                deduction_tables[deduction_index][target_year] = -1

        # 추가 납무 금액 계산
        tax = calculate_tax_sum(deduction_tables, target_year)
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
