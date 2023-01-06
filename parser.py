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
    :Dateframe return:
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
        example)
            +--------+----------+----------+----------+----------+--------+
            |        | 2018.1.1 | 2018.1.2 | 2018.1.3 | 2018.1.4 | 2018.1.5|
            +--------+----------+----------+----------+----------+--------+
            | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
            +--------+----------+----------+----------+----------+--------+
            | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
            +--------+----------+----------+----------+----------+--------+

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
    :datetime return: yyyymmdd

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
        :param DataFrame disable_workdate_df:
        :argument: 사용자 index 정보 및 장애인 자격 취득 시기, 장애인 자격 상실 시기 정보를 tuple 로 제공
            [(index, acquisi_date, disqual_date),  (index, acquisi_date, disqual_date) ... (index, acquisi_date, disqual_date)]
            example)
                [(0, '1989-04-20', '1989-05-20'), (0, '1989-01-01', None), (1, '1991-01-01', None), (2, '2018-07-20', None)]

        지정된 기간내 장애인 기간 복무 기간을 체크해 반환합니다.
    :DataFrame return:
        example)
            +--------+----------+----------+----------+----------+--------+
            |        | 2018.1.1 | 2018.1.2 | 2018.1.3 | 2018.1.4 | 2018.1.5|
            +--------+----------+----------+----------+----------+--------+
            | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
            +--------+----------+----------+----------+----------+--------+
            | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
            +--------+----------+----------+----------+----------+--------+


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


def generate_work_calendar(path, start_date, end_date, curr_date):
    """
    Description:
        각 인원별, 각 년도별 상시 근로자와 청년 근로자 총 근무 달수를 계산해 반환합니다.
        ⚠️ Warning : 210살 이상 생존한 사람이 있다면 해당 기능에 문제가 생길수 있습니다.

    Args:
        :param str path: ex) './data/사업장가입자명부_20221222 (상실자포함).xls'
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param timestamp curr_date: yyyy-mm-dd, pd.Timestamp.today()

    :DataFrame return:
        example)
                +--------+--------+--------+--------+--------+--------+
                |        | 2018년 | 2019년 | 2020년 | 2021년 | 2022년 |
                +--------+--------+--------+--------+--------+--------+
                | 강대영 | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+--------+
                | 강혜진 | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+--------+

    """
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    years = list(range(start_year, end_year + 1))

    # index 는 각 개인 고유 번호(pk)이어야 한다.
    df = load_workdate(path)
    name = df.iloc[:, 1]
    dummy_date = pd.to_datetime('1800-01-01')

    # 상시 근무 날짜를 측정합니다.
    acquisi_date = pd.to_datetime(df.iloc[:, -2])
    disqual_date = pd.to_datetime(df.iloc[:, -1]).fillna(curr_date)
    workdate_df = check_workdate(start_date, end_date, acquisi_date, disqual_date)
    workdate_sum_df = sum_by_yaer(workdate_df, years)

    # skelton dataframe
    skeleton_df = workdate_df.copy()
    skeleton_df.iloc[:] = False

    # 청년 근무 날짜를 측정 합니다.(군복무 기간 추가)
    young_offset = 30
    birth_date = pd.to_datetime(resident2date(df.iloc[:, 0]))
    young_acquisi_date = birth_date
    young_disqual_date = birth_date + pd.DateOffset(years=young_offset)
    # 청년 복무 기간에서 군대를 다녀온 기간을 추가로 제공합니다.
    period = pd.to_timedelta(military_period(), unit='D')
    period.index = young_disqual_date.index
    young_disqual_date = young_disqual_date + period
    # 청년 인정 기간과 근무 기간 중 겹치는 기간을 계산합니다.
    intrsctn_young_acquisi_date, intrsctn_young_disqual_date = \
        intersection(acquisi_date, disqual_date, young_acquisi_date, young_disqual_date, dummy_date)
    young_workdate_df = check_workdate(start_date, end_date, intrsctn_young_acquisi_date, intrsctn_young_disqual_date)
    young_workdate_sum_df = sum_by_yaer(young_workdate_df, years)

    # 노인 근무 기간
    elder_offset = 60
    elder_acquisi_date = birth_date + pd.DateOffset(years=elder_offset)
    elder_disqual_date = elder_acquisi_date + pd.DateOffset(years=150)
    intrsctn_elder_acquisi_date, intrsctn_elder_acquisi_date = \
        intersection(acquisi_date, disqual_date, elder_acquisi_date, elder_disqual_date, dummy_date)
    elder_workdate_df = check_workdate(start_date, end_date, intrsctn_elder_acquisi_date, intrsctn_elder_acquisi_date)
    elder_workdate_sum_df = sum_by_yaer(elder_workdate_df, years)

    # 장애인 기간
    disables = [(1, '1989-04-20', '1989-05-20'), (1, '1989-01-01', None), (2, '1991-01-01', None),
                (3, '2018-07-20', None)]
    # 지정된 기간 동안 장애인 자격을 부여 받은 달에 대한 calendar 을 가져옵니다.
    disable_workdate_df = skeleton_df.copy()
    disable_workdate_df = disable_calender("2017-01-01", "2022-12-31", disable_workdate_df, curr_date, *disables)
    # 상시 근로한 달(month)중에 장애인 자격을 부여 받은 달(month)을 체크한 켈린더를 반환합니다.
    disable_workdate_df = disable_workdate_df & workdate_df
    disable_workdate_sum_df = sum_by_yaer(disable_workdate_df, years)

    # 통합 근무 기간
    merged_young_workdate = young_workdate_df | elder_workdate_df | disable_workdate_df
    merged_young_workdate_sum = sum_by_yaer(merged_young_workdate, years)

    # 임직원 및 계약직 직원 제거
    excutive_indices = [2, 3, 4]
    contract_indices = [5, 6, 7]
    indices = list(set(contract_indices + excutive_indices))
    merged_young_workdate_sum.drop(index=indices, inplace=True)
    workdate_sum_df.drop(index=indices, inplace=True)
    name.drop(index=indices, inplace=True)

    # 연도별 상시 및 청년 근무 통합
    workdate_by_year = pd.concat([name, workdate_sum_df, merged_young_workdate_sum], axis=1)
    return workdate_by_year


