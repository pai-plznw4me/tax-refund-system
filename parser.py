"""

상시 근로 인정 예외 대상
    1. 임원 여부(제외),
    2. 1년 미만 계약직(제외)

청년 인정기간에 제한이 없는 대상 및 청년인정기간 추가 대상
    1. 장애인 여부(청년 인정 기간 평생)
    2. 60세 이상(청년 인정 기간 평생)
    3. 군 복무 기간(추가 대상)
"""

import calendar
import numpy as np
import pandas as pd


def load_workdate(path):
    """
    Description:
        사업자가입명부 엑셀 파일을 로드 합니다.

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
    Description:
        지정된 기간내 달 단위로 날짜 정보(yyyy-mm-dd)를 제공합니다.

    Args:
        :param str start_date: yyyy-mm-dd
        :param str end_date: yyyy-mm-dd
        :param option:
         1) end : 매달 마지막 날 정보를 제공
         2) start : 매달 첫번째 날 정보를 제공

    :list return:
     [yyyy-mm-dd, yyyy-mm-dd, ... yyyy-mm-dd]

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
        시작날짜와 종료날짜 사이 각 달에 해당 인원이 근무 했는지를 파악합니다.

    Args:
        :param datetime start_date: 시작 날짜
        :param datetime end_date: 종료 날짜
        :param DataFrame.Series acquisi_date:
        :param DataFrame.Series disqual_date:

    :return DataFrame:
        지정된 기간동안에 각 달(month)별로 근무 여부가 check 되어 있는 table
    """

    # 지정된 기간내 마지막 날짜 추출
    dates = get_dates_by_month(start_date, end_date, option='end')

    # 각 년도의 마지막날을 기준으로 자격취득이 해당 날짜를 기준으로 이전에 입사했고 해당 날짜를 기준으로 이후에 퇴사했으면 True 아니면 False 을 준다.
    calendar_df = pd.DataFrame()
    for date in dates:
        mask = (acquisi_date <= date) & (disqual_date >= date)
        calendar_df[date] = pd.Series(mask)
    return calendar_df


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
    totalwork_df.index = calendar_df.index
    calendar_years = calendar_df.columns.map(lambda x: x.year)
    for ind, year in enumerate(years):
        # 각 년도에 해당 하는 column 을 추출합니다.
        mask = (calendar_years == year)
        sliced_df = calendar_df.loc[:, mask]

        # 각 년도별로 일한 날짜를 더해 제공합니다.
        total_works = sliced_df.values.sum(axis=1)
        totalwork_df[year] = total_works

    return totalwork_df


def resident2date(resident_codes):
    """
    Description:
        주민등록번호를 날짜로 변환합니다.
        뒷번호가 1, 2, 3, 4 여부에 따라 19년도 출생인지 20년도 출생인지가 결정 됩니다.
        주민등록번호 샘플: 900117-1xxxxxx

    :param pd.Series resident_codes:
    :return:
    """

    # 생년 월일을 계산한다.
    birth_date = resident_codes.map(lambda x: x[:6])
    birth_index = resident_codes.map(lambda x: x[7]).map(int)
    prefix_mask = birth_index < 3
    birth_date.loc[prefix_mask] = birth_date.loc[prefix_mask].map(lambda x: '19' + str(x))
    birth_date.loc[~prefix_mask] = birth_date.loc[~prefix_mask].map(lambda x: '20' + str(x))
    return birth_date


def military_period():
    """
    Description:
        각 인원별로 군 복무 기간을 반환합니다.
    Args:
    :Series return:

    """
    period = pd.Series(name='period', data=np.ones(shape=(103,))).astype(int)
    return period


def disable_calender(start_date, end_date, disable_workdate_df, curr_date, *disables):
    """
    Description:
        장애인 취득 시기를 calender 로 제공

    Args:
        :param str start_date: 'yyyy-mm-dd'
        :param str end_date: 'yyyy-mm-dd'
        :param DataFrame skeleton_df:
        :argument: 사용자 index 정보 및 장애인 자격 취득 시기, 장애인 자격 상실 시기 정보를 tuple 로 제공
            [(index, acquisi_date, disqual_date),  (index, acquisi_date, disqual_date) ... (index, acquisi_date, disqual_date)]
            example)
                [(0, '1989-04-20', '1989-05-20'), (0, '1989-01-01', None), (1, '1991-01-01', None), (2, '2018-07-20', None)]

        장애인 기간 복무 기간을 반환합니다.
    :DataFrame return:

    """

    for disable in disables:
        index, acquisi_date, disqual_date = disable
        if not disqual_date:
            disqual_date = curr_date
        disable_calendar_df = check_workdate(start_date,
                                             end_date,
                                             pd.to_datetime(acquisi_date),
                                             pd.to_datetime(disqual_date)).iloc[0]
        disable_workdate_df.loc[index, :] = disable_workdate_df.loc[index, :] | disable_calendar_df
    return disable_workdate_df


