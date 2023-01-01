import calendar
import pandas as pd
import numpy as np

"""
TODO: 
상시 근로 인정 예외 대상
    1. 임원 여부(제외), 
    2. 1년 미만 계약직(제외)

청년 인정기간에 제한이 없는 대상 및 청년인정기간 추가 대상
    1. 장애인 여부(청년 인정 기간 평생) 
    2. 60세 이상(청년 인정 기간 평생)
    3. 군 복무 기간(추가 대상)
"""


def load_workdate(path):
    """
        사업자가입명부를 로드 합니다.
    :param str path:
    :return:
    """

    # 엑셀 파일 로드
    xls = pd.ExcelFile(path)
    sheets = xls.sheet_names
    sheet = sheets[0]
    sh_df = xls.parse(sheet_name=sheet)
    df = sh_df.iloc[1:, -4:]
    return df


def get_dates_by_month(start_date, end_date, option='end'):
    """
    지정된 기간내 달 단위로 날짜 정보를 제공합니다.

    :param str start_date: yyyy-mm-dd
    :param str end_date: yyyy-mm-dd
    :param option:
     1) end : 매달 마지막 날 정보를 제공
     2) start : 매달 첫번째 날 정보를 제공

    :return:
    """
    if option == 'end':
        dates = list(pd.date_range(start=start_date, end=end_date, freq='MS'))
        for ind, date in enumerate(dates):
            dd = calendar.monthrange(date.year, date.month)[1]
            date = pd.to_datetime(date.date().replace(day=dd))
            dates[ind] = date
    elif option == 'start':
        # day 을
        dates = list(map(pd.to_datetime, pd.date_range(start=start_date, end=end_date, freq='MS')))
    else:
        raise NotImplementedError
    return dates


def check_workdate(start_date, end_date, acquisi_date, disqual_date):
    """
    Description:
        시작날짜와 종료 날짜 사이에 해당 인원이 근무 했는지를 파악합니다.

    Args:
        :param datetime start_date: 시작 날짜
        :param datetime end_date: 종료 날짜
        :param DataFrame.Series acquisi_date:
        :param DataFrame.Series disqual_date:

    :return DataFrame:
        지정된 기간동안에 각 달(month)별로 근무 날짜가 check 되어 있는 table
        example)
    """

    # 지정된 기간내 마지막 날짜 추출
    dates = get_dates_by_month(start_date, end_date, option='end')

    # 각 년도의 마지막날을 기준으로 자격취득이 해당 날짜를 기준으로 이전에 입사했고 해당 날짜를 기준으로 이후에 퇴사했으면 True 아니면 False 을 준다.
    calendar_df = pd.DataFrame()
    for date in dates:
        mask = (acquisi_date <= date) & (disqual_date >= date)
        calendar_df[date] = mask
    return calendar_df


