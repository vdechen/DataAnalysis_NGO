import streamlit as st

# streamlit_app.py

import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
import pandas as pd
import numpy as np
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# create a connection object.
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1DTJpebBQeccOdhoSCg7qAOWOh0zySvvwj3hHLRtB2Ik/edit?usp=sharing").sheet1

# excel upload and transformation

arquivo = st.file_uploader('Insira o arquivo em excel. Antes de enviar, confira se os dados e a formatação estão conforme o modelo fornecido.', type = ['xls', 'xlsx'])

if arquivo: 
    df = pd.read_excel(arquivo)

    # add "month" and "year" columns
    month = df.iloc[0,1].month
    year = df.iloc[0,1].year
    data = str(year) + '-' + str(month) + '-' + '01'
    df['data'] = pd.to_datetime(data)
    df.drop(df.index[0:3], inplace = True)
    df.dropna(axis = 1, inplace = True, how = 'all')

    # reorder columns and drop unwanted rows 
    df.columns = ['dia', 'receita', 'depositante', 'despesas', 'favorecido', 'saldo', 'data']
    df = df[['receita', 'depositante', 'despesas', 'favorecido', 'data']]

    # create "expenses" dataframe and drop nulls
    expenses = df[['despesas', 'favorecido', 'data']].copy()
    expenses.dropna(subset = 'despesas', axis = 0, inplace=True)
    expenses.reset_index(drop = True, inplace = True)

    # create "income" dataframe and drop nulls
    income = df[['receita', 'depositante', 'data']].copy()
    income.dropna(subset = 'receita', axis = 0, inplace=True)
    income.reset_index(drop = True, inplace = True)

    # create categories for 'expenses'

    mask = expenses['favorecido'].str.contains('sal|intercamb|alim|lanch|temperinho|rest|pão|café|panif|doce|confeitaria|subway|gratificação|sabor|hong ju|mansa', flags = re.I)
    sal = np.where(mask, 'salários e auxílios alimentação', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = sal

    mask2 = expenses['favorecido'].str.contains('sup|super|hiper|hipper|mercado|bistek|milium|embala|atacad|cassol|agua|distrib|loja|zeus|comerc', flags = re.I)
    sup = np.where(mask2, 'suprimentos', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = sup

    mask3 = expenses['favorecido'].str.contains('medic|clínica|clinica|vet|remédio|farm|biofilia|gral|asamed|pet|cuidados|panvel|acupuntura|raio x|praiana|castração|tosa|cremat', flags = re.I)
    medic = np.where(mask3, 'medicações e veterinário', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = medic

    mask4 = expenses['favorecido'].str.contains('hosp|poeta|lilian ribeiro|lar|cuidadora|casa|canil|canis|inse', flags = re.I)
    hosp = np.where(mask4, 'hospedagem e manutenção de canis', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = hosp

    mask5 = expenses['favorecido'].str.contains('agro|ração|reção|pecuária|terra|arcadia', flags = re.I)
    rac = np.where(mask5, 'ração e agropecuária', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = rac

    mask7 = expenses['favorecido'].str.contains('combust|escap|posto|seguro|veíc|motorista|car|borrack|park|auto|taxi|táxi|tàxi|frete|motor|estac|floripeças|multa|mecanica|mecânica|mecãnica|parachoque|borrach|estrela|localiza', flags = re.I)
    trans = np.where(mask7, 'transporte', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = trans

    mask6 = expenses['favorecido'].str.contains('camis|malhas|mat|jebelus|agenda|vest|patchwork|plumas|bazar|graf|gráf|digital|mtools|eletr|hd|site|notebook|face|cópias|copia|plot|mídia|chip|marca|mix|print', flags = re.I)
    vend = np.where(mask6, 'bazar, divulgação e tecnologias', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = vend

    mask8 = expenses['favorecido'].str.contains('empr|apli|renda', flags = re.I)
    emp = np.where(mask8, 'empréstimos e aplicações', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = emp

    mask9 = expenses['favorecido'].str.contains('tarif|INSS|IR|taxa|IPVA|DARF|celesc|tim|distrit|alvará|cadastro|licen|trib|certif|dss|cmf', flags = re.I)
    tax = np.where(mask9, 'taxas, tarifas e impostos', expenses['favorecido'])
    expenses.loc[:,'favorecido'] = tax

    outros_mask = ~(expenses['favorecido'].isin(['salários e auxílios alimentação', 'suprimentos', 'medicações e veterinário', 'hospedagem e manutenção de canis', 'ração e agropecuária', 'bazar, divulgação e tecnologias', 'transporte', 'empréstimos e aplicações', 'taxas, tarifas e impostos']))
    expenses.loc[outros_mask,'favorecido'] = "outros"

    # create categories for income

    mask = income['depositante'].str.contains('doaç|ração|v.d.|\d|DD|cielo|cielo|pag|pic', regex = True, flags = re.I)
    doa = np.where(mask, 'doações e vendas', income['depositante'])
    income.loc[:,'depositante'] = doa

    mask2 = income['depositante'].str.contains('empr|apli|resg|rend', regex = True, flags = re.I)
    emp = np.where(mask2, 'empréstimos e aplicações', income['depositante'])
    income.loc[:,'depositante'] = emp

    mask3 = income['depositante'].str.contains('Pista', regex = True, flags = re.I)
    proj = np.where(mask3, 'projeto Autopista Litoral Sul', income['depositante'])
    income.loc[:,'depositante'] = proj

    mask4 = income['depositante'].str.contains('justiça|PMF ', regex = True, flags = re.I)
    gov = np.where(mask4, 'governo', income['depositante'])
    income.loc[:,'depositante'] = gov

    mask5 = income['depositante'].str.contains('div|tran|int|seguro|rog|BB|dif', regex = True, flags = re.I)
    out = np.where(mask5, 'outros', income['depositante'])
    income.loc[:,'depositante'] = out

    #converting data types
    expenses['despesas'] = expenses['despesas'].astype(str).str.strip()
    expenses['despesas'] = expenses['despesas'].str.replace(',', '')
    expenses['despesas'] = expenses['despesas'].astype(float)
    income['receita'] = income['receita'].astype(str).str.strip()
    income['receita'] = income['receita'].str.replace(',', '')
    income['receita'] = income['receita'].astype(float)
    expenses['data'] = expenses['data'].astype(str)
    income['data'] = income['data'].astype(str)

    st.write(income.values.tolist())
    

