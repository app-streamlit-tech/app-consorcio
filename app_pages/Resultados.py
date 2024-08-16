import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
import numpy as np

def resultados(df_sales):
    '''Results window'''

    st.title("Resultados")

    date_col = list(set(list(df_sales['data_venda_abv'])))
    date_col.sort(reverse=True)
    # df_sales['id_prod_caract'] = df_sales['id_prod_caract'].astype(str)
    df_sales['data_venda'] = pd.to_datetime(df_sales['data_venda'])

    adm_col = list(set(list(df_sales['nome_adm'])))
    adm_col.sort()

    df_sales_up = df_sales.copy()

    with st.container():

        col_date, col_adm = st.columns(2)
        with col_date:
            date_selected = st.multiselect('Selecione a(s) Data(s)', date_col, default = date_col[0])
            if len(date_selected) == 0:
                date_selected = date_col
        
        with col_adm:
            adm_selected = st.multiselect('Selecione a(s) Administradora(s)', adm_col)
            if len(adm_selected) == 0:
                adm_selected = adm_col

        df_sales_up = df_sales.loc[(df_sales['data_venda_abv'].isin(date_selected)) & (df_sales_up['nome_adm'].isin(adm_selected))]

    # Create DFs
    df_emp_up = df_sales_up[['id_funcionario','nome_funcionario','valor_venda']].groupby(by=['id_funcionario','nome_funcionario']).sum().sort_values(by='valor_venda', ascending=False).reset_index()
    df_emp_up_count = df_sales_up[['id_funcionario','nome_funcionario','valor_venda']].groupby(by=['id_funcionario','nome_funcionario']).count().sort_values(by='valor_venda', ascending=False).reset_index()
    df_emp_up_count.rename(columns={'valor_venda':'qtd'}, inplace=True)

    df_sales_up['adm_produto'] = df_sales_up['nome_adm'] + ' - ' + df_sales_up['nome_produto']
    df_prod_up = df_sales_up[['adm_produto','valor_venda']].groupby(by=['adm_produto']).sum().sort_values(by='valor_venda', ascending=False).reset_index()
    df_prod_up_count = df_sales_up[['adm_produto','valor_venda']].groupby(by=['adm_produto']).count().sort_values(by='valor_venda', ascending=False).reset_index()
    df_prod_up_count.rename(columns={'valor_venda':'qtd'}, inplace=True)
    df_prod_up_count['qtd'] = df_prod_up_count['qtd'].astype(int)

    df_prod_up_mean = df_sales_up[['adm_produto','valor_venda']].groupby(by=['adm_produto']).mean().sort_values(by='valor_venda', ascending=False).reset_index()
    df_prod_up_mean.rename(columns={'valor_venda':'media'}, inplace=True)
    df_prod_up_mean['media'] = df_prod_up_mean['media'].astype(float)

    df_comissao = df_sales_up[['id_funcionario','nome_funcionario','valor_comissao']].groupby(by=['id_funcionario','nome_funcionario']).sum().sort_values(by='valor_comissao', ascending=False).reset_index()
    df_comissao['valor_comissao'] = df_comissao['valor_comissao'].astype(float)

    def absolute_value(val):
        a  = np.round(val/100.*df_prod_up_count['qtd'].sum(), 0)
        return int(a)

    sale_menu = option_menu(None, ['Funcionários', 'Produtos'], orientation='horizontal')
    if sale_menu == 'Funcionários':
        with st.container():
            st.subheader("Funcionários")

            col1, col2 = st.columns(2)

            with col1:
                st.text('Valor de venda')
                st.bar_chart(df_emp_up, x='nome_funcionario', y='valor_venda', x_label='Vendedor', y_label='Valor de venda')

                st.text('Valor da comissão')
                st.bar_chart(df_comissao, x='nome_funcionario', y='valor_comissao', x_label='Vendedor', y_label='Valor de comissão')

            with col2:
                st.text('Quantidade de cotas')

                fig1, ax1 = plt.subplots()
                ax1.pie(df_emp_up_count['qtd'], labels=df_emp_up_count['nome_funcionario'], autopct=absolute_value, startangle=90) # autopct='%1.1f%%'
                ax1.axis('equal')

                st.pyplot(fig1)

    if sale_menu == 'Produtos':
        with st.container():
            st.subheader("Produtos")

            col1, col2 = st.columns(2)

            with col1:
                st.text('Quantidade de cotas')
                fig1, ax1 = plt.subplots()
                ax1.pie(df_prod_up_count['qtd'], labels=df_prod_up_count['adm_produto'], autopct=absolute_value, startangle=90) # autopct='%1.1f%%'
                ax1.axis('equal')
                st.pyplot(fig1)

            with col2:
                st.text('Valor de venda')
                st.bar_chart(df_prod_up, x='adm_produto', y='valor_venda', x_label='Produto', y_label='Valor de venda')

                st.text('Valor medio por cota')
                st.bar_chart(df_prod_up_mean, x='adm_produto', y='media', x_label='Produto', y_label='Média')

    # return df_sales
