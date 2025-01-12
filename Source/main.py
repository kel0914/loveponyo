#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Dash 앱 초기화
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 엑셀 파일 로드 및 중복제거
dataset = pd.read_excel('output.xlsx')
dataset['startDate'] = pd.to_datetime(dataset['startDate'])
dataset['endDate'] = pd.to_datetime(dataset['endDate'])
dataset2 = dataset.drop_duplicates('type')
선택된_열 = dataset[['startDate', 'endDate', 'unit', 'type', 'value', 'Metadata_0']]

# 'type' 열이 있는지 확인 후 리스트로 변환
if 'type' in dataset2.columns:
    list_from_column = dataset2['type'].dropna().tolist()  # NaN 값 제거
else:
     list_from_column = []

# 탑 섹션 정의
top = html.Div()

# 체크박스 생성
checkboxes = [
    html.Div(
        [
            dcc.Checklist(
                options=[{'label': item, 'value': item}],
                id=f'checkbox-{i}',
                inline=True
            )
        ],
        style={'margin-bottom': '1px'}
    )
    for i, item in enumerate(list_from_column)
]

# 사이드바 정의
sidebar = html.Div(
    [
        #html.P('사이드바'),
        html.Label("날짜 범위 선택:"),
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=dataset['startDate'].min().date(),
            end_date=dataset['endDate'].max().date(),
            display_format='YYYY-MM-DD',
            style={'margin-top': '10px'}
        ),
        html.Label("타입:"),
        html.Div(checkboxes)
    ],
    style={
        'overflow-y': 'auto',
        'max-height': '90vh',
        'padding': '10px'
    }
)

# 컨텐츠 정의
content = html.Div(
    id='content-display',
    children=[
        html.P('테이블'),
        dash_table.DataTable(
            id='data-table',
            columns=[{"name": col, "id": col} for col in 선택된_열.columns],
            data=선택된_열.to_dict('records'),
            page_size=10
        ),
        dcc.Graph(id='data-graph')
    ]
)

# 레이아웃 정의
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(top, width=12, className='bg-danger'),
            style={"height": "10vh"}
        ),
        dbc.Row(
            [
                dbc.Col(sidebar, width=3, className='bg-light'),
                dbc.Col(content, width=9)
            ],
            style={"height": "90vh"}
        )
    ],
    fluid=True
)

# 그래프 및 테이블 업데이트 콜백 정의
@app.callback(
    [Output('data-graph', 'figure'),
     Output('data-table', 'data')],
    [Input(f'checkbox-{i}', 'value') for i in range(len(list_from_column))] +
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_output(*args):
    selected_items = [item for sublist in args[:-2] if sublist for item in sublist]
    start_date = args[-2]
    end_date = args[-1]

    # 데이터 필터링
    filtered_df = dataset.copy()
    if selected_items:
        filtered_df = filtered_df[filtered_df['type'].isin(selected_items)]
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        filtered_df = filtered_df[
            (filtered_df['startDate'] >= start_date) & 
            (filtered_df['endDate'] <= end_date)
        ]

    # 그래프 업데이트
    fig = go.Figure()
    for item in selected_items:
        df_by_type = filtered_df[filtered_df['type'] == item]
        fig.add_trace(
            go.Scatter(
                x=df_by_type['startDate'],
                y=df_by_type['value'],
                mode='lines',
                name=item
            )
        )

    fig.update_layout(
        title='그래프',
        xaxis_title='시작 날짜',
        yaxis_title='값',
        width=1000,
        showlegend=True
    )

    # 데이터 테이블 업데이트
    table_data = filtered_df.to_dict('records')

    return fig, table_data

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)


# In[ ]:




