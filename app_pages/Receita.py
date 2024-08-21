import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from .functions import comissoes, convert_column_types, convert_number, save_table

def receita(df_sales, df_income):

    st.title('Receita')

    today = dt.now()
    list_date_col = []
    for i in range(-6, 7):
        data = dt.now() + relativedelta(months=i)
        data_str = f'{data.year}/0{data.month}' if len(str(data.month)) == 1 else f'{data.year}/{data.month}'
        list_date_col.append(data_str)

    list_func_col = list(set(df_sales['nome_funcionario']))
    list_func_col = ['Todos'] + list_func_col

    with st.container():
        # col1, col2 = st.columns(2)
        # with col1:
        date_selected = st.selectbox('Selecione a data', list_date_col, index=6, key='income_date_selected')
        if len(date_selected) > 0:
            year_selected = date_selected.split('/')[0]
            month_selected = date_selected.split('/')[1]
            cur_month_datetime = dt(int(year_selected), int(month_selected), 10)
        else:
            cur_month_datetime = dt(today.year, today.month, 10)

        # with col2:
        #     emp_selected = st.selectbox('Selecione o vendedor', list_func_col, index=0)

    df_comissao_geral, df_comissao_filt, dict_columns, df_holerite = comissoes(df_sales, df_income, cur_month_datetime.date(), 'id_income')
    # if emp_selected != 'Todos':
    #     df_comissao_filt = df_comissao_filt[df_comissao_filt['Vendedor'] == emp_selected]
    #     df_comissao_geral = df_comissao_geral[df_comissao_geral['Vendedor'] == emp_selected]
    #     df_holerite = df_holerite[df_holerite['Vendedor'] == emp_selected]

    with st.container():
        
        valor_total_global = 0
        dict_month_value = {}
        selected_cols = ['Produto'] + list(df_comissao_geral.columns[13:])
        df_group_prod = df_comissao_geral[selected_cols].groupby('Produto').sum().reset_index()
        for idx in dict_columns:
            value = df_comissao_geral[dict_columns[idx]].sum()
            valor_total_global += value
            dict_month_value[dict_columns[idx]] = [value]
        
        df_month_total_value = pd.DataFrame(dict_month_value).T
        df_month_total_value.rename(columns={0: 'Valor'}, inplace=True)
        
        list_prod_filt = list(df_group_prod['Produto'])
        list_valor_total_receita = []

        for prod in list_prod_filt:
            df_prod_filt = df_group_prod[df_group_prod['Produto'] == prod]
            valor_total_receita = 0

            for idx in dict_columns:
                if idx != 0:
                    valor_total_receita += df_prod_filt[dict_columns[idx]].sum()
                    
            list_valor_total_receita.append(valor_total_receita)

        df_comissao_filt['Receita Futura (R$)'] = list_valor_total_receita

        data = pd.melt(df_month_total_value.reset_index(), id_vars=["index"])

        # Horizontal stacked bar chart
        chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("value", type="quantitative", title="", axis=alt.Axis(labels=False)),
                y=alt.Y("index", type="nominal", title="",  sort=None),
                text='value',
                color=alt.Color("variable", type="nominal", title="", legend=None),
                # order=alt.Order("variable"), #, sort="descending"
            ).properties(
                # width=800,
                height=430
            )
        )
        chart = chart.mark_bar() + chart.mark_text(align='left', dx=2)
        valor_mes_selecionado = df_comissao_filt[dict_columns[0]].sum()
        valor_mes_selecionado_str = convert_number(valor_mes_selecionado)
        valor_comissoes_futuras = valor_total_global - valor_mes_selecionado
        valor_comissoes_futuras_str = convert_number(valor_comissoes_futuras)

        col1, col2 = st.columns(2)

        with col1:

            col3, col4 = st.columns(2)
            with col3:
                st.subheader('Total de receita do mês')
                st.write(f'R$ {valor_mes_selecionado_str}')
            
            with col4:
                st.subheader('Total de receita futura')
                st.write(f'R$ {valor_comissoes_futuras_str}')

            st.subheader('Receita a ser paga')
            df_comissao_filt_view = convert_column_types(df_comissao_filt, df_comissao_filt.columns[1:], [])
            st.write(df_comissao_filt_view)

            # if emp_selected != 'Todos':
            #     st.subheader('Holerite')
            #     st.write(df_holerite)

            #     save_holerite_bt = st.button('Baixar Holerite')
            #     if save_holerite_bt:
            #         save_table(f'Holerite {emp_selected}', df_holerite)
            #         st.success("Tabela salva com sucesso!")

        with col2:
            # col5, col6 = st.columns(2)
            # with col5:
            #     st.subheader('Valor do mês selecionado')
            #     st.write(f'R$ {valor_mes_selecionado_str}')

            # with col6:
            #     st.subheader('Valor total global')
            #     st.write(f'R$ {valor_total_global_str}')

            with st.container():
                st.subheader('Valor total mensal')
                st.altair_chart(chart, use_container_width=True)

    with st.container():
        st.subheader('Receita')

        list_float_col_holerite = ['Crédito (R$)','Comissão Total (%)','Comissão Atual (%)'] + list(df_holerite.columns[12:])
        df_holerite_view = convert_column_types(df_holerite, list_float_col_holerite, ['Alocação'])

        st.write(df_holerite_view)

        save_table(df_holerite_view, "Baixar Receita")
        # save_holerite_bt = st.button('Baixar Receita')
        # if save_holerite_bt:
        #     save_table(f'Receita', df_holerite)
        #     st.success("Tabela salva com sucesso!")

    with st.container():
        st.subheader('Tabela geral de receitas')
        list_float_col_geral = ['Crédito (R$)','Comissão Total (%)','Comissão Atual (%)'] + list(df_comissao_geral.columns[12:])
        df_comissao_geral_view = convert_column_types(df_comissao_geral, list_float_col_geral, ['Alocação'])
        st.write(df_comissao_geral_view)
