#!/usr/bin/env python
# coding: utf-8

# In[7]:


#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import re

def xml_to_excel(import_filename, output_filename):
    # 파일 경로 유효성 검사
    if import_filename is None:
        raise ValueError("You must specify an input filename.")
    if output_filename is None:
        raise ValueError("You must specify an output filename.")
    
    # 파일 크기 및 예상 처리 시간 출력
    file_size = os.path.getsize(import_filename)
    print(f"File size: {file_size / (1024**2):.2f} MiB")
    print(f"Estimated import time at 5 MiB/s: {round(file_size / (5 * 1024**2))} seconds")
    
    # 타이머 시작
    start_time = datetime.now()
    print(f"Import started at: {start_time}")
    
    # XML 파일 로드
    tree = ET.parse(import_filename)
    root = tree.getroot()
    
    # 'Record' 요소 추출
    records = root.findall(".//Record")
    data = []
    
    for record in records:
        record_data = record.attrib
        data.append(record_data)
        
    # 데이터프레임으로 변환
    health_data = pd.DataFrame(data)
    
    # 필요한 열만 유지
    required_columns = {'type', 'value', 'unit', 'startDate', 'endDate'}
    if not required_columns.issubset(health_data.columns):
        raise ValueError("The XML data does not contain the required columns.")
    
    health_data = health_data[list(required_columns)]
    
    # 'value'를 숫자로 변환
    if health_data['value'].apply(lambda x: str(x).isdigit()).all():
        health_data['value'] = health_data['value'].astype(float)

    # 값이 글자가 포함되어 있지 않으면 숫자형태로 변환하는 함수
    def convert_to_float_if_no_letters(value):
        if value.replace('.', '', 1).isdigit():  # 문자열에서 소수점을 제거한 후 숫자만 있는지 확인
            try:
                return float(value)
            except ValueError:
                return value  # 변환할 수 없는 경우 원래 값 반환
        else:
            return value  # 글자가 포함된 경우 원래 값 반환

    # 'value' 열에 함수 적용
    health_data['value'] = health_data['value'].apply(convert_to_float_if_no_letters)
    
        
    # 'type' 열 정리
    health_data['type'] = health_data['type'].apply(lambda x: x.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', ''))

    # 'startDate'와 'endDate'를 datetime 형식으로 변환하고 timezone 제거
    health_data['startDate'] = pd.to_datetime(health_data['startDate']).dt.tz_localize(None)
    health_data['endDate'] = pd.to_datetime(health_data['endDate']).dt.tz_localize(None)
    
    # 추가 시간 관련 열 생성
    time_columns2 = ['eyear', 'emonth', 'emonth_name', 'eday', 'eday_name', 'edate', 'ehour', 'eminutes']
    time_columns = ['syear', 'smonth', 'smonth_name', 'sday', 'sday_name', 'sdate', 'shour', 'sminutes']

    for col, func in zip(time_columns, [lambda x: x.year, lambda x: x.month, lambda x: x.month_name(), lambda x: x.day, lambda x: x.day_name(), lambda x: x.date(), lambda x: x.hour, lambda x: x.minute]):
        health_data[col] = health_data['startDate'].apply(func).astype('category')

    for col, func in zip(time_columns2, [lambda x: x.year, lambda x: x.month, lambda x: x.month_name(), lambda x: x.day, lambda x: x.day_name(), lambda x: x.date(), lambda x: x.hour, lambda x: x.minute]):
        health_data[col] = health_data['endDate'].apply(func).astype('category')
    
    # 중복 데이터 제거
    health_data = health_data.drop_duplicates()
    
    # Excel 파일로 저장
    health_data.to_excel(output_filename, index=False, engine='openpyxl')
    print(f"Data successfully saved to {output_filename}")
    
    # 타이머 종료 및 처리 시간 계산
    end_time = datetime.now()
    running_time = (end_time - start_time).total_seconds()
    print(f"Import finished at: {end_time}")
    print(f"Time for import: {round(running_time)} seconds")
    print(f"File size/running time: {file_size / running_time:.2f} MiB per second")

# Example usage
xml_to_excel('export.xml', 'output.xlsx')


# In[18]:


#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os

def xml_to_excel(import_filename, output_filename):
    # 파일 경로 유효성 검사
    if import_filename is None:
        raise ValueError("You must specify an input filename.")
    if output_filename is None:
        raise ValueError("You must specify an output filename.")
    
    # 파일 크기 및 예상 처리 시간 출력
    file_size = os.path.getsize(import_filename)
    print(f"File size: {file_size / (1024**2):.2f} MiB")
    print(f"Estimated import time at 5 MiB/s: {round(file_size / (5 * 1024**2))} seconds")
    
    # 타이머 시작
    start_time = datetime.now()
    print(f"Import started at: {start_time}")
    
    # XML 파일 로드
    tree = ET.parse(import_filename)
    root = tree.getroot()
    
    # 'Record' 요소 추출
    records = root.findall(".//Record")
    data = []
    metadata_columns = set()
    
    for record in records:
        record_data = record.attrib
        
        # 'MetadataEntry' 요소의 '@value' 속성 추출
        metadata_entries = record.findall('.//MetadataEntry')
        metadata_values = {f"Metadata_{i}": entry.get('value') for i, entry in enumerate(metadata_entries)}
        
        # Update metadata columns
        metadata_columns.update(metadata_values.keys())
        
        # Merge record attributes with metadata values
        combined_data = record_data.copy()
        combined_data.update(metadata_values)
        
        data.append(combined_data)
    
    # 데이터프레임으로 변환
    health_data = pd.DataFrame(data)
    
    # 기본적으로 필요한 열
    required_columns = {'type', 'value', 'unit', 'startDate', 'endDate'}
    
    # 모든 열 추가 (기본 열 + 동적으로 생성된 MetadataEntry 열)
    all_columns = required_columns.union(metadata_columns)
    
    # 데이터프레임에서 모든 열 선택
    health_data = health_data[list(all_columns)]
    
    # 'value'를 숫자로 변환하는 함수
    def convert_to_float_if_no_letters(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    
    # 'value' 열에 함수 적용
    if 'value' in health_data.columns:
        health_data['value'] = health_data['value'].apply(convert_to_float_if_no_letters)
    
    # 'type' 열 정리
    if 'type' in health_data.columns:
        health_data['type'] = health_data['type'].apply(lambda x: x.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', ''))

    # 'startDate'와 'endDate'를 datetime 형식으로 변환하고 timezone 제거
    if 'startDate' in health_data.columns:
        health_data['startDate'] = pd.to_datetime(health_data['startDate']).dt.tz_localize(None)
    if 'endDate' in health_data.columns:
        health_data['endDate'] = pd.to_datetime(health_data['endDate']).dt.tz_localize(None)
    
    # 추가 시간 관련 열 생성
    time_columns2 = ['eyear', 'emonth', 'emonth_name', 'eday', 'eday_name', 'edate', 'ehour', 'eminutes']
    time_columns = ['syear', 'smonth', 'smonth_name', 'sday', 'sday_name', 'sdate', 'shour', 'sminutes']

    if 'startDate' in health_data.columns:
        for col, func in zip(time_columns, [lambda x: x.year, lambda x: x.month, lambda x: x.month_name(), lambda x: x.day, lambda x: x.day_name(), lambda x: x.date(), lambda x: x.hour, lambda x: x.minute]):
            health_data[col] = health_data['startDate'].apply(func).astype('category')

    if 'endDate' in health_data.columns:
        for col, func in zip(time_columns2, [lambda x: x.year, lambda x: x.month, lambda x: x.month_name(), lambda x: x.day, lambda x: x.day_name(), lambda x: x.date(), lambda x: x.hour, lambda x: x.minute]):
            health_data[col] = health_data['endDate'].apply(func).astype('category')
    
    # 중복 데이터 제거
    health_data = health_data.drop_duplicates()
    
    # Excel 파일로 저장
    health_data.to_excel(output_filename, index=False, engine='openpyxl')
    print(f"Data successfully saved to {output_filename}")
    
    # 타이머 종료 및 처리 시간 계산
    end_time = datetime.now()
    running_time = (end_time - start_time).total_seconds()
    print(f"Import finished at: {end_time}")
    print(f"Time for import: {round(running_time)} seconds")
    print(f"File size/running time: {file_size / running_time:.2f} MiB per second")

# Example usage
xml_to_excel('export.xml', 'output.xlsx')


# In[ ]:




