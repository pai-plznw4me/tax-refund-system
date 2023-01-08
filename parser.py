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


def nan2boolean(series):
    """
    Description:
        DataFrame Series 을 datatype 을 boolean 으로 변환합니다.
        NaN 은 False 로 변환합니다. 그 이외는 True 로 변환합니다.

    :param pd.Series series:
    :pd.Series return:
    """
    series = series.copy()
    nan_mask = series.isna()
    series.loc[nan_mask] = False
    series.loc[~nan_mask] = True
    series = series.astype(bool)
    return series


def load_workdate(path):
    """
    Description:
        사업자가입명부 엑셀 파일을 로드 합니다.
        장애인, 임원, 계약직 boolean mask 으로 변환합니다.

    :param str path: 사업자 가입자 명부
    :pd.Dataframe return:
    """

    # 엑셀 파일 로드
    xls = pd.ExcelFile(path)
    sheets = xls.sheet_names
    sheet = sheets[0]
    sh_df = xls.parse(sheet_name=sheet)
    df = sh_df.iloc[1:, 3:]
    df.columns = ['주민등록번호', '이름', '자격취득일', '자격상실일', '장애인', '임원', '계약직', '입대', '전역']

    df.isetitem(4, nan2boolean(df.iloc[:, 4]))  # 장애인 여부
    df.isetitem(5, nan2boolean(df.iloc[:, 5]))  # 임원 여부
    df.isetitem(6, nan2boolean(df.iloc[:, 6]))  # 계약직 여부
    df.isetitem(7, pd.to_datetime(df.iloc[:, 7]))  # 입대 날짜
    df.isetitem(8, pd.to_datetime(df.iloc[:, 8]))  # 전역 날짜

    return df


