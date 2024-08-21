import pandas as pd
import numpy as np
import streamlit as st
import os
import io
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from core.db import Db_pg

def convert_column_types(df, list_float_col, list_date_col):
    df_view = df.copy()
    # df_view[list_float_col] = df_view[list_float_col].astype(str)
    for col in list_float_col:
        df_view[col] = df_view[col].map(lambda x: f'{float(x):_.2f}'.replace('.',',').replace('_','.') if pd.isna(x) == False else '')
    for col in list_date_col:
        df_view[col] = df_view[col].map(lambda x: dt.strftime(x, '%d/%m/%Y'))
    return df_view

def convert_number(value) -> str:
    '''Convert format number to brazilian type'''

    if pd.isna(value):

        return np.nan
    
    else:
        value = float(value)
        sep_value = f'{value:_.2f}'
        res = sep_value.replace('.',',').replace('_','.')
    
        return res

def get_columns(table: str, cur) -> list:
    '''Get table columns'''

    cur.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}';")
    columns = cur.fetchall()
    table_columns = [x[0] for x in columns]

    return table_columns

def save_table(df, label, area=None, emp_selected=None, list_func_col=None):
    '''Save table in Downloads file'''

    # buffer to use for excel writer
    buffer = io.BytesIO()
    # writer = pd.ExcelWriter(buffer, engine='xlsxwriter')

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:

        if area == 'RH':
            if emp_selected != 'Todos':
                df.to_excel(writer, index=False, sheet_name=emp_selected)
            else:
                for func in list_func_col:
                    if func != 'Todos':
                        df_holerite_temp = df[df['Vendedor'] == func]
                        df_holerite_temp.to_excel(writer, index=False, sheet_name=func)
        else:
            df.to_excel(writer, index=False)

        writer.close()

        st.download_button(
            label=label,
            data=buffer,
            file_name='large_df.xlsx',
            mime='application/vnd.ms-excel'
        )

def comissoes(df_sales, df_select, cur_month_date, id_name): # cur_month_datetime=dt.now()
    
    # cur_month_date = cur_month_datetime.date()
    cur_month_datetime = dt(cur_month_date.year, cur_month_date.month, cur_month_date.day)

    # Filtrando dataframe pela data selecionada
    data_ultima_parcela = 'data_ultima_parcela' if id_name == 'id_prod_caract' else 'data_ultima_parcela_receita'
    df_sales_upd = df_sales[(df_sales[data_ultima_parcela] >= cur_month_date)]
    df_sales_upd = pd.merge(df_sales_upd, df_select[[id_name, 'qtd_parcelas', 'taxa_parcelas']])
    nr_max_parcelas = round((df_sales_upd[data_ultima_parcela].max() - cur_month_date).days/30) if pd.isna(df_sales_upd[data_ultima_parcela].max()) == False else 0
    
    dict_month_name = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    # Gerando o dataframe geral de comissões
    # df_comissao_geral = pd.DataFrame(columns=['Vendedor', 'Administradora', 'Produto', 'Projeto', 'Data da Venda', 'Nº Parcela'])
    if id_name == 'id_prod_caract':
        list_columns = ['Contrato','Vendedor', 'Alocação', 'Consorciado', 'Crédito (R$)', 'Administradora', 'Produto', 'Grupo', 'Cota', 'Qtd Parcelas', 'Nº Parcela', 'Comissão Total (%)', 'Comissão Atual (%)']
    else:
        list_columns = ['Contrato','Alocação', 'Consorciado', 'Crédito (R$)', 'Administradora', 'Produto', 'Grupo', 'Cota', 'Qtd Parcelas', 'Nº Parcela', 'Comissão Total (%)', 'Comissão Atual (%)']

    df_comissao_geral = pd.DataFrame(columns=list_columns)
    dict_columns = {}
    for i in range(nr_max_parcelas+1):
        date_temp = cur_month_datetime + relativedelta(months=i)
        nome_coluna = f'Parcela {dict_month_name[date_temp.month]}/{date_temp.year} (R$)'
        dict_columns[i] = nome_coluna
        df_comissao_geral[nome_coluna] = None

    df_holerite = pd.DataFrame(columns=list_columns)
    for row in df_sales_upd.itertuples():
        
        taxa_parcelas = row.taxa_parcelas
        if taxa_parcelas != '':
            list_taxa_parcelas = taxa_parcelas.split(' - ')
            nr_parcelas = len(list_taxa_parcelas)
            data_primeira_parcela = row.data_primeira_parcela
            valor_venda = float(row.valor_venda)

            month_1 = data_primeira_parcela.month
            year_1 = data_primeira_parcela.year
            month_2 = cur_month_date.month
            year_2 = cur_month_date.year

            if year_2 > year_1:
                month_2 = month_2 + 12 
            elif year_2 < year_1:
                month_1 = month_1 + 12
            
            diff_months = month_2 - month_1
            if diff_months < 0:
                comissao_atual = 0
            else:
                # try:
                comissao_atual = list_taxa_parcelas[diff_months]
                # except:
                #     print('-'*30)
                #     print(diff_months)
                #     print(list_taxa_parcelas)
                #     print(nr_parcelas)
                #     print(row)
                #     print('-'*30)
                #     raise

            # dict_result = {}
            # dict_result['Vendedor'] = row.nome_funcionario
            # dict_result['Administradora'] = row.nome_adm
            # dict_result['Produto'] = row.nome_produto
            # dict_result['Projeto'] = row.projeto
            # dict_result['Data da Venda'] = row.data_venda
            # dict_result['Nº Parcela'] = diff_months+1

            dict_holerite = {}
            if id_name == 'id_prod_caract':
                dict_holerite['Vendedor'] = row.nome_funcionario
            dict_holerite['Contrato'] = row.id_venda
            dict_holerite['Alocação'] = row.data_venda
            dict_holerite['Consorciado'] = row.nome_cliente
            dict_holerite['Crédito (R$)'] = row.valor_venda
            dict_holerite['Grupo'] = row.grupo
            dict_holerite['Cota'] = row.cota
            dict_holerite['Comissão Total (%)'] = row.taxa_comissao
            dict_holerite['Comissão Atual (%)'] = comissao_atual
            dict_holerite['Nº Parcela'] = diff_months+1
            dict_holerite['Qtd Parcelas'] = row.qtd_parcelas
            dict_holerite['Administradora'] = row.nome_adm
            dict_holerite['Produto'] = row.nome_produto

            dict_result = dict_holerite.copy()
            for i in range(diff_months, nr_parcelas):
                if i >= 0:
                    try:
                        valor_parcela = float(list_taxa_parcelas[i])/100 * float(valor_venda)
                    except:
                        print(row)
                    dict_result[dict_columns[i-diff_months]] = valor_parcela
                    
            df_holerite = pd.concat([df_holerite, pd.DataFrame([dict_holerite])], ignore_index=True)
            df_comissao_geral = pd.concat([df_comissao_geral, pd.DataFrame([dict_result])], ignore_index=True)
    if id_name == 'id_prod_caract':
        df_comissao_filt = df_comissao_geral[['Vendedor', dict_columns[0]]].groupby('Vendedor').sum()
        # df_comissao_filt = df_comissao_filt[df_comissao_filt[dict_columns[0]] > 0]
        df_comissao_filt.reset_index(inplace=True)
    else:
        df_comissao_filt = df_comissao_geral[['Produto', dict_columns[0]]].groupby('Produto').sum()
        # df_comissao_filt = df_comissao_filt[df_comissao_filt[dict_columns[0]] > 0]
        df_comissao_filt.reset_index(inplace=True)
    
    df_holerite[dict_columns[0]] = df_comissao_geral[dict_columns[0]]
    # df_holerite = df_holerite[(pd.isna(df_holerite[dict_columns[0]]) == False)]# & (df_holerite[dict_columns[0]] != 0)]

    # Filtrar DataFrames retirando as linhas com nº de parcelas negativas
    # df_comissao_geral = df_comissao_geral[df_comissao_geral['Nº Parcela'] >= 0]
    df_holerite = df_holerite[df_holerite['Nº Parcela'] > 0]

    return df_comissao_geral, df_comissao_filt, dict_columns, df_holerite

