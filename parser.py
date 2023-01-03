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

    :param ndarray young_counts: 청년 근로자, 값 순서는 연도순으로 나열되어 있어야 합니다.
    :param ndarray etc_counts: 기타 근로자
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

    # 최초 공제 세부사항
    target_young_deductions = yng_diff[first_deduction_index]  # 청년
    target_etc_deductions = etc_diff[first_deduction_index]  # 기타

    # 세부 사항에서 rate 가 음수이면 0으로 치환합니다.
    target_young_deductions = np.where(target_young_deductions <= 0, 0, target_young_deductions)
    target_etc_deductions = np.where(target_etc_deductions <= 0, 0, target_etc_deductions)

    # axis=0 최초 공제 연도, axis=1 (index, 청년 공제 비율, 기타 공제 비율)
    first_deduction_infos = np.stack([first_deduction_index, target_young_deductions, target_etc_deductions], axis=-1)
    return first_deduction_infos


def add_deduction(young_counts, etc_counts, index):
    """
    Description:
        추가 공제 자격여부를 확인 한 후 여부를 확인합니다.
    :return:
    """
    n = len(young_counts)
    yng_diff = get_diff(young_counts)
    etc_diff = get_diff(etc_counts)
    wkr_diff = yng_diff + etc_diff

    sliced_wrk = wkr_diff[index:]
    sliced_yng = yng_diff[index:]
    sliced_etc = etc_diff[index:]

    return False


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


if __name__ == '__main__':
    path = './data/사업장가입자명부_20221222 (상실자포함).xls'

    # 지정된 년도별, 각 사람별 상시 근무자 개월 수, 청년 근무자 개월 수 추출
    start_date = '2018-01-01'
    end_date = '2022-12-31'
    curr_date = pd.Timestamp.today()
    calendar = generate_work_calendar(path, start_date, end_date, curr_date=curr_date)

    # 각 년도별 상시 근무자 인원 및 청년 근무자 인원
    calendar_sum = calendar.iloc[:, :].sum(axis=0)
    calendar_sum.iloc[0] = '합계'

    # 공제 금액 계산
    first_deduction_infos = first_deduction(calendar_sum[1:1 + 5].values, calendar_sum[1 + 5:1 + 5 + 5].values)
    pass
