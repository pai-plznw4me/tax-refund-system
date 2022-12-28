import pandas as pd
import numpy as np

"""
TODO: 
1.장애인 여부, 
2. 임원 여부(제외), 
3. 60세 이상, 
4. 1년 미만 계약직(제외)
"""

xls = pd.ExcelFile('/Users/kimseongjung/Downloads/사업장가입자명부_20221222 (상실자포함).xls')
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

    # filter
    # 현재 년도 1월 1일부터 5년전 1월 1일 정보만을 가져온다. filter 된 데이터는 2017.1.1 일 이후 하루라도 근무함을 보증 한다.
    gap = 5
    today = pd.Timestamp.today()
    start_date = today.date().replace(year=today.year - gap, month=1, day=1)
    end_date = today.date().replace(month=1, day=1)
    mask = disqual_date.map(lambda x: x < start_date)
    target_df = target_df.loc[~mask]

    # 상시 근무 날짜를 계산한다.
    target_df['가상자격취득일'] = start_date
    target_df['가상자격상실일'] = disqual_date.fillna(today)
    # 2017.1.1 보다 늦게 자격을 취득했다면 그대로 두고 2017.1.1 보다 일찍 자격을 취득했다면 2017.1.1 로 변경한다.
    mask = target_df['자격취득일'].map(lambda x: x > start_date)
    target_df['가상자격취득일'].loc[mask] = target_df['자격취득일'].loc[mask]

    virtual_acquisi_date = pd.to_datetime(target_df['가상자격취득일'])
    virtual_disqual_date = pd.to_datetime(target_df['가상자격상실일'])

    target_df['diff_month'] = (virtual_disqual_date - virtual_acquisi_date) / np.timedelta64(1, 'M')
    target_df['diff_month'] = target_df['diff_month'].map(np.ceil).map(int)

    # 생년 월일을 계산한다.
    birth_date = target_df.iloc[:, 0].map(lambda x: x[:6])
    birth_index = target_df.iloc[:, 0].map(lambda x: x[7]).map(int)
    prefix_mask = birth_index < 3
    birth_date.loc[prefix_mask] = birth_date.loc[prefix_mask].map(lambda x: '19' + str(x))
    birth_date.loc[~prefix_mask] = birth_date.loc[~prefix_mask].map(lambda x: '20' + str(x))
    pass

    # 청년 근무 날짜를 계산한다. 현재 날짜로 부터 만 30세가 되는 날짜를 계산한다.
    # 청년 허용 날짜:  30년
    young_offset = 30
    target_df['청년자격취득일'] = pd.to_datetime(birth_date)
    target_df['청년자격상실일'] = target_df['청년자격취득일'].map(lambda x: x + pd.DateOffset(year=young_offset))
    print()
    pass