@st.cache_data(show_spinner=False)
def load_data(company_id):
    '''Load data from database'''

    cur, conn = Db_pg.connect()

    cur.execute(f"SELECT * FROM sales WHERE company_id = '{company_id}';")
    sales_list = list(cur.fetchall())
    table_sales_columns = [desc[0] for desc in cur.description]
    df_sales = pd.DataFrame(sales_list, columns=table_sales_columns)
    df_sales.drop(columns=['company_id'], inplace=True)
    df_sales['data_venda'] = pd.to_datetime(df_sales['data_venda'], format='%Y-%m-%d')
    df_sales['data_venda'] = df_sales['data_venda'].map(lambda x: x.date())
    df_sales['data_primeira_parcela'] = pd.to_datetime(df_sales['data_primeira_parcela'], format='%Y-%m-%d')
    df_sales['data_primeira_parcela'] = df_sales['data_primeira_parcela'].map(lambda x: x.date())
    df_sales['data_ultima_parcela'] = pd.to_datetime(df_sales['data_ultima_parcela'], format='%Y-%m-%d')
    df_sales['data_ultima_parcela'] = df_sales['data_ultima_parcela'].map(lambda x: x.date())
    # df_sales[['data_venda','data_primeira_parcela','data_ultima_parcela']] = df_sales[['data_venda','data_primeira_parcela','data_ultima_parcela']].astype('datetime64[ns]')
    df_sales[['valor_venda','taxa_comissao','valor_comissao','taxa_receita','valor_receita']] = df_sales[['valor_venda','taxa_comissao','valor_comissao','taxa_receita','valor_receita']].astype(float)

    # for row in df_sales.itertuples():
    #     for r in row:
    #         print(f'{r}: {type(r)}')

    cur.execute(f"SELECT * FROM employees WHERE company_id = '{company_id}';")
    employees_list = list(cur.fetchall())
    table_employees_columns = [desc[0] for desc in cur.description]
    df_employees = pd.DataFrame(employees_list, columns=table_employees_columns)
    df_employees.drop(columns=['company_id'], inplace=True)
    # df_employees[['data_adesao']] = df_employees[['data_adesao']].astype('datetime64[ns]')
    df_employees['data_adesao'] = pd.to_datetime(df_employees['data_adesao'], format='%Y-%m-%d')
    df_employees['data_adesao'] = df_employees['data_adesao'].map(lambda x: x.date())
    df_employees[['salario']] = df_employees[['salario']].astype(float)

    cur.execute(f"SELECT * FROM expenses WHERE company_id = '{company_id}';")
    despesa_list = list(cur.fetchall())
    table_despesa_columns = [desc[0] for desc in cur.description]
    df_despesa = pd.DataFrame(despesa_list, columns=table_despesa_columns)
    df_despesa.drop(columns=['company_id'], inplace=True)
    df_despesa['data_despesa'] = pd.to_datetime(df_despesa['data_despesa'], format='%Y-%m-%d')
    df_despesa['data_despesa'] = df_despesa['data_despesa'].map(lambda x: x.date())
    # df_despesa[['data_despesa']] = df_despesa[['data_despesa']].astype('datetime64[ns]')
    df_despesa[['valor_salario','valor_comissao','valor_despesa']] = df_despesa[['valor_salario','valor_comissao','valor_despesa']].astype(float)

    cur.execute(f"SELECT * FROM products WHERE company_id = '{company_id}';")
    products_list = list(cur.fetchall())
    table_products_columns = [desc[0] for desc in cur.description]
    df_products = pd.DataFrame(products_list, columns=table_products_columns)
    df_products.drop(columns=['company_id'], inplace=True)

    cur.execute(f"SELECT * FROM prod_caract WHERE company_id = '{company_id}';")
    prod_caract_list = list(cur.fetchall())
    table_prod_caract_columns = [desc[0] for desc in cur.description]
    df_prod_caract = pd.DataFrame(prod_caract_list, columns=table_prod_caract_columns)
    df_prod_caract.drop(columns=['company_id'], inplace=True)
    df_prod_caract[['taxa_comissao']] = df_prod_caract[['taxa_comissao']].astype(float)

    cur.execute(f"SELECT * FROM income WHERE company_id = '{company_id}';")
    income_list = list(cur.fetchall())
    table_income_columns = [desc[0] for desc in cur.description]
    df_income = pd.DataFrame(income_list, columns=table_income_columns)
    df_income.drop(columns=['company_id'], inplace=True)
    df_income[['taxa_comissao','contemplacao']] = df_income[['taxa_comissao','contemplacao']].astype(float)

    cur.execute(f"SELECT * FROM projects WHERE company_id = '{company_id}';")
    projects_list = list(cur.fetchall())
    table_products_columns = [desc[0] for desc in cur.description]
    df_projects = pd.DataFrame(projects_list, columns=table_products_columns)
    df_projects.drop(columns=['company_id'], inplace=True)

    cur.execute(f"SELECT s.id_funcionario, s.nome_adm, s.nome_funcionario, s.nome_produto, s.projeto, s.data_venda, s.data_primeira_parcela, s.data_ultima_parcela, s.valor_venda, s.valor_comissao, \
                pc.qtd_parcelas, pc.taxa_parcelas FROM sales AS s LEFT JOIN prod_caract AS pc on s.id_prod_caract = pc.id_prod_caract;")
    prod_sales_list = list(cur.fetchall())
    table_prod_sales_columns= [desc[0] for desc in cur.description]
    df_prod_sales = pd.DataFrame(prod_sales_list, columns=table_prod_sales_columns)
    df_prod_sales[['valor_venda','valor_comissao']] = df_prod_sales[['valor_venda','valor_comissao']].astype(float)
    # df_prod_sales[['data_venda','data_primeira_parcela','data_ultima_parcela']] = df_prod_sales[['data_venda','data_primeira_parcela','data_ultima_parcela']].astype('datetime64[ns]')
    df_prod_sales['data_venda'] = pd.to_datetime(df_prod_sales['data_venda'], format='%Y-%m-%d')
    df_prod_sales['data_venda'] = df_prod_sales['data_venda'].map(lambda x: x.date())
    df_prod_sales['data_primeira_parcela'] = pd.to_datetime(df_prod_sales['data_primeira_parcela'], format='%Y-%m-%d')
    df_prod_sales['data_primeira_parcela'] = df_prod_sales['data_primeira_parcela'].map(lambda x: x.date())
    df_prod_sales['data_ultima_parcela'] = pd.to_datetime(df_prod_sales['data_ultima_parcela'], format='%Y-%m-%d')
    df_prod_sales['data_ultima_parcela'] = df_prod_sales['data_ultima_parcela'].map(lambda x: x.date())

    cur.execute(f"SELECT * FROM administrators WHERE company_id = '{company_id}';")
    adm_list = list(cur.fetchall())
    table_adm_columns = [desc[0] for desc in cur.description]
    df_adm = pd.DataFrame(adm_list, columns=table_adm_columns)
    df_adm.drop(columns=['company_id'], inplace=True)

    Db_pg.disconnect(cur, conn)

    return df_sales, df_employees, df_despesa, df_products, df_prod_caract, df_projects, df_prod_sales, df_adm, df_income