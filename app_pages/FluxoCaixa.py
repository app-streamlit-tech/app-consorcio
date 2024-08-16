import streamlit as st
from datetime import datetime as dt
import pandas as pd
from .functions import convert_number

def fluxo_caixa(df_sales, df_expenses):
    st.title('Fluxo de Caixa')

    # df_expenses = pd.read_excel("sheets/despesas.xlsx", converters={'data_despesa':dt.date})
    # df_sales = pd.read_excel("sheets/saless.xlsx", converters={'data_venda':dt.date})

    # df_temp_sales = pd.DataFrame(columns=['id_funcionario','nome_funcionario','id_produto','nome_produto','placa_carro','valor_venda','data_venda','taxa_comissao','valor_comissao','valor_liquido'])
    # df_sales = pd.concat([df_sales, df_temp_sales], ignore_index=True)

    df_sales['data_venda'] = pd.to_datetime(df_sales['data_venda'], format='%Y-%m-%d')
    df_expenses['data_despesa'] = pd.to_datetime(df_expenses['data_despesa'], format='%Y-%m-%d')

    # df_sales['date_col'] = df_sales['data_venda'].map(lambda x: f'{x.year}/{x.month}')
    # df_expenses['date_col'] = df_expenses['data_despesa'].map(lambda x: f'{x.year}/{x.month}')

    date_col_sales = list(set(df_sales['data_venda_abv']))
    date_col_desp = list(set(df_expenses['data_despesa_abv']))
    date_col = list(set(date_col_sales + date_col_desp))
    date_col.sort(reverse=True)

    with st.container():

        # date_validation = False
        date_selected = st.multiselect('Selecione a(s) Data(s)', date_col, key='date_caixa')

        if len(date_selected) > 0:
            df_sales_up = pd.DataFrame(columns=df_sales.columns)
            for date in date_selected:
                year_selected = date.split('/')[0]
                month_selected = date.split('/')[1]
                df_temp_sales = df_sales.loc[(df_sales['data_venda'].dt.year == int(year_selected)) & (df_sales['data_venda'].dt.month == int(month_selected))]
                df_sales_up = pd.concat([df_sales_up, df_temp_sales])

            df_expenses_up = pd.DataFrame(columns=df_expenses.columns)
            for date in date_selected:
                year_selected = date.split('/')[0]
                month_selected = date.split('/')[1]
                df_temp_desp = df_expenses.loc[(df_expenses['data_despesa'].dt.year == int(year_selected)) & (df_expenses['data_despesa'].dt.month == int(month_selected))]
                df_expenses_up = pd.concat([df_expenses_up, df_temp_desp])

            # date_validation = True

        else:
            df_sales_up = df_sales
            df_expenses_up = df_expenses

    with st.container():

        total_despesas = df_expenses_up['valor_despesa'].sum()
        total_despesas_str = convert_number(total_despesas)
        total_vendas = df_sales_up['valor_venda'].sum()
        total_vendas_str = convert_number(total_vendas)
        total_comissao = df_sales_up['valor_comissao'].sum()
        total_comissao_str = convert_number(total_comissao)
        total_receita = df_sales_up['valor_receita'].sum()
        total_receita_str = convert_number(total_receita)
        total_lucro = total_vendas - total_despesas
        total_lucro_str = convert_number(total_lucro)

        st.subheader('Valor de Venda')
        st.write(f'R$ {total_vendas_str}')

        st.subheader('Valor de Comissão')
        st.write(f'R$ {total_comissao_str}')

        st.subheader('Valor de Receita')
        st.write(f'R$ {total_receita_str}')

        # st.subheader('Despesas')
        # st.write(f'R$ {total_despesas_str}')

        # st.subheader('Lucro')
        # st.write(f'R$ {total_lucro_str}')


    with st.container():

        df_sales_graph = df_sales_up[['data_venda_abv','valor_comissao','valor_receita']].groupby('data_venda_abv').sum().reset_index() # ,'valor_venda','valor_liquido'
        df_expenses_graph = df_expenses_up[['data_despesa_abv','valor_salario']].groupby('data_despesa_abv').sum().reset_index()

        df_sales_graph.rename(columns={'data_venda_abv':'data_abv'}, inplace=True)
        df_expenses_graph.rename(columns={'data_despesa_abv':'data_abv'}, inplace=True)

        df_graph = pd.merge(df_sales_graph,df_expenses_graph,how='outer',on='data_abv').reset_index()
        # df_graph = df_expenses_graph.copy()
        df_graph['valor_salario'] = df_graph['valor_salario'].astype(float)
        df_graph['valor_comissao'] = df_graph['valor_comissao'].astype(float)
        df_graph['valor_receita'] = df_graph['valor_receita'].astype(float)
        # df_graph['lucro'] = df_graph['valor_venda'] - df_graph['valor_despesa']
        
        st.subheader('Gráfico')

        col_names = {'Comissão': 'valor_comissao', 'Receita': 'valor_receita'}
        col_selected = st.multiselect('Selecione a(s) Coluna(s)', list(col_names.keys()), default=list(col_names.keys()))
        list_col_selected = [col_names[x] for x in col_selected]

        if len(date_selected) == 1:

            df_graph_bar = df_graph[list_col_selected].T.rename(columns={0:'Valor'}) # 'valor_venda','valor_despesa','lucro'
            st.bar_chart(df_graph_bar)
        else:
            st.line_chart(df_graph, x='data_abv', y=list_col_selected) # 'valor_venda','valor_despesa','lucro'

    return df_sales, df_expenses