def get_diff(workers):
    """
    년도별 근로자 차이를 계산해 반환합니다.
    :param workers:
    :return:
    """
    rolled_workers = np.roll(workers, 1)
    diff = workers - rolled_workers
    diff[0] = 0
    return diff


def first_deduction(young_counts, etc_counts):
    """
    Description:
        최초 공제 정보를 계산해 반환합니다.

    :param ndarray young_counts: 연도별 청년 근로자, 값 순서는 연도순으로 나열되어 있어야 합니다.
    :param ndarray etc_counts: 연도별 기타 근로자
    :return:
        [[index, 청년 공제 증가, 기타 공제 증가],
         [index, 청년 공제 증가, 기타 공제 증가]]
    공제 증가 최소값은 0
    """
    yng_diff = get_diff(young_counts)
    etc_diff = get_diff(etc_counts)
    wkr_diff = yng_diff + etc_diff

    # 최초 공제 시기
    first_deduction_index = np.where(wkr_diff > 0)[0]

    # 최초 공제 시기에 청년/기타 작년도 대비 근무 개월 수 차이
    target_young_deductions = yng_diff[first_deduction_index]  # 청년
    target_etc_deductions = etc_diff[first_deduction_index]  # 기타

    # axis=0 최초 공제 연도, axis=1 (index, 작년도 대비 청년 근무 개월 수 차이, 작년도 대비 기타 근무 개월 수 차이)
    first_deduction_infos = np.stack([first_deduction_index, target_young_deductions, target_etc_deductions], axis=-1)
    return first_deduction_infos


