import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import time, datetime as dt
from dateutil.relativedelta import relativedelta
import shortuuid
from core.db import Db_pg
from .functions import comissoes, save_table, convert_column_types

def on_click_sub(id_funcionario, df_employees, cur, conn):
    '''Delete employee from database'''

    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'emp_validation'] = False
    
    query = f"DELETE FROM employees WHERE id_funcionario = {id_funcionario};"
    cur.execute(query)
    conn.commit()

def registrar(cur, conn, company_id, df_employees, df_products, df_prod_caract, df_sales, df_projects, df_expenses, df_adm, df_income):
    st.title("Registro de Dados")

    if cur.closed:
        cur, conn = Db_pg.connect()

    df_sales = df_sales.sort_values('id_venda', ascending=False).reset_index(drop=True)
    df_projects = df_projects.sort_values('id_projeto', ascending=False).reset_index(drop=True)
    projects = list(df_projects['nome_projeto'].map(str))

    selected = option_menu(
        menu_title = None,
        options = ['Venda','Projeto','Vendedor','Produto'],#,'Salário'],
        icons = ['currency-dollar','folder','person','box'],#,'receipt-cutoff'],
        menu_icon = 'cast',
        orientation = 'horizontal',
        default_index = 0
    )

    if selected == 'Venda':
        administradoras = tuple(set(df_prod_caract['nome_adm']))
        funcionarios = tuple(df_employees['id_funcionario'].map(str) + ' - ' + df_employees['nome_funcionario'].map(str))
        projetos = tuple(set(df_prod_caract['projeto']))
        sale_menu = option_menu(None, ['Registrar', 'Atualizar', 'Deletar'], orientation='horizontal')
        if sale_menu == 'Registrar':
            st.subheader("Registrar Venda")
            
            nome_adm = st.selectbox('Administradora', administradoras)
            produtos = tuple(set(df_prod_caract[df_prod_caract['nome_adm'] == nome_adm]['nome_produto']))

            with st.form(key="reg_sales", clear_on_submit=True):
                
                # id_sales_atual = df_sales['id_venda'].max()
                # if pd.isna(id_sales_atual) == False:
                #     id_sales = int(id_sales_atual) + 1
                # else:
                #     id_sales = 1
                # short_id = shortuuid.ShortUUID()
                # id_sales = short_id.random(length=8)

                nome_produto = st.selectbox('Produto', produtos)
                id_func_s = st.selectbox('Vendedor', funcionarios)
                projeto_venda = st.selectbox('Projeto', projetos)
                nome_cliente = st.text_input('Nome do Cliente')
                id_sales = st.text_input('Contrato')
                grupo = st.number_input('Grupo', step=1)
                cota = st.number_input('Cota', step=1)
                valor_venda = st.number_input('Valor do Consórcio')
                data = st.date_input("Data da Venda", format= "DD/MM/YYYY")
                
                submit_prod = st.form_submit_button(label="Salvar")

                if submit_prod:
                    func = id_func_s.split(' - ')
                    id_funcionario = func[0]
                    nome_funcionario = func[1]

                    data_venda_abv = f'{data.year}/0{data.month}' if len(str(data.month)) == 1 else f'{data.year}/{data.month}'

                    # projeto_venda = df_employees.loc[df_employees['id_funcionario'] == int(id_funcionario), 'projeto'].values[0]
    
                    id_prod_caract = df_prod_caract.loc[(df_prod_caract['nome_produto'] == nome_produto) & (df_prod_caract['projeto'] == projeto_venda), 'id_prod_caract'].values[0]
                    qtd_parcelas = df_prod_caract.loc[(df_prod_caract['id_prod_caract'] == id_prod_caract), 'qtd_parcelas'].values[0]

                    data_primeira_parcela = data + relativedelta(months=1)
                    data_primeira_parcela_upd = dt(data_primeira_parcela.year, data_primeira_parcela.month, 10).date()
                    data_ultima_parcela = data + relativedelta(months=(qtd_parcelas))
                    data_ultima_parcela_upd = dt(data_ultima_parcela.year, data_ultima_parcela.month, 10).date()

                    taxa_comissao = float(df_prod_caract.loc[df_prod_caract['id_prod_caract'] == id_prod_caract, 'taxa_comissao'].values[0])
                    valor_comissao = round((taxa_comissao/100) * valor_venda, 2)

                    id_income = df_income.loc[(df_income['nome_produto'] == nome_produto), 'id_income'].values[0]
                    qtd_parcelas_receita = df_income.loc[(df_income['id_income'] == id_income), 'qtd_parcelas'].values[0]
                    data_ultima_parcela_income = data + relativedelta(months=(qtd_parcelas_receita))
                    data_ultima_parcela_income_upd = dt(data_ultima_parcela_income.year, data_ultima_parcela_income.month, 10).date()
                    taxa_receita = float(df_income.loc[df_income['nome_produto'] == nome_produto, 'taxa_comissao'].values[0])
                    valor_receita = round((taxa_receita/100) * valor_venda, 2)

                    df_temp_sales = pd.DataFrame([{"id_venda": id_sales, "id_prod_caract": id_prod_caract, "id_income": id_income, "nome_adm": nome_adm, "nome_produto": nome_produto, "id_funcionario": id_funcionario, "nome_funcionario": nome_funcionario, 
                                                'grupo': grupo, 'cota': cota, 'projeto': projeto_venda, 'nome_cliente': nome_cliente, "data_venda": pd.to_datetime(data), "data_venda_abv": data_venda_abv, 'data_primeira_parcela': data_primeira_parcela_upd, 
                                                'data_ultima_parcela': data_ultima_parcela_upd, "valor_venda": valor_venda, "taxa_comissao": taxa_comissao, "valor_comissao": valor_comissao, "taxa_receita": taxa_receita, "valor_receita": valor_receita}])
                    df_sales = pd.concat([df_temp_sales, df_sales], ignore_index=True)

                    query = f"INSERT INTO sales (id_venda, id_prod_caract, id_income, nome_adm, nome_produto, id_funcionario, nome_funcionario, grupo, cota, projeto, nome_cliente, data_venda, data_venda_abv, data_primeira_parcela, data_ultima_parcela, data_ultima_parcela_receita, \
                    valor_venda, taxa_comissao, valor_comissao, taxa_receita, valor_receita, company_id) VALUES ('{id_sales}', '{id_prod_caract}', {id_income}, '{nome_adm}', '{nome_produto}', {id_funcionario}, '{nome_funcionario}', {grupo}, {cota}, '{projeto_venda}', '{nome_cliente}', \
                        '{data}', '{data_venda_abv}', '{data_primeira_parcela_upd}', '{data_ultima_parcela_upd}', '{data_ultima_parcela_income_upd}', {valor_venda}, {taxa_comissao}, {valor_comissao}, {taxa_receita}, {valor_receita}, '{company_id}');"
                    cur.execute(query)
                    conn.commit()

                    st.success("Venda registrada com sucesso!")

        if sale_menu == 'Atualizar':
            st.subheader("Atualizar Venda")
            vendas_select_upd = list(df_sales['id_venda'].map(str) + ' - ' + df_sales['nome_adm'].map(str) + ' - ' + df_sales['nome_produto'].map(str) + ' - ' + df_sales['nome_funcionario'].map(str))
            select_sales_upd = st.selectbox('Escolha a venda', vendas_select_upd)

            id_sales_upd = select_sales_upd.split(' - ')[0]
            # print(df_sales[df_sales['id_venda'] == id_sales_upd])
            administradora_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['nome_adm'].values[0]
            id_administradora = administradoras.index(administradora_upd)
            produto_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['nome_produto'].values[0]
            func_upd = str(df_sales[df_sales['id_venda'] == id_sales_upd]['id_funcionario'].values[0]) + ' - ' + df_sales[df_sales['id_venda'] == id_sales_upd]['nome_funcionario'].values[0]
            proj_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['projeto'].values[0]
            cliente_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['nome_cliente'].values[0]
            grupo_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['grupo'].values[0]
            cota_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['cota'].values[0]
            valor_venda_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['valor_venda'].values[0]
            data_venda_upd = df_sales[df_sales['id_venda'] == id_sales_upd]['data_venda'].values[0]

            with st.container(border=True):
                nome_adm = st.selectbox('Administradora', administradoras, index=id_administradora)
                produtos = tuple(set(df_prod_caract[df_prod_caract['nome_adm'] == nome_adm]['nome_produto']))
                if nome_adm == administradora_upd:
                    nome_produto = st.selectbox('Produto', produtos, index=produtos.index(produto_upd))
                else:
                    nome_produto = st.selectbox('Produto', produtos)
                id_func_s = st.selectbox('Vendedor', funcionarios, index=funcionarios.index(func_upd))
                projeto_venda = st.selectbox('Projeto', projetos, index=projetos.index(proj_upd))
                nome_cliente = st.text_input('Nome do Cliente', value=cliente_upd)
                grupo = st.number_input('Grupo', step=1, value=int(grupo_upd))
                cota = st.number_input('Cota', step=1, value=int(cota_upd))
                valor_venda = st.number_input('Valor do Consórcio', value=valor_venda_upd)
                data = st.date_input("Data da Venda", format= "DD/MM/YYYY", value=pd.to_datetime(data_venda_upd))

                save_upd_sales = st.button('Salvar', key='save_upd_sales')
                if save_upd_sales:
                    func = id_func_s.split(' - ')
                    id_funcionario = func[0]
                    nome_funcionario = func[1]
                    data = pd.to_datetime(data, format='%Y-%m-%d')

                    data_venda_abv = f'{data.year}/0{data.month}' if len(str(data.month)) == 1 else f'{data.year}/{data.month}'

                    id_prod_caract = df_prod_caract.loc[(df_prod_caract['nome_produto'] == nome_produto) & (df_prod_caract['projeto'] == projeto_venda), 'id_prod_caract'].values[0]
                    qtd_parcelas = df_prod_caract.loc[(df_prod_caract['id_prod_caract'] == id_prod_caract), 'qtd_parcelas'].values[0]

                    taxa_comissao = float(df_prod_caract.loc[df_prod_caract['id_prod_caract'] == id_prod_caract, 'taxa_comissao'].values[0])
                    valor_comissao = round((taxa_comissao/100) * valor_venda, 2)

                    taxa_receita = float(df_income.loc[df_income['nome_produto'] == nome_produto, 'taxa_comissao'].values[0])
                    valor_receita = round((taxa_receita/100) * valor_venda, 2)

                    data_primeira_parcela = data + relativedelta(months=1)
                    data_primeira_parcela_upd = dt(data_primeira_parcela.year, data_primeira_parcela.month, 10).date()
                    data_ultima_parcela = data + relativedelta(months=(qtd_parcelas))
                    data_ultima_parcela_upd = dt(data_ultima_parcela.year, data_ultima_parcela.month, 10).date()

                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'id_prod_caract'] = id_prod_caract
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'nome_adm'] = nome_adm
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'nome_produto'] = nome_produto
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'id_funcionario'] = id_funcionario
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'nome_funcionario'] = nome_funcionario
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'projeto'] = projeto_venda
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'nome_cliente'] = nome_cliente
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'grupo'] = grupo
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'cota'] = cota
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'valor_venda'] = valor_venda
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'data_venda'] = data
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'data_venda_abv'] = data_venda_abv
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'data_primeira_parcela'] = data_primeira_parcela_upd
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'data_ultima_parcela'] = data_ultima_parcela_upd
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'taxa_comissao'] = taxa_comissao
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'valor_comissao'] = valor_comissao
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'taxa_receita'] = taxa_receita
                    df_sales.loc[df_sales['id_venda'] == id_sales_upd, 'valor_receita'] = valor_receita

                    query = f"UPDATE sales SET id_prod_caract = '{id_prod_caract}', nome_adm = '{nome_adm}', nome_produto = '{nome_produto}', id_funcionario = '{id_funcionario}', nome_funcionario = '{nome_funcionario}', \
                        projeto = '{projeto_venda}', nome_cliente = '{nome_cliente}', grupo = {grupo}, cota = {cota}, valor_venda = {valor_venda}, data_venda = '{data}', data_venda_abv = '{data_venda_abv}', \
                         data_primeira_parcela = '{data_primeira_parcela_upd}', data_ultima_parcela = '{data_ultima_parcela_upd}', taxa_comissao = {taxa_comissao}, valor_comissao = {valor_comissao}, \
                             taxa_receita = {taxa_receita}, valor_receita = {valor_receita} WHERE id_venda = '{id_sales_upd}';"
                    cur.execute(query)
                    conn.commit()

                    st.success("Venda atualizada com sucesso!")

        if sale_menu == 'Deletar':
            st.subheader("Deletar Venda")
            with st.form(key="del_sales", clear_on_submit=True):
                
                vendas = list(df_sales['id_venda'].map(str) + ' - ' + df_sales['nome_produto'].map(str) + ' - ' + df_sales['nome_funcionario'])

                id_sales_valid = None
                if 'sb_sales' in st.session_state:
                    id_sales_valid = st.session_state['sb_sales']

                id_sales_s = st.selectbox('Venda', vendas, key='sb_sales')
                id_sales_s = id_sales_s if id_sales_s == id_sales_valid else id_sales_valid

                del_sales = st.form_submit_button(label="Deletar")
                
                if del_sales:

                    sales = id_sales_s.split(' - ')
                    id_venda = sales[0]
                    nome_produto = sales[1]

                    df_sales = df_sales[df_sales['id_venda'] != id_venda]
                    
                    query = f"DELETE FROM sales WHERE id_venda = '{id_venda}';"
                    cur.execute(query)
                    conn.commit()

                    st.success("Venda deletada com sucesso!")

        st.subheader("Tabela Vendas")

        df_sales_view = convert_column_types(df_sales.sort_values(by='data_venda',ascending=False), ['valor_venda','taxa_comissao','valor_comissao','taxa_receita','valor_receita'], ['data_venda','data_primeira_parcela','data_ultima_parcela'])
        dict_rename_sales = {'id_venda':'ID Venda','nome_adm':'Adm','nome_produto':'Produto','nome_funcionario':'Vendedor','grupo':'Grupo','cota':'Cota','projeto':'Projeto','nome_cliente':'Cliente','data_venda':'Data Venda',
                        'valor_venda':'Valor Venda (R$)','taxa_comissao':'Taxa Comissão (%)','valor_comissao':'Valor Comissão','taxa_receita':'Taxa Receita','valor_receita':'Valor Receita'}
        df_sales_view_upd = df_sales_view[dict_rename_sales.keys()]
        df_sales_view_upd = df_sales_view_upd.rename(columns=dict_rename_sales)

        st.write(df_sales_view_upd)

        save_table(df_sales_view_upd, "Baixar Tabela")

        # save_sales_bt = st.button('Baixar Tabela')
        # if save_sales_bt:
        #     save_table('tabela_vendas', df_sales_view_upd)
        #     st.success("Tabela salva com sucesso!")


    if selected == 'Projeto':
        project_menu = option_menu(None, ['Registrar', 'Deletar'], orientation='horizontal')
        if project_menu == 'Registrar':
            st.subheader("Registrar Projeto")
            with st.form(key="reg_project", clear_on_submit=True):
                
                # id_proj_atual = df_projects['id_projeto'].max()
                # if pd.isna(id_proj_atual) == False:
                #     id_proj = int(id_proj_atual) + 1
                # else:
                #     id_proj = 1
                short_id = shortuuid.ShortUUID()
                id_proj = short_id.random(length=3)

                nome_projeto = st.text_input('Nome do Projeto')
                
                submit_proj = st.form_submit_button(label="Salvar")

                if submit_proj:
                    
                    nome_projeto = nome_projeto.title()

                    df_temp_proj = pd.DataFrame([{"id_projeto": id_proj, "nome_projeto": nome_projeto}])
                    df_projects = pd.concat([df_temp_proj, df_projects], ignore_index=True)
                    
                    query = f"INSERT INTO projects (id_projeto, nome_projeto, company_id) VALUES ('{id_proj}', '{nome_projeto}', '{company_id}');"
                    cur.execute(query)
                    conn.commit()

                    st.success("Projeto registrado com sucesso!")

        if project_menu == 'Deletar':
            st.subheader("Deletar Projeto")
            with st.form(key="del_project", clear_on_submit=True):
                
                projects = list(df_projects['id_projeto'].map(str) + ' - ' + df_projects['nome_projeto'].map(str))

                id_projects_valid = None
                if 'sb_projects' in st.session_state:
                    id_projects_valid = st.session_state['sb_projects']

                id_projects_s = st.selectbox('Projeto', projects, key='sb_projects')
                id_projects_s = id_projects_s if id_projects_s == id_projects_valid else id_projects_valid

                del_projects = st.form_submit_button(label="Deletar")
                
                if del_projects:

                    projects = id_projects_s.split(' - ')
                    id_project = projects[0]
                    name_project = projects[1]

                    df_projects = df_projects[df_projects['id_projeto'] != id_project]
                    
                    query = f"DELETE FROM projects WHERE id_projeto = '{id_project}';"
                    cur.execute(query)
                    conn.commit()

                    st.success("Projeto deletado com sucesso!")

        st.subheader("Tabela Projetos")

        dict_rename_projects = {'id_projeto':'ID Projeto','nome_projeto':'Projeto'}
        df_projects_view_upd = df_projects[dict_rename_projects.keys()]
        df_projects_view_upd = df_projects_view_upd.rename(columns=dict_rename_projects)
        
        st.write(df_projects_view_upd)

        save_table(df_projects_view_upd, "Baixar Tabela")
        # save_sales_bt = st.button('Baixar Tabela')
        # if save_sales_bt:
        #     save_table('tabela_projetos', df_projects_view_upd)
        #     st.success("Tabela salva com sucesso!")

    if selected == 'Vendedor':
        employee_menu = option_menu(None, ['Registrar', 'Atualizar', 'Deletar'], orientation='horizontal')
        if employee_menu == 'Registrar':
            st.subheader("Registrar Vendedor")
            with st.form(key="reg_employee", clear_on_submit=True):

                # id_func_atual = df_employees['id_funcionario'].max()
                # if pd.isna(id_func_atual) == False:
                #     id_func = int(id_func_atual) + 1
                # else:
                #     id_func = 1
                short_id = shortuuid.ShortUUID()
                id_func = short_id.random(length=3)
                
                st.text("Dados Gerais")
                nome_func = st.text_input("Nome Vendedor", key='nome_func')
                cpf = st.text_input("CPF", key='cpf')
                data_adesao = st.date_input("Data de Adesão", key='data_adesao', format= "DD/MM/YYYY")
                salario = st.number_input("Salário", key='salario')
                
                st.text('Dados Bancários')
                pix = st.text_input('Pix', key='pix')
                nome_banco = st.text_input("Nome do Banco", key='nome_banco')
                nr_banco = st.text_input("Nº do Banco", key='nr_banco')
                agencia = st.text_input("Agência", key='agencia')
                nr_conta = st.text_input("Conta", key='conta')

                st.text('Dados Empresariais (opcional)')
                titular = st.text_input('Titular', key='titular')
                documento = st.text_input('Documento', key='documento')

                # id_projects_valid = None
                # if 'sb_projects_func' in st.session_state:
                #     id_projects_valid = st.session_state['sb_projects_func']

                # project_employee = st.selectbox('Projeto', projects, key='sb_projects_func')
                # project_employee = project_employee if project_employee == id_projects_valid else id_projects_valid

                submit_emp = st.form_submit_button(label="Salvar")
                    
                if submit_emp:
                    df_temp_func = pd.DataFrame([{"id_funcionario": id_func, "nome_funcionario": nome_func, "cpf": cpf, "data_adesao": data_adesao, "salario": salario, "pix": pix, "emp_validation": True,
                                                  "nome_banco": nome_banco, "nr_banco": nr_banco, "agencia": agencia, "conta": nr_conta, 'titular': titular, 'documento': documento}]) # "projeto": project_employee, 
                    df_employees = pd.concat([df_employees, df_temp_func], ignore_index=True)
                    
                    query = f"INSERT INTO employees (id_funcionario, nome_funcionario, cpf, data_adesao, salario, pix, emp_validation, company_id, nome_banco, nr_banco, agencia, conta, titular, documento) VALUES \
                    ('{id_func}', '{nome_func}', '{cpf}', '{data_adesao}', {salario}, '{pix}', true, '{company_id}', '{nome_banco}', '{nr_banco}', '{agencia}', '{nr_conta}', '{titular}', '{documento}');"
                    cur.execute(query)
                    conn.commit()

                    st.success("Vendedor registrado com sucesso!")

        if employee_menu == 'Atualizar':
            st.subheader("Atualizar Vendedor")

            df_employees_valid = df_employees[df_employees['emp_validation'] == True]
            list_funcionario = list(df_employees_valid['id_funcionario'].astype(str) + ' - ' + df_employees_valid['nome_funcionario'])
            func_upd = st.selectbox('Escolha o funcionário', list_funcionario, key='func_upd')

            func = func_upd.split(' - ')
            id_funcionario = int(func[0])

            with st.form(key="upd_employee", clear_on_submit=True):

                # id_func_valid = None
                # if 'sb_employee_upd' in st.session_state:
                #     id_func_valid = st.session_state['sb_employee_upd']
                
                st.text("Dados Gerais")
                nome_func = st.text_input("Nome Vendedor", key='nome_func', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'nome_funcionario'].values[0])
                cpf = st.text_input("CPF", key='cpf', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'cpf'].values[0])
                data_adesao = st.date_input("Data de Adesão", key='data_adesao', format= "DD/MM/YYYY", value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'data_adesao'].values[0])
                salario = st.number_input("Salário", key='salario', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'salario'].values[0])
                
                st.text('Dados Bancários')
                pix = st.text_input('Pix', key='pix', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'pix'].values[0])
                nome_banco = st.text_input("Nome do Banco", key='nome_banco', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'nome_banco'].values[0])
                nr_banco = st.text_input("Nº do Banco", key='nr_banco', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'nr_banco'].values[0])
                agencia = st.text_input("Agência", key='agencia', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'agencia'].values[0])
                nr_conta = st.text_input("Conta", key='conta', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'conta'].values[0])

                st.text('Dados Empresariais (opcional)')
                titular = st.text_input('Titular', key='titular', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'titular'].values[0])
                documento = st.text_input('Documento', key='documento', value=df_employees.loc[df_employees.id_funcionario == id_funcionario, 'documento'].values[0])

                # id_func_s = id_func_s if id_func_s == id_func_valid else id_func_valid

                upd_emp = st.form_submit_button(label="Atualizar")
                
                if upd_emp:
                    
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'nome_funcionario'] = nome_func
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'cpf'] = cpf
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'data_adesao'] = data_adesao
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'salario'] = salario
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'pix'] = pix
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'nome_banco'] = nome_banco
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'nr_banco'] = nr_banco
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'agencia'] = agencia
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'conta'] = nr_conta
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'titular'] = titular
                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'documento'] = documento

                    query = f"UPDATE employees SET nome_funcionario = '{nome_func}', cpf = '{cpf}', data_adesao = '{data_adesao}', salario = {salario}, pix = '{pix}', nome_banco = '{nome_banco}', nr_banco = '{nr_banco}', \
                        agencia = '{agencia}', conta = '{nr_conta}', titular = '{titular}', documento = '{documento}' WHERE id_funcionario = '{id_funcionario}';"
                    
                    cur.execute(query)
                    conn.commit()
                        
                    st.success("Vendedor atualizado com sucesso!")

        if employee_menu == 'Deletar':
            st.subheader("Deletar Vendedor")
            with st.form(key="del_employee", clear_on_submit=True):
                
                df_employees_valid = df_employees[df_employees['emp_validation'] == True]
                funcionarios = list(df_employees_valid['id_funcionario'].map(str) + ' - ' + df_employees_valid['nome_funcionario'].map(str))

                id_func_valid = None
                if 'sb_employee' in st.session_state:
                    id_func_valid = st.session_state['sb_employee']

                id_func_s = st.selectbox('Vendedor', funcionarios, key='sb_employee')
                id_func_s = id_func_s if id_func_s == id_func_valid else id_func_valid

                del_emp = st.form_submit_button(label="Deletar")
                
                if del_emp:

                    func = id_func_s.split(' - ')
                    id_funcionario = func[0]
                    nome_funcionario = func[1]

                    df_employees.loc[df_employees['id_funcionario'] == id_funcionario, 'emp_validation'] = False
                    
                    query = f"DELETE FROM employees WHERE id_funcionario = '{id_funcionario}';"
                    cur.execute(query)
                    conn.commit()

                    st.success("Vendedor deletado com sucesso!")

        st.subheader("Tabela Vendedores")

        df_employees_view = df_employees[df_employees['emp_validation'] == True].loc[:, df_employees.columns != 'emp_validation']
        dict_rename_employees = {'id_funcionario':'ID Vendedor','nome_funcionario':'Vendedor','cpf':'CPF','data_adesao':'Data Adesão','pix':'PIX','salario':'Salário','nome_banco':'Banco','nr_banco':'Nº Banco',
                                 'agencia':'Agência','conta':'Conta','titular':'Titular','documento':'Documento'}
        df_employees_view_upd = df_employees_view[dict_rename_employees.keys()]
        df_employees_view_upd = df_employees_view_upd.rename(columns=dict_rename_employees)
        df_employees_view_upd = convert_column_types(df_employees_view_upd, ['Salário'], ['Data Adesão'])

        st.write(df_employees_view_upd)

        save_table(df_employees_view_upd, "Baixar Tabela")
        # save_employees_bt = st.button('Baixar Tabela')
        # if save_employees_bt:
        #     save_table('tabela_funcionarios', df_employees_view_upd)
        #     st.success("Tabela salva com sucesso!")

    if selected == 'Produto':
        product_menu = option_menu(None, ['Administradora','Produto','Receita','Comissão'], orientation='horizontal')
        if product_menu == 'Administradora':
            adm_menu = option_menu(None, ['Registrar','Deletar'], orientation='horizontal')

            if adm_menu == 'Registrar':
                st.subheader("Registrar Administradora")
                with st.form(key="reg_adm", clear_on_submit=True):

                    # id_adm_atual = df_adm['id_adm'].max()
                    # if pd.isna(id_adm_atual) == False:
                    #     id_adm = int(id_adm_atual) + 1
                    # else:
                    #     id_adm = 1
                    short_id = shortuuid.ShortUUID()
                    id_adm = short_id.random(length=3)

                    nome_adm = st.text_input("Nome da Administradora")

                    submit_adm = st.form_submit_button(label="Salvar")
                    if submit_adm:
                        df_adm = pd.concat([df_adm, pd.DataFrame([{"id_adm": id_adm, "nome_adm": nome_adm}])], ignore_index=True)
                        
                        query = f"INSERT INTO administrators (id_adm, nome_adm, company_id) VALUES ('{id_adm}', '{nome_adm}', '{company_id}');"
                        cur.execute(query)
                        conn.commit()

                        st.success("Administradora inserida com sucesso!")

            if adm_menu == 'Deletar':
                adminstradoras = list(df_adm['id_adm'].map(str) + ' - ' + df_adm['nome_adm'].map(str))
                st.subheader("Deletar Administradora")
                with st.form(key="del_adm", clear_on_submit=True):
                    id_adm_valid = None
                    if 'sb_adm' in st.session_state:
                        id_adm_valid = st.session_state['sb_adm']

                    id_adm_s = st.selectbox('Administradora', adminstradoras, key='sb_adm')
                    id_adm_s = id_adm_s if id_adm_s == id_adm_valid else id_adm_valid

                    del_adm = st.form_submit_button(label="Deletar")
                    
                    if del_adm:

                        adm = id_adm_s.split(' - ')
                        id_adm = adm[0]
                        nome_adm = adm[1]

                        df_adm = df_adm[df_adm['id_adm'] != id_adm].reset_index(drop=True)
                        
                        query = f"DELETE FROM administrators WHERE id_adm = '{id_adm}';"
                        cur.execute(query)
                        conn.commit()

                        st.success("Administradora deletada com sucesso!")

            st.subheader("Tabela Administradoras")

            dict_rename_adm = {'id_adm':'ID Adm','nome_adm':'Administradora'}
            df_adm_view_upd = df_adm[dict_rename_adm.keys()]
            df_adm_view_upd = df_adm_view_upd.rename(columns=dict_rename_adm)

            st.write(df_adm_view_upd)

            save_table(df_adm_view_upd, "Baixar Tabela")
            # save_adm_bt = st.button('Baixar Tabela')
            # if save_adm_bt:
            #     save_table('tabela_adm', df_adm_view_upd)
            #     st.success("Tabela salva com sucesso!")


        if product_menu == 'Produto':
            prod_menu = option_menu(None, ['Registrar','Deletar'], orientation='horizontal')

            if prod_menu == 'Registrar':
                st.subheader("Registrar Produto")
                with st.form(key="reg_product", clear_on_submit=True):
                    
                    # id_produto_atual = df_products['id_produto'].max()
                    # if pd.isna(id_produto_atual) == False:
                    #     id_produto = int(id_produto_atual) + 1
                    # else:
                    #     id_produto = 1
                    short_id = shortuuid.ShortUUID()
                    id_produto = short_id.random(length=4)

                    list_adm = list(df_adm['nome_adm'])

                    administradora = st.selectbox("Administradora", list_adm)
                    nome_produto = st.text_input("Nome Produto")
                    # venda_produto = st.number_input("Valor de Venda")

                    submit_prod = st.form_submit_button(label="Salvar")
                    if submit_prod:
                        df_products = pd.concat([df_products, pd.DataFrame([{"id_produto": id_produto, "nome_adm": administradora, "nome_produto": nome_produto}])], ignore_index=True)
                        
                        query = f"INSERT INTO products (id_produto, nome_adm, nome_produto, company_id) VALUES ('{id_produto}', '{administradora}', '{nome_produto}', '{company_id}');"
                        cur.execute(query)
                        conn.commit()

                        st.success("Produto inserido com sucesso!")

            if prod_menu == 'Deletar':

                st.subheader("Deletar Produto")

                list_adm = list(df_adm['nome_adm'])
                administradora = st.selectbox("Administradora", list_adm)
                with st.form(key="del_prod", clear_on_submit=True):

                    df_products_temp = df_products[df_products['nome_adm'] == administradora]
                    produtos = list(df_products_temp['id_produto'].map(str) + ' - ' + df_products_temp['nome_produto'].map(str))

                    id_prod_valid = None
                    if 'sb_prod' in st.session_state:
                        id_prod_valid = st.session_state['sb_prod']

                    id_prod_s = st.selectbox('Produto', produtos, key='sb_prod')
                    id_prod_s = id_prod_s if id_prod_s == id_prod_valid else id_prod_valid

                    del_prod = st.form_submit_button(label="Deletar")
                    
                    if del_prod:

                        prod = id_prod_s.split(' - ')
                        id_prod = prod[0]
                        nome_prod = prod[1]

                        df_products = df_products[df_products['id_produto'] != id_prod].reset_index(drop=True)
                        
                        query = f"DELETE FROM products WHERE id_produto = '{id_prod}';"
                        cur.execute(query)
                        conn.commit()

                        st.success("Produto deletado com sucesso!")

            st.subheader("Tabela Produtos")

            dict_rename_products = {'id_produto':'ID Produto','nome_adm':'Administradora','nome_produto':'Produto'}
            df_products_view_upd = df_products[dict_rename_products.keys()]
            df_products_view_upd = df_products_view_upd.rename(columns=dict_rename_products)

            st.write(df_products_view_upd)

            save_table(df_products_view_upd, "Baixar Tabela")
            # save_prod_bt = st.button('Baixar Tabela')
            # if save_prod_bt:
            #     save_table('tabela_prod', df_products_view_upd)
            #     st.success("Tabela salva com sucesso!")

        if product_menu == 'Receita':
            inc_menu = option_menu(None, ['Registrar','Deletar'], orientation='horizontal')

            if inc_menu == 'Registrar':

                st.subheader("Registrar Receita")

                # administradoras = tuple(set(df_prod_caract['nome_adm']))
                administradoras = list_adm = list(df_adm['nome_adm'])
                nome_adm = st.selectbox('Administradora', administradoras)
                qtd_parcelas = st.number_input("Quantidade de Parcelas", step=1, key='receita_qtd_parcelas')

                with st.form(key="reg_product_caract", clear_on_submit=True):

                    # id_income_atual = df_income['id_income'].max()
                    # if pd.isna(id_income_atual) == False:
                    #     id_income = int(id_income_atual) + 1
                    # else:
                    #     id_income = 1
                    short_id = shortuuid.ShortUUID()
                    id_income = short_id.random(length=4)

                    # produtos = list(df_products['id_produto'].map(str) + ' - ' +  df_products['nome_adm'].map(str) + ' - ' + df_products['nome_produto'].map(str))
                    produtos = list(df_products[df_products['nome_adm'] == nome_adm]['nome_produto'])

                    produto = st.selectbox('Produto', produtos, key='sb_product_caract_id')
                    contemplacao = st.number_input("Contemplação (%)")
                    taxa_comissao_produto = st.number_input("Taxa de Comissão Total (%)")

                    list_parcelas = []
                    # qtd_parcelas = 0 if qtd_parcelas == '' else qtd_parcelas
                    for i in range(int(qtd_parcelas)):
                        key = f"number_input_{i}"
                        a = st.number_input(f"Taxa da parcela {i+1} (%)", key=key, step=0.001, format="%0.3f")
                        list_parcelas.append(str(a))

                    submit_prod = st.form_submit_button(label="Salvar")

                    if submit_prod:
                        
                        list_parcelas_upd = ' - '.join(list_parcelas)
                        # prod = produto.split(' - ')
                        # id_prod = prod[0]
                        # administradora = prod[1]
                        # nome_produto = prod[2]
                        # venda_produto = df_products.loc[df_products['id_produto'] == int(id_prod), 'valor_venda'].values[0]
                        
                        df_income = pd.concat([df_income, pd.DataFrame([{"id_income": id_income, "nome_adm": nome_adm, "nome_produto": produto, 'taxa_comissao': taxa_comissao_produto, 'contemplacao': contemplacao, 
                                                                            'qtd_parcelas': qtd_parcelas, 'taxa_parcelas': list_parcelas_upd}])], ignore_index=True)

                        query = f"INSERT INTO income (id_income, nome_adm, nome_produto, taxa_comissao, contemplacao, qtd_parcelas, taxa_parcelas, company_id) VALUES ('{id_income}', '{nome_adm}', '{produto}', \
                            {taxa_comissao_produto}, {contemplacao}, {qtd_parcelas}, '{list_parcelas_upd}', '{company_id}');"
                        cur.execute(query)
                        conn.commit()

                        st.success("Receita registrada com sucesso!")

            if inc_menu == 'Deletar':

                st.subheader("Deletar Receita")

                with st.form(key="del_inc", clear_on_submit=True):

                    receitas = list(df_income['id_income'].map(str) + ' - ' + df_income['nome_adm'].map(str) + ' - ' + df_income['nome_produto'].map(str))

                    id_inc_valid = None
                    if 'sb_inc' in st.session_state:
                        id_inc_valid = st.session_state['sb_inc']

                    id_inc_s = st.selectbox('Receita', receitas, key='sb_inc')
                    id_inc_s = id_inc_s if id_inc_s == id_inc_valid else id_inc_valid

                    del_inc = st.form_submit_button(label="Deletar")
                    
                    if del_inc:

                        inc = id_inc_s.split(' - ')
                        id_inc = inc[0]
                        nome_inc = inc[1]

                        df_income = df_income[df_income['id_income'] != id_inc].reset_index(drop=True)
                        
                        query = f"DELETE FROM income WHERE id_income = '{id_inc}';"
                        cur.execute(query)
                        conn.commit()

                        st.success("Receita deletada com sucesso!")

            st.subheader("Tabela Receitas")

            df_income_view = convert_column_types(df_income, ['taxa_comissao','contemplacao'], [])
            dict_rename_income = {'id_income':'ID Receita','nome_adm':'Administradora','nome_produto':'Produto','taxa_comissao':'Taxa Comissão (%)','contemplacao':'Contemplação (%)',
                                  'qtd_parcelas':'Qtd Parcelas','taxa_parcelas':'Taxa Parcelas'}
            df_income_view_upd = df_income_view[dict_rename_income.keys()]
            df_income_view_upd = df_income_view_upd.rename(columns=dict_rename_income)

            st.write(df_income_view_upd)

            save_table(df_income_view_upd, "Baixar Tabela")
            # save_inc_bt = st.button('Baixar Tabela')
            # if save_inc_bt:
            #     save_table('tabela_inc', df_income_view_upd)
            #     st.success("Tabela salva com sucesso!")

        if product_menu == 'Comissão':

            comissao_menu = option_menu(None, ['Registrar','Deletar'], orientation='horizontal')

            if comissao_menu == 'Registrar':

                st.subheader("Registrar comissão")
                
                # administradoras = tuple(set(df_prod_caract['nome_adm']))
                administradoras = list(df_adm['nome_adm'])
                nome_adm = st.selectbox('Administradora', administradoras)
                qtd_parcelas = st.number_input("Quantidade de Parcelas", step=1, key='comissao_qtd_parcelas')

                with st.form(key="reg_product_caract", clear_on_submit=True):

                    # id_produto_caract_atual = df_prod_caract['id_prod_caract'].max()
                    # if pd.isna(id_produto_caract_atual) == False:
                    #     id_prod_caract = int(id_produto_caract_atual) + 1
                    # else:
                    #     id_prod_caract = 1
                    short_id = shortuuid.ShortUUID()
                    id_prod_caract = short_id.random(length=4)

                    # produtos = list(df_products['id_produto'].map(str) + ' - ' +  df_products['nome_adm'].map(str) + ' - ' + df_products['nome_produto'].map(str))
                    produtos = list(df_products[df_products['nome_adm'] == nome_adm]['nome_produto'])

                    produto = st.selectbox('Produto', produtos, key='sb_product_caract_id')
                    projeto_produto = st.selectbox('Projeto', projects, key='sb_project_prod_caract')
                    taxa_comissao_produto = st.number_input("Taxa de Comissão Total (%)")

                    list_parcelas = []
                    # qtd_parcelas = 0 if qtd_parcelas == '' else qtd_parcelas
                    for i in range(int(qtd_parcelas)):
                        key = f"number_input_{i}"
                        a = st.number_input(f"Taxa da parcela {i+1} (%)", key=key, step=0.001, format="%0.3f")
                        list_parcelas.append(str(a))

                    submit_prod = st.form_submit_button(label="Salvar")

                    if submit_prod:
                        
                        list_parcelas_upd = ' - '.join(list_parcelas)
                        # prod = produto.split(' - ')
                        # id_prod = prod[0]
                        # administradora = prod[1]
                        # nome_produto = prod[2]
                        # venda_produto = df_products.loc[df_products['id_produto'] == int(id_prod), 'valor_venda'].values[0]
                        
                        df_prod_caract = pd.concat([df_prod_caract, pd.DataFrame([{"id_prod_caract": id_prod_caract, "nome_adm": nome_adm, "nome_produto": produto, 'projeto': projeto_produto, 'taxa_comissao': taxa_comissao_produto, 
                                                                            'qtd_parcelas': qtd_parcelas, 'taxa_parcelas': list_parcelas_upd}])], ignore_index=True)

                        query = f"INSERT INTO prod_caract (id_prod_caract, nome_adm, nome_produto, projeto, taxa_comissao, qtd_parcelas, taxa_parcelas, company_id) VALUES ('{id_prod_caract}', '{nome_adm}', '{produto}', '{projeto_produto}', \
                            {taxa_comissao_produto}, {qtd_parcelas}, '{list_parcelas_upd}', '{company_id}');"
                        cur.execute(query)
                        conn.commit()

                        st.success("Comissão registrada com sucesso!")

            if comissao_menu == 'Deletar':

                st.subheader("Deletar Comissão")

                with st.form(key="del_comis", clear_on_submit=True):

                    list_comissoes = list(df_prod_caract['id_prod_caract'].map(str) + ' - ' + df_prod_caract['nome_adm'].map(str) + ' - ' + df_prod_caract['nome_produto'].map(str) + ' - ' + df_prod_caract['projeto'].map(str))

                    id_comis_valid = None
                    if 'sb_comis' in st.session_state:
                        id_comis_valid = st.session_state['sb_comis']

                    id_comis_s = st.selectbox('Comissão', list_comissoes, key='sb_comis')
                    id_comis_s = id_comis_s if id_comis_s == id_comis_valid else id_comis_valid

                    del_comis = st.form_submit_button(label="Deletar")
                    
                    if del_comis:

                        comis = id_comis_s.split(' - ')
                        id_comis = comis[0]
                        nome_comis = comis[1]

                        df_prod_caract = df_prod_caract[df_prod_caract['id_prod_caract'] != id_comis].reset_index(drop=True)
                        
                        query = f"DELETE FROM prod_caract WHERE id_prod_caract = '{id_comis}';"
                        cur.execute(query)
                        conn.commit()

                        st.success("Comissão deletada com sucesso!")

            st.subheader("Tabela Comissões")

            df_prod_caract_view = convert_column_types(df_prod_caract, ['taxa_comissao'], [])
            dict_rename_prod_caract = {'id_prod_caract':'ID Comissão','nome_adm':'Administradora','nome_produto':'Produto','projeto':'Projeto','taxa_comissao':'Taxa Comissão (%)',
                                  'qtd_parcelas':'Qtd Parcelas','taxa_parcelas':'Taxa Parcelas'}
            df_prod_caract_view_upd = df_prod_caract_view[dict_rename_prod_caract.keys()]
            df_prod_caract_view_upd = df_prod_caract_view_upd.rename(columns=dict_rename_prod_caract)

            st.write(df_prod_caract_view_upd)

            save_table(df_prod_caract_view_upd, "Baixar Tabela")
            # save_comis_bt = st.button('Baixar Tabela')
            # if save_comis_bt:
            #     save_table('tabela_comis', df_prod_caract)
            #     st.success("Tabela salva com sucesso!")
        
        # if product_menu == 'Atualizar':
        #     st.subheader("Atualizar Produto")
        #     # with st.form(key="upd_product", clear_on_submit=True):

        #     produtos = list(df_prod_caract['id_prod_caract'].map(str) + ' - ' + df_prod_caract['nome_produto'].map(str) + ' - ' + df_prod_caract['projeto'].map(str))

        #     id_prod_valid = None
        #     if 'sb_product_upd' in st.session_state:
        #         id_prod_valid = st.session_state['sb_product_upd']

        #     id_prod_s = st.selectbox('Produto', produtos, key='sb_product_upd')
        #     prod_upd = st.selectbox('Campo a ser atualizado', ['Valor de Venda','Projeto','Taxa de Comissão','Parcelas'], key='prod_upd')

        #     if prod_upd == 'Valor de Venda':
        #         valor_venda_novo = st.number_input("Valor de Venda", key='valor_venda_novo_prod')
        #     elif prod_upd == 'Projeto':
        #         projeto_novo = st.selectbox('Projeto', projects, key='projeto_novo_prod')
        #     elif prod_upd == 'Taxa de Comissão':
        #         taxa_comissao_novo = st.number_input("Taxa de Comissão (%)")
        #     else:
        #         qtd_parcelas = st.text_input("Quantidade de Parcelas")
        #         list_parcelas = []
        #         qtd_parcelas = 0 if qtd_parcelas == '' else qtd_parcelas
        #         for i in range(int(qtd_parcelas)):
        #             key = f"number_input_{i}"
        #             a = st.number_input(f"Taxa da parcela {i+1}", key=key)
        #             list_parcelas.append(a)

        #     id_prod_s = id_prod_s if id_prod_s == id_prod_valid else id_prod_valid

        #     upd_prod = st.button(label="Atualizar")
            
        #     if upd_prod:

        #         prod = id_prod_s.split(' - ')
        #         id_produto = int(prod[0])
        #         nome_produto = prod[1]
        #         list_parcelas_upd_novo = ' - '.join(list_parcelas)

        #         if func_upd == 'Valor de Venda':
        #             df_products.loc[df_products['id_produto'] == id_produto, 'valor_venda'] = valor_venda_novo
        #             query = f"UPDATE products SET valor_venda = {valor_venda_novo} WHERE id_produto = {id_produto};"
                    
        #         elif func_upd == 'Projeto':
        #             df_products.loc[df_products['id_produto'] == id_produto, 'projeto'] = projeto_novo
        #             query = f"UPDATE products SET projeto = {projeto_novo} WHERE id_produto = {id_produto};"
                    
        #         elif func_upd == 'Taxa de Comissão':
        #             df_products.loc[df_products['id_produto'] == id_produto, 'taxa_comissao'] = taxa_comissao_novo
        #             query = f"UPDATE products SET taxa_comissao = {taxa_comissao_novo} WHERE id_produto = {id_produto};"
                    
        #         else:
        #             df_products.loc[df_products['id_produto'] == id_produto, 'qtd_parcelas'] = qtd_parcelas
        #             df_products.loc[df_products['id_produto'] == id_produto, 'taxa_parcelas'] = list_parcelas_upd_novo
        #             query = f"UPDATE products SET qtd_parcelas = '{qtd_parcelas}', taxa_parcelas = '{list_parcelas_upd_novo}' WHERE id_produto = {id_produto};"

        #         cur.execute(query)
        #         conn.commit()

        #         st.success("Produto atualizado com sucesso!")

        if product_menu == 'Deletar':
            st.subheader("Deletar Produto")
            with st.form(key="del_product", clear_on_submit=True):
                
                produtos = list(df_products['id_produto'].map(str) + ' - ' +  df_products['nome_adm'].map(str) + ' - ' + df_products['nome_produto'].map(str))

                id_prod_valid = None
                if 'sb_product' in st.session_state:
                    id_prod_valid = st.session_state['sb_product']

                id_prod_s = st.selectbox('Produto', produtos, key='sb_product')
                id_prod_s = id_prod_s if id_prod_s == id_prod_valid else id_prod_valid

                del_prod = st.form_submit_button(label="Deletar")
                
                if del_prod:

                    prod = id_prod_s.split(' - ')
                    id_produto = prod[0]
                    nome_produto = prod[1]

                    df_products = df_products[df_products['id_produto'] != id_produto]
                    
                    query = f"DELETE FROM products WHERE id_produto = '{id_produto}';"
                    cur.execute(query)
                    conn.commit()

                    st.success("Produto deletado com sucesso!")
        
        # if product_menu == 'Registrar Adm':
        #     st.subheader("Tabela Administradoras")
        #     st.write(df_adm)

        #     save_adm_bt = st.button('Baixar Tabela')
        #     if save_adm_bt:
        #         save_table('tabela_adm', df_adm)
        #         st.success("Tabela salva com sucesso!")
            
        # elif product_menu == 'Registrar Produto':
        #     st.subheader("Tabela Produtos")
        #     st.write(df_products)

        #     save_products_bt = st.button('Baixar Tabela')
        #     if save_products_bt:
        #         save_table('tabela_produtos', df_products)
        #         st.success("Tabela salva com sucesso!")

        # else:
        #     st.subheader("Tabela Comissões")
        #     st.write(df_prod_caract)

        #     save_products_caract_bt = st.button('Baixar Tabela')
        #     if save_products_caract_bt:
        #         save_table('tabela_caracteristicas_produtos', df_prod_caract)
        #         st.success("Tabela salva com sucesso!")

    if selected == 'Salário':
        expense_menu = option_menu(None, ['Registrar', 'Deletar'], orientation='horizontal')
        if expense_menu == 'Registrar':
            st.subheader("Registrar Salário")

            # tipo_despesa = st.selectbox('Tipo de Despesa', ['Salário','Fixo','Variável'])

            id_desp_atual = df_expenses['id_despesa'].max()
            if pd.isna(id_desp_atual) == False:
                id_desp = int(id_desp_atual) + 1
            else:
                id_desp = 1
            
            # if tipo_despesa == 'Salário':
            # list_date_col = []
            # for i in range(-14, 7):
            #     data = dt.now() + relativedelta(months=i)
            #     data_str = f'{data.year}/0{data.month}' if len(str(data.month)) == 1 else f'{data.year}/{data.month}'
            #     list_date_col.append(data_str)
            list_date_col = list(set(df_sales['data_venda_abv']))
            list_date_col.sort()
            mes_atual = f'{dt.now().year}/0{dt.now().month}' if len(str(dt.now().month)) == 1 else f'{dt.now().year}/{dt.now().month}'
            idx_date_col = list_date_col.index(mes_atual) if mes_atual in list_date_col else 0

            data_referencia = st.selectbox('Mês de referência', list_date_col, index=idx_date_col)
            if len(data_referencia) > 0:
                year_selected = data_referencia.split('/')[0]
                month_selected = data_referencia.split('/')[1]
                cur_month_date = dt(int(year_selected), int(month_selected), 10).date()
            else:
                cur_month_date = dt(dt.today().year, dt.today().month, 10).date()

            with st.form(key="despesas_salario", clear_on_submit=True):
                
                df_comissao_geral, df_comissao_filt, dict_columns, df_holerite = comissoes(df_sales, df_prod_caract, cur_month_date, 'id_prod_caract')

                valor_comissao_total = df_comissao_filt[dict_columns[0]].sum()
                valor_salario_total = df_employees[df_employees['emp_validation'] == True]['salario'].sum()

                valor_salario_total = float(valor_salario_total)
                valor_comissao_total = float(valor_comissao_total)

                valor_salario_input = st.number_input('Valor do Salário', value=valor_salario_total)
                valor_comissao_input = st.number_input('Valor da Comissão', value=valor_comissao_total)
                valor_despesa = valor_salario_input + valor_comissao_input
                
                # data_despesa = st.date_input('Data da Despesa', format= "DD/MM/YYYY")
                submit_desp = st.form_submit_button(label="Salvar")

                if submit_desp:
                    data_despesa = cur_month_date
                    data_despesa_abv = f'{data_despesa.year}/0{data_despesa.month}' if len(str(data_despesa.month)) == 1 else f'{data_despesa.year}/{data_despesa.month}'
                    df_temp_desp = pd.DataFrame([{'id_despesa': id_desp, 'tipo_despesa': tipo_despesa, 'nome_despesa': tipo_despesa, 'qtd': None, 'descricao': None, 'valor_salario': valor_salario_input, 'valor_comissao': valor_comissao_input, 'valor_despesa': valor_despesa, 'data_despesa': data_despesa, 
                                                'data_despesa_abv': data_despesa_abv}])
                    df_expenses = pd.concat([df_expenses, df_temp_desp], ignore_index=True)
                    
                    query = f"INSERT INTO expenses (id_despesa, tipo_despesa, nome_despesa, valor_salario, valor_comissao, valor_despesa, data_despesa, data_despesa_abv, company_id) VALUES ({id_desp}, '{tipo_despesa}', '{tipo_despesa}', {valor_salario_input}, \
                        {valor_comissao_input}, {valor_despesa}, '{data_despesa}', '{data_despesa_abv}', '{company_id}');"
                    cur.execute(query)
                    conn.commit()
                    st.success("Salário registrado com sucesso!")
                        
            # if tipo_despesa == 'Fixo':
            #     with st.form(key="despesas_fixo", clear_on_submit=True):

            #         nome_despesa = st.text_input('Nome')
            #         descricao = st.text_input('Descrição')
            #         qtd = st.number_input('Quantidade', step=1)
            #         valor_despesa = st.number_input('Valor')
            #         data_despesa = st.date_input('Data da Despesa', format= "DD/MM/YYYY")

            #         submit_desp = st.form_submit_button(label="Salvar")

            #         if submit_desp:
            #             data_despesa_abv = f'{data_despesa.year}/0{data_despesa.month}' if len(str(data_despesa.month)) == 1 else f'{data_despesa.year}/{data_despesa.month}'
            #             df_temp_desp = pd.DataFrame([{'id_despesa': id_desp, 'tipo_despesa': tipo_despesa, 'nome_despesa': nome_despesa, 'qtd': qtd, 'descricao': descricao, 'valor_salario': valor_salario_input, 'valor_comissao': valor_comissao_input, 'valor_despesa': valor_despesa, 'data_despesa': data_despesa, 
            #                                         'data_despesa_abv': data_despesa_abv}])
                        
            #             query = f"INSERT INTO expenses (id_despesa, tipo_despesa, nome_despesa, valor_despesa, data_despesa, data_despesa_abv, company_id) VALUES ({id_desp}, '{tipo_despesa}', '{nome_despesa}', {valor_despesa}, \
            #                 '{data_despesa}', '{data_despesa_abv}', '{company_id}');"
            #             cur.execute(query)
            #             conn.commit()
            #             st.success("Despesa registrada com sucesso!")
            
            # if tipo_despesa == 'Variável':
            #     with st.form(key="despesas_variavel", clear_on_submit=True):

            #         nome_despesa = st.text_input('Nome')
            #         descricao = st.text_input('Descrição')
            #         qtd = st.number_input('Quantidade', step=1)
            #         valor_despesa = st.number_input('Valor')
            #         data_despesa = st.date_input('Data da Despesa', format= "DD/MM/YYYY")

            #         submit_desp = st.form_submit_button(label="Salvar")

            #         if submit_desp:
            #             data_despesa_abv = f'{data_despesa.year}/0{data_despesa.month}' if len(str(data_despesa.month)) == 1 else f'{data_despesa.year}/{data_despesa.month}'
            #             df_temp_desp = pd.DataFrame([{'id_despesa': id_desp, 'tipo_despesa': tipo_despesa, 'nome_despesa': nome_despesa, 'qtd': qtd, 'descricao': descricao, 'valor_salario': valor_salario_input, 'valor_comissao': valor_comissao_input,'valor_despesa': valor_despesa, 'data_despesa': data_despesa, 
            #                                         'data_despesa_abv': data_despesa_abv}])
                        
            #             query = f"INSERT INTO expenses (id_despesa, tipo_despesa, nome_despesa, valor_despesa, data_despesa, data_despesa_abv, company_id) VALUES ({id_desp}, '{tipo_despesa}', '{nome_despesa}', {valor_despesa}, \
            #                 '{data_despesa}', '{data_despesa_abv}', '{company_id}');"
            #             cur.execute(query)
            #             conn.commit()
            #             st.success("Despesa registrada com sucesso!")

        if expense_menu == 'Deletar':
            st.subheader("Deletar Despesa")
            with st.form(key="del_desp", clear_on_submit=True):
                
                despesas = list(df_expenses['id_despesa'].map(str) + ' - ' + df_expenses['tipo_despesa'].map(str))

                id_desp_valid = None
                if 'sb_desp' in st.session_state:
                    id_desp_valid = st.session_state['sb_desp']

                id_desp_s = st.selectbox('Despesa', despesas, key='sb_desp')
                id_desp_s = id_desp_s if id_desp_s == id_desp_valid else id_desp_valid

                del_desp = st.form_submit_button(label="Deletar")
                
                if del_desp:

                    desp = id_desp_s.split(' - ')
                    id_desp = int(desp[0])
                    tipo_despesa = desp[1]

                    df_expenses = df_expenses[df_expenses['id_despesa'] != id_desp]
                    
                    query = f"DELETE FROM expenses WHERE id_despesa = {id_desp};"
                    cur.execute(query)
                    conn.commit()

                    st.success("Despesa deletada com sucesso!")

        st.subheader("Tabela Despesas")
        st.write(df_expenses.sort_values('data_despesa', ascending=False))

        save_despesa_bt = st.button('Baixar Tabela')
        if save_despesa_bt:
            save_table('tabela_despesa', df_expenses)
            st.success("Tabela salva com sucesso!")
        
    return df_employees, df_products, df_prod_caract, df_sales, df_projects, df_expenses, df_adm, df_income
