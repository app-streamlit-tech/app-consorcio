import streamlit as st

st.set_page_config(page_title='App', layout='wide')

qtd_parcelas = st.text_input("Quantidade de Parcelas")

with st.form(key="del_employee", clear_on_submit=True):
    
    key1 = st.number_input("key 1")
    key2 = st.number_input("key 2")

        # with st.columns(len(['a']))[0]:
        
    # qtd_parcelas = st.text_input("Quantidade de Parcelas")
    qtd_parcelas = 0 if qtd_parcelas == '' else qtd_parcelas
    list_parcelas = []
    for i in range(int(qtd_parcelas)):
        key = f"number_input_{i}"
        a = st.number_input(f"Parcela {i+1}", key=key)
        list_parcelas.append(str(a))

    list_parcelas_upd = ' - '.join(list_parcelas)

    submit_prod = st.form_submit_button(label="Salvar")

    if submit_prod:
        st.text(list_parcelas_upd)