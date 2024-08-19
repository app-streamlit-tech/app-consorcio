import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from core.db import Db_pg
from app_pages.RH import rh
from app_pages.Receita import receita
from app_pages.FluxoCaixa import fluxo_caixa
from app_pages.Registrar import registrar
from app_pages.Resultados import resultados
from app_pages.functions import load_data

st.set_page_config(page_title='App', layout='wide')

# User Auth

cur, conn = Db_pg.connect()

query = fr"select * from app_auth;"
cur.execute(query)
list_cred = cur.fetchall()
credentials = {"usernames":{}}
dict_permissions = {}
dict_company_id = {}
for cred in list_cred:
    credentials["usernames"][cred[0]] = {'email':cred[0],'name':cred[1],'password':cred[2]}
    # dict_permissions[cred[0]] = cred[3]
    dict_company_id[cred[0]] = cred[3]

Db_pg.disconnect(cur, conn)

col1, col2, col3 = st.columns(3)

with col2:
    authenticator = stauth.Authenticate(credentials, "sales_dashboard", "abcdef", cookie_expiry_days=30)

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status == False:
        st.error("Username/password is incorrect")

    if authentication_status == None:
        st.warning("Please enter your username and password")

if authentication_status:
    name = 'CONTATO'
    company_id = dict_company_id[username] # 'contato_4b42bcf5-6cb5-47d7-8a4e-6c14b30f7dac'

    if "df_sales" not in st.session_state:
        df_sales, df_employees, df_expenses, df_products, df_prod_caract, df_projects, df_prod_sales, df_adm, df_income = load_data(company_id)
        
        st.session_state["df_sales"] = df_sales
        st.session_state["df_employees"] = df_employees
        st.session_state["df_expenses"] = df_expenses
        st.session_state["df_products"] = df_products
        st.session_state["df_prod_caract"] = df_prod_caract
        st.session_state["df_projects"] = df_projects
        st.session_state["df_prod_sales"] = df_prod_sales
        st.session_state["df_adm"] = df_adm
        st.session_state["df_income"] = df_income

    else:
        df_sales = st.session_state["df_sales"]
        df_employees = st.session_state["df_employees"]
        df_expenses = st.session_state["df_expenses"]
        df_products = st.session_state["df_products"]
        df_prod_caract = st.session_state["df_prod_caract"]
        df_projects = st.session_state["df_projects"]
        df_prod_sales = st.session_state["df_prod_sales"]
        df_adm = st.session_state["df_adm"]
        df_income = st.session_state["df_income"]

    with st.sidebar:
        selected = option_menu(name, ['Home','Registrar','Recursos Humanos','Receita','Fluxo de Caixa'], menu_icon="cast", default_index=0)
        authenticator.logout('Logout')

    cur, conn = Db_pg.connect()

    if selected == 'Recursos Humanos':

        # col1, col2, col3 = st.columns([1,2,1])
        # with col2:
        rh(df_sales, df_prod_caract)
        # st.session_state["df_sales"] = df_sales
        # st.session_state["df_prod_sales"] = df_prod_sales

    if selected == 'Receita':
        receita(df_sales, df_income)

    if selected == 'Registrar':

        col1, col2, col3 = st.columns([1,4,1])
        with col2:
            df_employees, df_products, df_prod_caract, df_sales, df_projects, df_expenses, df_adm, df_income = registrar(cur, conn, company_id, df_employees, df_products, df_prod_caract, df_sales, df_projects, df_expenses, df_adm, df_income)
            st.session_state["df_employees"] = df_employees
            st.session_state["df_products"] = df_products
            st.session_state["df_sales"] = df_sales
            st.session_state["df_expenses"] = df_expenses
            st.session_state["df_projects"] = df_projects
            st.session_state["df_prod_caract"] = df_prod_caract
            st.session_state["df_adm"] = df_adm
            st.session_state["df_income"] = df_income

    if selected == 'Home':

        # col1, col2, col3 = st.columns([1,2,1])
        # with col2:
        resultados(df_sales)
        # st.session_state["df_sales"] = df_sales

    if selected == 'Fluxo de Caixa':

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            df_sales, df_expenses = fluxo_caixa(df_sales, df_expenses)
            st.session_state["df_sales"] = df_sales
            st.session_state["df_expenses"] = df_expenses

    Db_pg.disconnect(cur, conn)
    