def calculate_workdate(start_year, path):
    """
    Description:
        사업자기입명부를 읽어 상시근로날짜와 청년근로날짜를 계산한 정보를 제공한다.

    :param int start_year: 시작 날짜, 해당 년도로 부터 5개년치 근무 날짜를 계산한다.
    :param str path: 사업자가입명부
    example) ./data/사업장가입자명부_20221222 (상실자포함).xls
    :return DataFrame:
    """

    # 엑셀 파일 로드
    xls = pd.ExcelFile(path)
    sheets = xls.sheet_names
    for sheet in sheets:
        sh_df = xls.parse(sheet_name=sheet)
        target_df = sh_df.iloc[1:, -4:]

        # to datetime
        target_df.iloc[:, -1] = pd.to_datetime(target_df.iloc[:, -1])
        target_df.iloc[:, -2] = pd.to_datetime(target_df.iloc[:, -2])

        # 자격 취득일 / 자격 상실일
        acquisi_date = target_df.iloc[:, -2]
        disqual_date = target_df.iloc[:, -1]

        # 현재날짜, 기준시작날짜, 기준종료날짜
        gap = 5
        today = pd.Timestamp.today()
        start_date = today.date().replace(year=start_year, month=1, day=1)  # 기준 시작 날짜
        end_date = today.date().replace(year=start_year + gap - 1, month=12, day=31)  # 기준 종료 날짜
        start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

        # filter
        # 현재 년도 1월 1일부터 5년전 1월 1일 정보만을 가져온다. filter 된 데이터는 2017.1.1 일 이후 하루라도 근무함을 보증 한다.
        mask = disqual_date < start_date
        target_df = target_df.loc[~mask]

        # 상시 근무 날짜를 계산한다.
        target_df['가상자격취득일'] = start_date
        target_df['가상자격상실일'] = disqual_date.fillna(today)
        # 2017.1.1 보다 늦게 자격을 취득했다면 그대로 두고 2017.1.1 보다 일찍 자격을 취득했다면 2017.1.1 로 변경한다.
        mask = target_df['자격취득일'] > start_date
        target_df['가상자격취득일'].loc[mask] = target_df['자격취득일'].loc[mask]

        # 각 연도별 근무 날짜를 추출한다.
        # 말일 기준이면 + 을 한다. 1월은 31일까지 존재한다고 했을때 1월 29일날 근무를 시작해도 +1 을 해야 한다.
        # 각 년도의 마지막날을 가져온다.
        dates = []
        years = range(int(start_date.year), int(end_date.year) + 1)
        for yy in years:
            for mm in range(1, 12 + 1):
                dd = calendar.monthrange(yy, mm)[1]
                date = '{}-{}-{}'.format(yy, mm, dd)
                dates.append(pd.to_datetime(date))

        # 각 년도의 마지막날을 기준으로 자격취득이 해당 날짜를 기준으로 이전에 입사했고 해당 날짜를 기준으로 이후에 퇴사했으면 True 아니면 False 을 준다.
        calendar_df = pd.DataFrame()
        calendar_df['이름'] = target_df.iloc[:, 1]
        for date in dates:
            mask = (target_df['가상자격취득일'] <= date) & (target_df['가상자격상실일'] >= date)
            calendar_df[date] = mask
        # 각 년도별 근무 날짜를 취합합니다.
        for ind, year in enumerate(years):
            sliced_calendar = calendar_df.iloc[:, 1 + (ind * 12):((ind + 1) * 12) + 1]  # +1 은 가장 앞단에 이름이 들어 있음
            a = sliced_calendar.values.sum(axis=1)
            target_df['상시_' + str(year)] = a
            print('{} : {}'.format(year, target_df['상시_' + str(year)].sum()))

        # 상시 총 근무 날짜 집계
        total_workdate = target_df.iloc[:, 6:].values.sum(axis=1)
        target_df['상시총근무날짜'] = total_workdate

        # 생년 월일을 계산한다.
        birth_date = target_df.iloc[:, 0].map(lambda x: x[:6])
        birth_index = target_df.iloc[:, 0].map(lambda x: x[7]).map(int)
        prefix_mask = birth_index < 3
        birth_date.loc[prefix_mask] = birth_date.loc[prefix_mask].map(lambda x: '19' + str(x))
        birth_date.loc[~prefix_mask] = birth_date.loc[~prefix_mask].map(lambda x: '20' + str(x))

        # 2017년 이후 청년을 유지하는 인력만을 가져온다. 청년 근무 날짜를 계산한다. 현재 날짜로 부터 만 30세가 되는 날짜를 계산한다.
        young_offset = 30
        target_df['청년자격취득일'] = pd.to_datetime(birth_date)
        target_df['청년자격상실일'] = target_df['청년자격취득일'] + pd.DateOffset(years=young_offset)
        young_df = target_df.loc[target_df['청년자격상실일'] >= start_date]
        old_df = target_df.loc[target_df['청년자격상실일'] < start_date]

        # 퇴사자 중 퇴사날짜가 청년자격상실일보다 일찍 퇴사 날짜 했으면 해당 날짜가 청년자격상실실일로 된다.
        mask = ~young_df['자격상실일'].isna()
        mask_ = young_df['청년자격상실일'].loc[mask] > young_df['자격상실일'].loc[mask]
        # target_df['청년자격상실일'].loc[mask].loc[mask_] = target_df['자격상실일'].loc[mask].loc[mask_] # Not working
        true_mask = mask_[mask_]
        young_df['청년자격상실일'].loc[true_mask.index] = young_df['자격상실일'].loc[true_mask.index]

        # 가상청년자격취득일은 가상자격취득일과 동일
        young_df['가상청년자격취득일'] = young_df['가상자격취득일']

        # 청년자격상실날짜가 기준자격상실날짜보다 이후이면 기준자격상실날짜로 변경, 아니면 청년자격상실날짜
        young_df['가상청년자격상실일'] = young_df['청년자격상실일']
        young_df['가상청년자격상실일'].loc[young_df['가상청년자격상실일'] > today] = today

        # 각 년도의 마지막날을 기준으로 자격취득이 해당 날짜를 기준으로 이전에 입사했고 해당 날짜를 기준으로 이후에 퇴사했으면 True 아니면 False 을 준다.
        calendar_df = pd.DataFrame()
        calendar_df['이름'] = young_df.iloc[:, 1]
        for date in dates:
            mask = (young_df['가상청년자격취득일'] <= date) & (young_df['가상청년자격상실일'] >= date)
            calendar_df[date] = mask
        # 각 년도별 근무 날짜를 취합합니다.
        for ind, year in enumerate(years):
            sliced_calendar = calendar_df.iloc[:, 1 + (ind * 12):((ind + 1) * 12) + 1]  # +1 은 가장 앞단에 이름이 들어 있음
            a = sliced_calendar.values.sum(axis=1)
            young_df['청년_' + str(year)] = a
            print('{} : {}'.format(year, young_df['청년_' + str(year)].sum()))

        # 청년 총 근무 날짜 집계
        total_young_workdate = young_df.iloc[:, -5:].values.sum(axis=1)
        young_df['청년총근무날짜'] = total_young_workdate

        # young_df 와 target df 을 하나로 합침, 청년이 아니면 청년 근무날짜를 모두 NaN 이 나오도록 설정
        dropped_target_df = target_df.drop(index=young_df.index, axis=0, inplace=False)
        target_df = pd.concat([dropped_target_df, young_df], axis=0)
        target_df.rename(columns={target_df.columns[0]: '주민등록번호',
                                  target_df.columns[1]: '이름'}, inplace=True)

        target_df['자격상실일'] = target_df['자격상실일'].fillna('근무중')
        target_df.iloc[:, -8:] = target_df.iloc[:, -8:].fillna(0)
        # 결과 반환

        # 청년 유예
        """
        군복무를 다녀오면 해당 기간동안은 청년 개월수를 연장 시켜준다.
        2017년에 10개월을 일했고 실제 청년기간이 끝났다라고 해보자
        그랬을때 2018년에도 2017년도의 청년 기간이 10이라고 인정을 해주는 것. 
        """

        return target_df