def get_dates_by_month(start_date, end_date, option='end'):
    """
    Description:
        지정된 기간 내 달(month) 단위로 날짜 정보(yyyy-mm-dd)를 제공합니다.
    Usage:
        >>> get_dates_by_month('2023-01-01', '2023-03-01', option='end')
        # ['2018-01-31', '2018-02-28']

    Args:
        :param pd.datetime start_date: yyyy-mm-dd
        :param pd.datetime end_date: yyyy-mm-dd
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
        시작 날짜와 종료 날짜 사이 각 달에 해당 인원이 근무 했는지를 파악해 반환합니다.
        근무 여부 판단 상세 기준: 각 달의 마지막날이 기준 날짜가 됩니다. 기준 날짜 이전에 입사, 기준 날짜 퇴사 시 True 로 합니다.

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

    # 각 달의 마지막날이 기준 날짜,
    # 기준 날짜 이전에 입사 그리고 기준 날짜 퇴사했으면 True 아니면 False 을 준다.
    calendar_df = pd.DataFrame()
    for date in dates:
        mask = (acquisi_date <= date) & (disqual_date >= date)
        calendar_df[date] = pd.Series(mask)
    return calendar_df


def sum_by_yaer(calendar_df, years, prefix=None):
    """
    Description:
        년도 별 근무자 수를 집계(sum)해 반환

    :param DataFrame calendar_df:
       ⚠️ calendar_df column 이름은 datatime 으로 이루어져야 한다.
            example)
            +--------+----------+----------+----------+----------+--------+
            |        |2018.1.31| 018.2.28 |2018.3.31| 2018.4.30 |2018.5.31|
            +--------+----------+----------+----------+----------+--------+
            | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
            +--------+----------+----------+----------+----------+--------+
            | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
            +--------+----------+----------+----------+----------+--------+
    :param list years: [int, int, ... int ]
    :param str prefix: column 명 앞에 붙여질 접두사

    :return DataFrame:
        columns : years
        index : calendar_df.index
        values : 각 년도별 일한 개월 수
    """

    # 각 년도별 집계(total)테이블 생성
    totalwork_df = pd.DataFrame()
    totalwork_df.index = calendar_df.index
    calendar_years = calendar_df.columns.map(lambda x: x.year)

    # 각 년도별 근무 날짜 집계
    for ind, year in enumerate(years):
        # 각 년도에 해당 하는 column 을 추출
        mask = (calendar_years == year)
        sliced_df = calendar_df.loc[:, mask]
        # 각 년도별 근무 달 수 집계(sum)
        total_works = sliced_df.values.sum(axis=1)
        # column 이름 변경
        if prefix:
            column_name = prefix + str(year)
        else:
            column_name = str(year)
        totalwork_df[column_name] = total_works

    return totalwork_df


def resident2date(resident_codes):
    """
    Description:
        주민등록번호를 날짜로 변환합니다.
        (주민등록번호 샘플: 900117-1xxxxxx)
        뒷번호가 1, 2, 3, 4 여부에 따라 19년도 출생인지 20년도 출생인지가 결정 됩니다.

    :param pd.Series resident_codes:
    example)
        [900117-1xxxxxx, 900117-1xxxxxx, ... 900117-1xxxxxx]
    :datetime return: yyyymmdd
    example)
        19900117
    """

    # 생년 월일을 계산한다.
    birth_date = resident_codes.map(lambda x: x[:6])
    birth_index = resident_codes.map(lambda x: x[7]).map(int)
    prefix_mask = birth_index < 3
    birth_date.loc[prefix_mask] = birth_date.loc[prefix_mask].map(lambda x: '19' + str(x))
    birth_date.loc[~prefix_mask] = birth_date.loc[~prefix_mask].map(lambda x: '20' + str(x))
    return birth_date


def military_period(enlist, discharge):
    """
    Description:
        각 인원별 군 복무 기간을 일(day) 단위로 계산해 반환합니다.
    Args:
        :param pd.Series enlist: 입대 날짜
        :param pd.Series discharge: 전역 날짜

    :Series return:
    """
    duration = discharge - enlist
    duration = duration.fillna(pd.Timedelta(0))
    period = pd.Series(name='period', data=duration)
    return period


def generate_work_calendar(start_date, end_date, acquisi_date, disqual_date):
    """
    Description:
        각 인원별, 각 년도별 상시 근로자와 청년 근로자 총 근무 달수를 계산해 반환합니다.
        ⚠️ Warning : 210살 이상 생존한 사람이 있다면 해당 기능에 문제가 생길수 있습니다.

    Args:
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param pd.Series acquisi_date: 자격취득일
            example) [timestamp, timestamp, ... timestamp]
        :param pd.Series disqual_date: 자격상실일
            example) [timestamp, timestamp, ... timestamp]

    :DataFrame return:
        workdate_df: 근무 달수 별로 일한 달에 True, 일하지 않은 달에 False
            +----------+----------+----------+----------+--------+
            | 2018.1.1 | 2018.1.2 | 2018.1.3 | 2018.1.4 | 2018.1.5|
            +----------+----------+----------+----------+--------+
            | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
            +--------+----------+----------+----------+----------+
            | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
            +----------+----------+----------+----------+--------+

        workdate_sum_df: 근무 달수를 연도별로 더함
            +--------+--------+--------+--------+--------+
            | 2018년 | 2019년 | 2020년 | 2021년 | 2022년    |
            +--------+--------+--------+--------+--------+
            | 12     | 12     | 12     | 12     | 12     |
            +--------+--------+--------+--------+--------+
            | 12     | 12     | 12     | 12     | 12     |
            +--------+--------+--------+--------+--------+

    """
    # 적용 연도
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    years = list(range(start_year, end_year + 1))

    # 인원별 상시 근무 날짜 체크 합니다.
    workdate_df = check_workdate(start_date, end_date, acquisi_date, disqual_date)
    workdate_sum_df = sum_by_yaer(workdate_df, years, prefix='(상시)')

    return workdate_df, workdate_sum_df


def generate_young_calendar(start_date, end_date, acquisi_date, disqual_date, enlist_date, discharge_date,
                            resident_number):
    """
    Description:
        청년 근로자 근로 테이블과 청년 근로 집계 테이블을 생성합니다.

    Args:
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param pd.Series acquisi_date: 자격취득일
            example) [timestamp, timestamp, ... timestamp]
        :param pd.Series disqual_date: 자격상실일
            example) [timestamp, timestamp, ... timestamp]
        :param Datetime enlist_date: 입대 날짜
            example) [timestamp, timestamp, ... timestamp]
        :param Datetime discharge_date: 전역 날짜
            example) [timestamp, timestamp, ... timestamp]
        :param Datetime resident_number: 생년 월일
            example) [yyyymmdd, yyyymmdd, ... yyyymmdd]
        :return:
            :DataFrame young_workdate_df: 근무 달수 별로 일한 달에 True, 일하지 않은 달에 False
                +--------+----------+----------+----------+----------+--------+
                |        |2018.1.31|2018.2.28 |2018.3.31 | 2018.4.30|2018.5.31|
                +--------+----------+----------+----------+----------+--------+
                | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
                +--------+----------+----------+----------+----------+--------+
                | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
                +--------+----------+----------+----------+----------+--------+

            :DataFrame young_workdate_sum_df: 근무 달수를 연도별로 더함
                +--------+--------+--------+--------+--------+
                | 2018년 | 2019년 | 2020년 | 2021년 | 2022년    |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
    """
    # 적용 연도
    years = get_years(start_date, end_date)
    dummy_date = pd.to_datetime('1800-01-01')

    # 청년 근무 날짜를 측정 합니다.(군복무 기간 추가)
    young_offset = 30
    birth_date = resident_number
    young_acquisi_date = birth_date
    young_disqual_date = birth_date + pd.DateOffset(years=young_offset)

    # 청년 복무 기간에서 군대를 다녀온 기간을 추가로 제공합니다.
    period = military_period(enlist_date, discharge_date)
    period.index = young_disqual_date.index
    young_disqual_date = young_disqual_date + period

    # 청년 인정 기간과 근무 기간 중 겹치는 기간을 계산합니다.
    intrsctn_young_acquisi_date, intrsctn_young_disqual_date = \
        intersection(acquisi_date, disqual_date, young_acquisi_date, young_disqual_date, dummy_date)
    young_workdate_df = check_workdate(start_date, end_date, intrsctn_young_acquisi_date, intrsctn_young_disqual_date)
    young_workdate_sum_df = sum_by_yaer(young_workdate_df, years)

    return young_workdate_df, young_workdate_sum_df


def generate_elder_calendar(start_date, end_date, acquisi_date, disqual_date, resident_number):
    """
    Description:
        청년 근로자 근로 테이블과 청년 근로 집계 테이블을 생성합니다.

    Args:
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param pd.Series acquisi_date: 자격취득일
            example) [timestamp, timestamp, ... timestamp]
        :param pd.Series disqual_date: 자격상실일
            example) [timestamp, timestamp, ... timestamp]
        :param DataFrame resident_number:
            example) [yyyymmdd, yyyymmdd, ... yyyymmdd]
        :return:
            elder_workdate_df: 근무 달수 별로 일한 달에 True, 일하지 않은 달에 False
                +--------+----------+----------+----------+----------+--------+
                |        |2018.1.31|2018.2.28 |2018.3.31 | 2018.4.30|2018.5.31|
                +--------+----------+----------+----------+----------+--------+
                | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
                +--------+----------+----------+----------+----------+--------+
                | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
                +--------+----------+----------+----------+----------+--------+

            elder_workdate_sum_df: 근무 달수를 연도별로 더함
                +--------+--------+--------+--------+--------+
                | 2018년 | 2019년 | 2020년 | 2021년 | 2022년    |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
    """

    years = get_years(start_date, end_date)
    birth_date = resident_number
    dummy_date = pd.to_datetime('1800-01-01')

    # 노인 근무 기간
    elder_offset = 60
    elder_acquisi_date = birth_date + pd.DateOffset(years=elder_offset)
    elder_disqual_date = elder_acquisi_date + pd.DateOffset(years=150)
    # 상시 근론 날짜와 노인이였던 시기중 겹치는 시기를 표시한다.
    intrsctn_elder_acquisi_date, intrsctn_elder_acquisi_date = \
        intersection(acquisi_date, disqual_date, elder_acquisi_date, elder_disqual_date, dummy_date)
    elder_workdate_df = check_workdate(start_date, end_date, intrsctn_elder_acquisi_date, intrsctn_elder_acquisi_date)
    elder_workdate_sum_df = sum_by_yaer(elder_workdate_df, years)

    return elder_workdate_df, elder_workdate_sum_df


def generate_disable_calendar(start_date, end_date, disable_mask, workdate_df):
    """
    Description:
        장애인 근무를 표기해 반환합니다.

    Args:
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param Series disable_mask: 장애인 리스트, 장애인 자격이 있으면 True, 없으면 False 로 되어 있습니다.
            example) [True, True, False, False ... True]
        :param DataFrame workdate_df: 상시 근로자 각 달별 근무 여부
        :return:
            :DataFrame disable_workdate_df:
                +--------+----------+----------+----------+----------+--------+
                |        |2018.1.31|2018.2.28 |2018.3.31 | 2018.4.30|2018.5.31|
                +--------+----------+----------+----------+----------+--------+
                | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
                +--------+----------+----------+----------+----------+--------+
                | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
                +--------+----------+----------+----------+----------+--------+

            :DataFrame disable_workdate_sum_df:
                +--------+--------+--------+--------+--------+
                | 2018년 | 2019년 | 2020년 | 2021년 | 2022년    |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+

        """

    years = get_years(start_date, end_date)

    disable_workdate_df = workdate_df.copy()
    disable_workdate_df.loc[~disable_mask] = False
    disable_workdate_df.loc[disable_mask] = True
    disable_workdate_df = disable_workdate_df & workdate_df
    disable_workdate_sum_df = sum_by_yaer(disable_workdate_df, years)

    return disable_workdate_df, disable_workdate_sum_df


def generate_executive_calendar(start_date, end_date, executive_mask, workdate_df):
    """
    Description:
       임원 근무를 표기해 반환합니다.

    Args:
        :param str start_date: yyyy-mm-dd, example) '2017-01-01'
        :param str end_date: yyyy-mm-dd, example) '2022-12-31'
        :param Series executive_mask: dtype bool
            임원 리스트, 임원 자격이 있으면 True, 없으면 False 로 되어 있습니다.
        :param DataFrame workdate_df:
        :return:
            executive_workdate_df: 근무 달수 별로 일한 달에 True, 일하지 않은 달에 False
                +--------+----------+----------+----------+----------+--------+
                |        |2018.1.31|2018.2.28 |2018.3.31 | 2018.4.30|2018.5.31|
                +--------+----------+----------+----------+----------+--------+
                | 강대영 | TRUE     | FALSE    | FALSE    | FALSE    | FALSE  |
                +--------+----------+----------+----------+----------+--------+
                | 강혜진 | TRUE     | TRUE     | TRUE     | TRUE     | TRUE   |
                +--------+----------+----------+----------+----------+--------+

            executive_workdate_sum_df: 근무 달수를 연도별로 더함
                +--------+--------+--------+--------+--------+
                | 2018년 | 2019년 | 2020년 | 2021년 | 2022년    |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
                | 12     | 12     | 12     | 12     | 12     |
                +--------+--------+--------+--------+--------+
        """
    years = get_years(start_date, end_date)

    executive_workdate_df = workdate_df.copy()
    executive_workdate_df.loc[executive_mask] = True
    executive_workdate_df.loc[~executive_mask] = False
    executive_workdate_df = executive_workdate_df & workdate_df
    executive_workdate_sum_df = sum_by_yaer(executive_workdate_df, years)

    return executive_workdate_df, executive_workdate_sum_df


def get_diff(workers):
    """
    Description:
        년도별 근로자 차이를 계산해 반환

    Args:
        :param ndarray workers:
            example) [52, 64, .. , 58]
        :ndarray return:
    """
    rolled_workers = np.roll(workers, 1)
    diff = workers - rolled_workers
    diff[0] = 0
    return diff


def get_years(start_date, end_date):
    """
    Description:
        시작년도 이상 마지막 년도 이하 모든 년도를 찾아 반환합니다.
        년도는 오름 차순으로 정렬되어 있습니다.
        시작년도와 마지막년도를 모두 포함합니다.

    :param str start_date: yyyy-mm-dd
    :param str end_date: yyyy-mm-dd
    :list return: [int, int, int]
    """

    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    years = list(range(start_year, end_year + 1))
    return years


def first_deduction(young_counts, etc_counts, years):
    """
    Description:
        최초 공제 정보를 계산해 반환합니다.
    Args:
        :param ndarray young_counts: 연도별 청년 근로자, 값 순서는 연도순으로 나열되어 있어야 합니다.
        :param ndarray etc_counts: 연도별 기타 근로자
        :return:
            [[index, 청년 공제 증가, 기타 공제 증가, 공제 년도],
             [index, 청년 공제 증가, 기타 공제 증가, 공제 년도]]
             ⚠️(청년 공제 증가, 기타 공제 증가 최소값 = 0)

    """
    yng_diff = get_diff(young_counts)
    etc_diff = get_diff(etc_counts)
    wkr_diff = yng_diff + etc_diff

    # 최초 공제 시기
    first_deduction_index = np.where(wkr_diff > 0)[0]
    first_deduction_year = list(map(lambda x: years[x], first_deduction_index))

    # 최초 공제 시기에 청년/기타 작년도 대비 근무 개월 수 차이
    target_young_deductions = yng_diff[first_deduction_index]  # 청년
    target_etc_deductions = etc_diff[first_deduction_index]  # 기타

    # axis=0 최초 공제 연도, axis=1 (index, 작년도 대비 청년 근무 개월 수 차이, 작년도 대비 기타 근무 개월 수 차이)
    first_deduction_infos = np.stack(
        [first_deduction_index, target_young_deductions, target_etc_deductions, first_deduction_year], axis=-1)
    first_deduction_infos = pd.DataFrame(first_deduction_infos)
    first_deduction_infos.columns = ['index', 'young', 'etc', 'year']

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
    Description:
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
    Args:
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
    Description:
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


def calculate_deduction(year, capital_area, yng_diff, etc_diff):
    """
    Description:
        공제 받을 세금을 계산해 반환
        공제 금액은 최대 상시 근로자 수에 비례한다.

    Args:
        :param int year: 적용 연도
        :param bool capital_area: 수도권 여부, 수도권이면 True
        :param ndarray yng_diff: 연도별 청년 근로자, 값 순서는 연도순으로 나열되어 있어야 합니다.
        :param ndarray etc_diff: 연도별 기타 근로자

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


