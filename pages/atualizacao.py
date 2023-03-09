import streamlit as st

# streamlit_app.py

import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
import pandas as pd
import re

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

# Perform SQL query on the Google Sheet.
# Uses st.cache_data to only rerun when the query changes or after 10 min.

def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

# Print results.

arquivo = st.file_uploader('Insira o arquivo em excel', type = ['xls', 'xlsx'])
df = pd.read_excel(arquivo)

# add "month" and "year" columns, reorder columns, drop unwanted rows and save dataframes as excel files
month = df.iloc[0,1].month
year = df.iloc[0,1].year
data = str(year) + '-' + str(month) + '-' + '01'
df['data'] = pd.to_datetime(data)
df.drop(df.index[0:3], inplace = True)
df.columns = ['dia', 'receita', 'depositante', 'despesas', 'favorecido', 'saldo', 'data']
df = df[['receita', 'depositante', 'despesas', 'favorecido', 'data']]
df['filler1'] = '1'
df['filler2'] = '2'
df['filler3'] = '3'
df['filler4'] = '4'

st.write(df)