def sum_by_yaer(calendar_df, years):
    """
    Description:

    :param DataFrame calendar_df:
    :param list years: [int, int, ... int ]
    :return DataFrame:
        columns : years
        index : calendar_df.index
        values : 각 년도별 일한 개월 수

    """
    # 각 년도별 근무 날짜를 취합합니다.
    totalwork_df = pd.DataFrame()
    calendar_years = calendar_df.columns.map(lambda x: x.year)
    for ind, year in enumerate(years):
        # 각 년도에 해당 하는 column 을 추출합니다.
        mask = (calendar_years == year)
        sliced_df = calendar_df.loc[:, mask]

        # 각 년도별로 일한 날짜를 더해 제공합니다.
        total_works = sliced_df.values.sum(axis=1)
        totalwork_df[year] = total_works

    return totalwork_df


if __name__ == '__main__':
    import pandas as pd

    date1 = "2017-01-01"  # input start date
    date2 = "2022-12-31"  # input end date
    month_list = [i.strftime("%y-%m") for i in pd.date_range(start=date1, end=date2, freq='MS')]
    print(month_list)

    df = load_workdate('./data/사업장가입자명부_20221222 (상실자포함).xls')

    # 상시 근무 날짜를 측정합니다.
    acquisi_date = pd.to_datetime(df.iloc[:, -2])
    disqual_date = pd.to_datetime(df.iloc[:, -1]).fillna(pd.Timestamp.today())
    workdate_df = check_workdate("2017-01-01", "2022-12-31", acquisi_date, disqual_date)
    workdate_sum_df = sum_by_yaer(workdate_df, [2018, 2019, 2020, 2021, 2022])

    # 청년 근무 날짜를 측정 합니다.
    # 청년 근무 날짜를 계산합니다.
    young_acquisi_date = pd.to_datetime(df.iloc[:, -2])
    young_disqual_date = pd.to_datetime(df.iloc[:, -1]).fillna(pd.Timestamp.today())