def calculate_deduction_sum(deductions, year):
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


def calculate_tax_sum(deductions, year):
    """
    Description:
        환급해야 할 세금 금액을 계산합니다.
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


def exclusive_workdate(workdate_df, *masks):
    """
    Description:
        mask 에 해당하는 row 는 모두 False 로 변환합니다.

    :param workdate_df:
    :param masks:
    :return:
    """

    workdate_df = workdate_df.copy()
    for mask in masks:
        workdate_df.loc[mask] = False
    return workdate_df


def get_deductions(n_youngs, n_etc, capital_area, years):
    """
    Description:
        공제 테이블을 추출해 반환합니다.
    Args:
        :param n_youngs: 각 년도 별 청년 근로자 수
        :param n_etc: 각 년도 별 기타 근로자 수
        :param capital_area: 수도권 여부
        :param years: 각 년도
        :list return:
            [공제 테이블, 공제 테이블 ... ,공제 테이블]

            공제 테이블 예시)
                +--+------+------+------+------+------+
                |  | 2019 | 2020 | 2021 | 2022 | 2023 |
                +--+------+------+------+------+------+
                |  | NaN  |  NaN | 1100 | 1100 | -1   |
                +--+------+------+------+------+------+
                |  | NaN  |  NaN | 700 | 0     | -1   |
                +--+------+------+------+------+------+
    """
    # 최초 공제 리스트 추출
    first_deduction_info_df = first_deduction(n_youngs, n_etc, years)
    first_deduction_infos = first_deduction_info_df.values

    # 최초 공제 리스트를 활용합니다.
    deduction_tables = []
    for info in first_deduction_infos:
        # 각 최초 공제 별 정보 추출
        index = info[0]
        yng_diff = info[1]
        etc_diff = info[2]
        mask = deduction_mask(n_youngs, n_etc, index)
        deduction_df = pd.DataFrame(mask.T, columns=years, index=['young', 'etc'])

        # 최초 공제에 대한 기타 공제 금액, 청년 공제 금액을 계산합니다.
        young_tax, etc_tax = calculate_deduction(year=years[index],
                                                 capital_area=capital_area,
                                                 yng_diff=yng_diff,
                                                 etc_diff=etc_diff)

        # 기타공제 금액, 청년 공제금액을 곱합니다.
        deduction_df.iloc[:, :] = np.array([[young_tax], [etc_tax]]) * deduction_df.values
        deduction_tables.append(deduction_df)

    return deduction_tables, first_deduction_info_df


def generate_workdate(df, start_date, end_date, curr_date):
    """
    Description:
        :param df:
            path = './data/사업장가입자명부_20221222 (상실자포함).xls'
        :param str start_date:
            start_date = '2018-01-01'
        :param str end_date:
            end_date = '2022-12-31'
        :param Timestamp curr_date:
            curr_date = pd.Timestamp.today()
        :return:
    """
    # 상시근로표 로드 및 관련 정보 추출
    resident_number = pd.to_datetime(resident2date(df.iloc[:, 0]))  # 주민등록번호
    acquisi_date = pd.to_datetime(df.iloc[:, 2])  # 자격취득날짜
    disqual_date = pd.to_datetime(df.iloc[:, 3]).fillna(curr_date)  # 자격상실날짜
    disable_mask = df.iloc[:, 4]  # 장애인 여부
    executive_mask = df.iloc[:, 5]  # 임원 여부
    contract_mask = df.iloc[:, 6]  # 계약직 여부
    enlist_date = df.iloc[:, 7]  # 입대 날짜
    discharge_date = df.iloc[:, 8]  # 전역 날짜

    # 시작년도 마지막 년도 사이 모든 연도 리스트
    years = list(range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1))

    # 상시 근로자 근무 표
    workdate_df, workdate_sum_df = generate_work_calendar(start_date, end_date, acquisi_date, disqual_date)

    # 청년 근로자 근무 표
    young_workdate_df, young_workdate_sum_df = generate_young_calendar(start_date, end_date, acquisi_date, disqual_date,
                                                                       enlist_date, discharge_date, resident_number)
    # 노인 근로자 근무 표
    elder_workdate_df, elder_workdate_sum_df = generate_elder_calendar(start_date, end_date, acquisi_date, disqual_date,
                                                                       resident_number)
    # 장애인 근로자 근무 표
    disable_workdate_df, disable_workdate_sum_df = generate_disable_calendar(start_date, end_date, disable_mask,
                                                                             workdate_df)
    # 임원 근로와 계약직 근로를 청년 근로에서 제거 합니다.
    young_workdate_df = exclusive_workdate(young_workdate_df, executive_mask, contract_mask)

    # 통합 청년 근로자
    merged_young_workdate_df = elder_workdate_df | young_workdate_df | disable_workdate_df
    merged_young_workdate_sum_df = sum_by_yaer(merged_young_workdate_df, years, '(청년)')

    return workdate_df, workdate_sum_df, merged_young_workdate_df, merged_young_workdate_sum_df


def extend_young_workdate_sum(young_workdate, etc_workdate):
    """
    Description:
        청년 유예 적용 young_workdate, etc_workdate 생성
    :param young_workdate:
    :param etc_workdate:
    :return:
    """


def validate_young_workdate(young_workdate, etc_workdate):
    """
    Description:
        청년 유예 적용 young_workdate, etc_workdate  을 활용해 추가 연장 가능 한지를 판단합니다.
    :param young_workdate:
    :param etc_workdate:
    :return:
    """


if __name__ == '__main__':
    # 사업자가입자명부를 로드합니다.
    path = './data/사업장가입자명부.xls'  # ./data/사업장가입자명부_20221222 (상실자포함).xls
    employee_df = load_workdate(path)

    # 필요 정보를 입력합니다.
    name = employee_df.iloc[:, 1]  # 이름
    start_date = '2018-01-01'
    end_date = '2022-12-31'
    curr_date = pd.Timestamp.today()
    years = list(range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1))

    # 상시근로표, 청년근로표, 기타근로표를 생성해 반환합니다,
    workdate_df, workdate_sum_df, young_workdate_df, young_workdate_sum_df = \
        generate_workdate(employee_df, start_date, end_date, curr_date)
    etc_workdate_sum_df = pd.DataFrame(workdate_sum_df.values - young_workdate_sum_df.values, index=workdate_df.index,
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

    # 최초 공제 시기별 청년 근로자, 기타 근로자 연도별 근무 달(month) 수 추출
    deduction_yng_workdate_sums = []
    deduction_etc_workdate_sums = []
    target_year = years[-1]
    target_info_df = first_deduction_info_df.loc[first_deduction_info_df['year'] >= target_year - 2]
    for _, row in target_info_df.iterrows():
        year = row['year']
        index = row['index']
        deduction_yng_workdate_sums.append(young_workdate_sum_df.iloc[:, index:])
        deduction_etc_workdate_sums.append(etc_workdate_sum_df.iloc[:, index:])

    # 총합 공제 금액 계산
    deduction_tax = calculate_deduction_sum(deduction_tables, target_year)

    # 추가 납무 금액 계산
    refund_tax = calculate_tax_sum(deduction_tables, target_year)
    print('2022년 공제 받은 금액 : {} \n2022년 추가 납부 금액 : {}'.format(deduction_tax, refund_tax))