def deduction_mask(young_counts, etc_counts, index):
    """
    Description:
        최초 공제 시기 이후 2년동안 청년 공제, 기타 공제 자격여부를 파악해 반환합니다.
        공제 규칙은 wiki 을 참조하세요.

    Args:
    :param ndarray young_counts: 연도별 청년 근무 달(month) 수
    :param ndarray etc_counts: 연도별 기타 근무 달(month) 수
    :param int index: 최초 공제를 받은 연도 인덱스

    :ndarray return:
        +--+------+------+------+------+------+
        |  | 2019 | 2020 | 2021 | 2022 | 2023 |
        +--+------+------+------+------+------+
        |  | NaN  |  NaN | True | True | -1  |
        +--+------+------+------+------+------+
        |  | NaN  |  NaN | True | False| -1  |
        +--+------+------+------+------+------+
    NaN 은 공제 계산을 하지 않은것
    """
    year_length = len(young_counts)
    deduction_year = 2  # 추가 공제 년도

    # axis 0 에 0th index => 청년 공제, axis 0 에 1th index => 기타 공제
    deduction_calendar = np.zeros(shape=(len(young_counts), 2)) + np.nan

    yng_diff = get_diff(young_counts)
    etc_diff = get_diff(etc_counts)
    wkr_diff = yng_diff + etc_diff

    # 최초 공제시 근로 개월수 작녀 대비 차이
    wrk_diff_std = wkr_diff[index]
    yng_diff_std = yng_diff[index]
    etc_diff_std = etc_diff[index]

    for i in np.arange(index, np.minimum(index + deduction_year + 1, year_length)):
        # 공제 자격 여부를 검토합니다.
        # 공제 자격을 유지 합니다.
        # 청년 공제 가능 여부를 검토 합니다.

        if wrk_diff_std <= wkr_diff[i]:
            # 청년 공제 가능시 deduction_calendar 에 청년 공제 비율을 기록합니다.
            if yng_diff_std <= yng_diff[i]:
                deduction_calendar[i, 0] = True
            else:
                deduction_calendar[i, 0] = False
                # 기타 공제 가능시 deduction_calendar 에 기타 공제 비율을 기록합니다.

            if etc_diff_std <= etc_diff[i]:
                deduction_calendar[i, 1] = True
            else:
                deduction_calendar[i, 1] = False
        # 상시 근로자가 한명이라도 2년안에 줄면 공제 자격을 상실 합니다.
        else:
            deduction_calendar[i, 0] = -1
            deduction_calendar[i, 1] = -1
            break
    return deduction_calendar


def deduction_table(capital_area):
    """
    공제 금액 테이블을 반환합니다.
    (⚠️ 중소 기업 이하만 적용 가능하다. 매년 년도별 공제 금액을 업데이트 해야 한다.)
    또한 수도권 / 비수도권이 나눠어져 있다.
    공제율(중소 기업 이하):
        2018~2020, 2023년
            +----------+------------+--------+
            |          | 수도권 밖  | 수도권 |
            +----------+------------+--------+
            | 청년     | 1200       | 1100   |
            +----------+------------+--------+
            | 청년 외  | 770        | 700    |
            +----------+------------+--------+
        2021,2022
            +----------+------------+--------+
            |          | 수도권 밖  | 수도권 |
            +----------+------------+--------+
            | 청년     | 1300       | 1100   |
            +----------+------------+--------+
            | 청년 외  | 770        | 700    |
            +----------+------------+--------+
    :param capital_area:
    :return:
    """
    capital_df = pd.DataFrame()
    capital_df.index = ['young', 'etc']
    capital_df[2018] = [1100, 700]
    capital_df[2019] = [1100, 700]
    capital_df[2020] = [1100, 700]
    capital_df[2021] = [1100, 700]
    capital_df[2022] = [1100, 700]
    capital_df[2023] = [1100, 700]

    noncptl_df = pd.DataFrame()
    noncptl_df.index = ['young', 'etc']
    noncptl_df[2018] = [1200, 770]
    noncptl_df[2019] = [1200, 770]
    noncptl_df[2020] = [1200, 770]
    noncptl_df[2021] = [1300, 770]
    noncptl_df[2022] = [1300, 770]
    noncptl_df[2023] = [1200, 770]

    if capital_area:
        tax_table = capital_df
    else:
        tax_table = noncptl_df

    return tax_table


def deduction_tax(year, type, capital_area):
    """
    해당년도의 청년 또는 기타 공제 금액을 산정해 반환한다.
    (⚠️ 중소 기업 이하만 적용 가능하다. 매년 년도별 공제 금액을 업데이트 해야 한다.)

    Args:
        :param int year: 적용 연도
        :param str type: 'young' or 'etc'
        :param bool capital_area: 수도권 여부, 수도권이면 True

        :int return: 공제 금액
    """
    assert (type == 'young') or (type == 'etc'), 'type 값으로는 "young" , "etc" 만 가능합니다.'

    tax_table_df = deduction_table(capital_area)
    tax = tax_table_df.loc[type, year]
    return tax


def calculate_tax(year, capital_area, yng_diff, etc_diff):
    """
    공제 받을 세금을 계산해 반환
    공제 금액은 최대 상시 근로자 수에 비례한다.

    :param int year: 적용 연도
    param bool capital_area: 수도권 여부, 수도권이면 True
    :param ndarray young_counts: 연도별 청년 근로자, 값 순서는 연도순으로 나열되어 있어야 합니다.
    :param ndarray etc_counts: 연도별 기타 근로자

    :return:
    """
    # 청년/기타 근로 개월 수 차이
    total_diff = yng_diff + etc_diff

    # 해당 연도 및 지역의 청년/기타 공제 금액
    young_tax = deduction_tax(year, 'young', capital_area)
    etc_tax = deduction_tax(year, 'etc', capital_area)

    if yng_diff >= 0 and etc_diff >= 0:
        young_diff_tax = young_tax * yng_diff
        etc_diff_tax = etc_tax * etc_diff

    elif yng_diff <= 0 and etc_diff >= 0:
        young_diff_tax = 0
        etc_diff_tax = etc_tax * total_diff

    elif yng_diff >= 0 and etc_diff <= 0:
        young_diff_tax = young_tax * total_diff
        etc_diff_tax = 0

    elif yng_diff <= 0 and etc_diff <= 0:
        young_diff_tax = 0
        etc_diff_tax = 0
    else:
        raise NotImplementedError

    return young_diff_tax, etc_diff_tax


def intersection(start_date_1, end_date_1, start_date_2, end_date_2, dummy_date):
    """
    Description:
        두 날짜 범위중 겹치는 범위를 제공 합니다.
        만약 겹치지 않으면 None 을 반환합니다.

    Usage:
        start_date_1 = pd.to_datetime(pd.Series(['2017-01-01', '2017-01-01', '2017-01-01', '2017-01-01']))
        end_date_1 = pd.to_datetime(pd.Series(['2019-01-01', '2019-01-01', '2019-01-01', '2019-01-01']))
        start_date_2 = pd.to_datetime(pd.Series(['2019-01-01', '2018-01-01', '2018-01-01', '2016-01-01']))
        end_date_2 = pd.to_datetime(pd.Series(['2020-01-01', '2020-01-01', '2018-12-31', '2018-01-01']))
        start_date, end_date = intersection(start_date_1, end_date_1, start_date_2, end_date_2,)
        results
            start_date (0, NaT) (1, Timestamp('2018-01-01 00:00:00')) (2, Timestamp('2018-01-01 00:00:00')) (3, Timestamp('2017-01-01 00:00:00'))
            end_date (0, NaT) (1, Timestamp('2019-01-01 00:00:00')) (2, Timestamp('2018-12-31 00:00:00')) (3, Timestamp('2018-01-01 00:00:00'))
    Args:
        :param pd.Series start_date_1:
        :param pd.Series end_date_1:
        :param pd.Series start_date_2:
        :param pd.Series end_date_2:
        :param datetime dummy_date: NaN 값을 대체할 날짜
            start_date (0, NaT) ... => (0, dummy_date)
            end_date (0, NaT) ...   => (0, dummy_date)
        :return:
    """
    assert (start_date_1 < end_date_1).all() & (start_date_2 < end_date_2).all()
    max_mask = start_date_1 >= start_date_2
    start_date = start_date_2.copy()
    start_date.loc[max_mask] = start_date_1.loc[max_mask]

    min_mask = end_date_1 <= end_date_2
    end_date = end_date_2.copy()
    end_date.loc[min_mask] = end_date_1.loc[min_mask]

    not_intersection_mask = start_date > end_date
    start_date.loc[not_intersection_mask] = np.nan
    end_date.loc[not_intersection_mask] = np.nan

    if dummy_date:
        start_date.fillna(dummy_date, inplace=True)
        end_date.fillna(dummy_date, inplace=True)
    return start_date, end_date