def parser():
    curr_date = pd.Timestamp.today()

    date1 = "2017-01-01"  # input start date
    date2 = "2022-12-31"  # input end date
    month_list = [i.strftime("%y-%m") for i in pd.date_range(start=date1, end=date2, freq='MS')]

    # index 는 각 개인 고유 번호(pk)이어야 한다.
    df = load_workdate('./data/사업장가입자명부_20221222 (상실자포함).xls')
    name = df.iloc[:, 1]
    # 상시 근무 날짜를 측정합니다.
    acquisi_date = pd.to_datetime(df.iloc[:, -2])
    disqual_date = pd.to_datetime(df.iloc[:, -1]).fillna(curr_date)
    workdate_df = check_workdate("2017-01-01", "2022-12-31", acquisi_date, disqual_date)
    workdate_sum_df = sum_by_yaer(workdate_df, [2018, 2019, 2020, 2021, 2022])

    # skelton dataframe
    skeleton_df = workdate_df.copy()
    skeleton_df.iloc[:] = False

    # 청년 근무 날짜를 측정 합니다.(군복무 기간 추가)
    young_offset = 30
    birth_date = pd.to_datetime(resident2date(df.iloc[:, 0]))
    young_disqual_date = birth_date + pd.DateOffset(years=young_offset)
    mask = disqual_date < young_disqual_date
    young_disqual_date.loc[mask] = disqual_date.loc[mask]

    # 청년 복무 기간에서 군대를 다녀온 기간을 추가로 제공합니다.
    period = pd.to_timedelta(military_period(), unit='D')
    period.index = young_disqual_date.index
    young_disqual_date = young_disqual_date + period
    young_workdate_df = check_workdate("2017-01-01", "2022-12-31", acquisi_date, young_disqual_date)
    young_workdate_sum_df = sum_by_yaer(young_workdate_df, [2018, 2019, 2020, 2021, 2022])
    young_df = pd.concat([name, acquisi_date, young_disqual_date, young_workdate_sum_df], axis=1)

    # 노인 근무 기간
    elder_offset = 60
    elder_acquisi_date = birth_date + pd.DateOffset(years=elder_offset)
    elder_disqual_date = elder_acquisi_date + pd.DateOffset(years=1000)
    elder_workdate_df = check_workdate("2017-01-01", "2022-12-31", elder_acquisi_date, elder_disqual_date)
    elder_workdate_sum_df = sum_by_yaer(elder_workdate_df, [2018, 2019, 2020, 2021, 2022])
    elder_df = pd.concat([name, elder_acquisi_date, elder_disqual_date, elder_workdate_sum_df], axis=1)

    # 장애인 기간
    disables = [(1, '1989-04-20', '1989-05-20'), (1, '1989-01-01', None), (2, '1991-01-01', None),
                (3, '2018-07-20', None)]
    disable_workdate_df = skeleton_df.copy()
    disable_workdate_df = disable_calender("2017-01-01", "2022-12-31", disable_workdate_df, curr_date, *disables)
    disable_workdate_sum_df = sum_by_yaer(disable_workdate_df, [2018, 2019, 2020, 2021, 2022])
    disable_df = pd.concat([name, disable_workdate_sum_df], axis=1)

    # 통합 근무 기간
    merged_workdate_df = young_workdate_df | disable_workdate_df | elder_workdate_df
    merged_workdate_sum_df = sum_by_yaer(merged_workdate_df, [2018, 2019, 2020, 2021, 2022])

    # 임직원 및 계약직 직원 제거
    excutive_indices = [2, 3, 4]
    contract_indices = [5, 6, 7]
    indices = list(set(contract_indices + excutive_indices))
    merged_workdate_sum_df.drop(index=indices, inplace=True)
    workdate_sum_df.drop(index=indices, inplace=True)
    name.drop(index=indices, inplace=True)

    # 연도별 상시 및 청년 근무 통합
    workdate_by_year = pd.concat([name, workdate_sum_df, merged_workdate_sum_df], axis=1)
    workdate_by_year_sum = workdate_by_year.iloc[:, 1:].sum(axis=0)

    return workdate_by_year
