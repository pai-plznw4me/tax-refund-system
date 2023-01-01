import os

import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from info.models import Info
from parser import calculate_workdate


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

        info_df = calculate_workdate(2018, filepath)
        info_df.drop(columns=['가상자격취득일', '가상자격상실일', '가상청년자격취득일', '가상청년자격상실일', '청년자격취득일', '청년자격상실일'], inplace=True)

        # db 저장
        infos = []
        for ind, row in info_df.iterrows():
            # 자격 상실이란
            info = Info.objects.create(
                filename=filepath,
                resident_code=row.iloc[0],
                name=row.iloc[1],
                acquisi_date=row.iloc[2],
                start_workyear='2018',

                workdate_1=row.iloc[4],
                workdate_2=row.iloc[5],
                workdate_3=row.iloc[6],
                workdate_4=row.iloc[7],
                workdate_5=row.iloc[8],
                total_workdate=row.iloc[9],

                young_workdate_1=row.iloc[10],
                young_workdate_2=row.iloc[11],
                young_workdate_3=row.iloc[12],
                young_workdate_4=row.iloc[13],
                young_workdate_5=row.iloc[14],
                total_young_workdate=row.iloc[15],
            )
            if not row['자격상실일'] == '근무중':
                info.disqual_date = row['자격상실일']

            info = list(Info.objects.filter(pk=info.pk).values())
            infos.extend(info)
        info_df = pd.DataFrame(infos)
        info_df.drop(columns='filename', inplace=True)
        htmls = info_df.to_html(table_id='workdate')
        context = {'htmls': htmls}

        return render(request, template_name='info/index.html', context=context)

    else:
        pass;