def get_deduction(deductions, year):
    """
    Description:
        해당 년도에 받은 총 공제 금액을 제공 한다.

    Args:
        :param list deductions:
            [deduction, deduction ... deduction]
            deduction:
                +--+------+------+------+------+------+
                |       | 2019 | 2020 | 2021 | 2022 | 2023 |
                +--+------+------+------+------+------+
                | young | NaN  |  NaN | True | True | NaN  |
                +--+------+------+------+------+------+
                | etc   | NaN  |  NaN | True | False| NaN  |
                +--+------+------+------+------+------+
        :param int year:

    :return:
    """
    tax = []
    for deduction_df in deductions:
        mask = deduction_df < 0
        deduction_df[mask] = 0
        deduction_df = deduction_df.fillna(0)
        tax.append(deduction_df.loc[:, year].sum())
    total_tax = np.sum(tax)
    return total_tax


def get_refund(deductions, year):
    """
    Description:
        환급해야 할 세금 금액을 계산해 반환합니다.
        :param list deductions:
            [deduction, deduction ... deduction]
            deduction:
                +--+------+------+------+------+------+
                |       | 2019 | 2020 | 2021 | 2022 | 2023 |
                +--+------+------+------+------+------+
                | young | NaN  |  NaN | True | True | NaN  |
                +--+------+------+------+------+------+
                | etc   | NaN  |  NaN | True | False| NaN  |
                +--+------+------+------+------+------+
        :param int year:
    :return:
    """

    # 환급 받아야 할 공제을 추출합니다.
    refund_index = []
    refund_taxs = []
    for ind, deduction_df in enumerate(deductions):
        # 추가 징수
        if deduction_df.loc['young', year] == -1:  # 'young' 이 -1 이면 'etc' 도 반드시 -1 입니다.
            deduction_df = deduction_df.replace({-1: 0})
            deduction_df = deduction_df.fillna(0)
            refund_index.append(ind)
            # 환급 해야 할 돈을 계산합니다. 받았던 모든 공제를 반납해야 합니다.
            tax = deduction_df.sum()
            refund_taxs.append(tax)
        else:
            refund_taxs.append(0)

    # 환급 해야 할 돈을 반환합니다.
    refund_tax = np.sum(refund_taxs)

    return refund_tax


def deduction_and_tax(path, start_date, end_date, curr_date, capital_area):
    """
    Description:
        :param path:
            path = './data/사업장가입자명부_20221222 (상실자포함).xls'
        :param start_date:
            start_date = '2018-01-01'
        :param end_date:
            end_date = '2022-12-31'
        :param curr_date:
            curr_date = pd.Timestamp.today()
        :return:
    """
    years = list(range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1))
    calendar = generate_work_calendar(path, start_date, end_date, curr_date=curr_date)

    # 각 년도별 상시 근무자 인원 및 청년 근무자 인원
    calendar_sum = calendar.iloc[:, :].sum(axis=0)
    calendar_sum.iloc[0] = '합계'

    # 청년 근로 및 기타 근로자 수를 계산합니다.
    n_workers = calendar_sum[1:1 + 5].values
    n_youngs = calendar_sum[1 + 5:1 + 5 + 5].values
    n_etc = n_workers - n_youngs

    # 각 년도별 공제 표 생성
    deductions = []
    first_deduction_infos = first_deduction(n_youngs, n_etc)

    for info in first_deduction_infos:
        index = info[0]
        yng_diff = info[1]
        etc_diff = info[2]
        mask = deduction_mask(n_youngs, n_etc, index)
        deduction_df = pd.DataFrame(mask.T, columns=years, index=['young', 'etc'])
        #
        young_tax, etc_tax = calculate_tax(year=years[index],
                                           capital_area=capital_area,
                                           yng_diff=yng_diff,
                                           etc_diff=etc_diff)
        #
        deduction_df.iloc[:, :] = np.array([[young_tax], [etc_tax]]) * deduction_df.values
        deductions.append(deduction_df)

    # 총합 공제 금액 계산
    deduction_tax = get_deduction(deductions, 2022)

    # 공제 금액 반납
    refund_tax = get_refund(deductions, 2022)

    print('2022년 공제 받은 금액 : {} \n2022년 추가 납부 금액 : {}'.format(deduction_tax, refund_tax))
    return deduction_tax, refund_tax, calendar


if __name__ == '__main__':
    # path = './data/사업장가입자명부_20221222 (상실자포함).xls'
    #
    # # 지정된 년도별, 각 사람별 상시 근무자 개월 수, 청년 근무자 개월 수 추출
    # start_date = '2018-01-01'
    # end_date = '2022-12-31'
    # curr_date = pd.Timestamp.today()
    # years = list(range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1))
    # calendar = generate_work_calendar(path, start_date, end_date, curr_date=curr_date)
    # capital_area = True
    #
    # # 각 년도별 상시 근무자 인원 및 청년 근무자 인원
    # calendar_sum = calendar.iloc[:, :].sum(axis=0)
    # calendar_sum.iloc[0] = '합계'
    #
    # # 청년 근로 및 기타 근로자 수를 계산합니다.
    # n_workers = calendar_sum[1:1 + 5].values
    # n_youngs = calendar_sum[1 + 5:1 + 5 + 5].values
    # n_etc = n_workers - n_youngs
    #
    # # 각 년도별 공제 표 생성
    # deductions = []
    # first_deduction_infos = first_deduction(n_youngs, n_etc)
    # for info in first_deduction_infos:
    #     index = info[0]
    #     yng_diff = info[1]
    #     etc_diff = info[2]
    #     mask = deduction_mask(n_youngs, n_etc, index)
    #     deduction_df = pd.DataFrame(mask.T, columns=years, index=['young', 'etc'])
    #     #
    #     young_tax, etc_tax = calculate_tax(year=years[index],
    #                                        capital_area=capital_area,
    #                                        yng_diff=yng_diff,
    #                                        etc_diff=etc_diff)
    #     #
    #     deduction_df.iloc[:, :] = np.array([[young_tax], [etc_tax]]) * deduction_df.values
    #     deductions.append(deduction_df)
    #
    # # 총합 공제 금액 계산
    # deduction_tax = get_deduction(deductions, 2022)
    #
    # # 공제 금액 반납
    # refund_tax = get_refund(deductions, 2022)

    # /print('2022년 공제 받은 금액 : {} \n2022년 추가 납부 금액 : {}'.format(deduction_tax, refund_tax))

    path = './data/사업장가입자명부_20221222 (상실자포함).xls'
    start_date = '2018-01-01'
    end_date = '2022-12-31'
    curr_date = pd.Timestamp.today()
    deduction_tax, refund_tax = deduction_and_tax(path, start_date, end_date, curr_date, True)
    pass
