import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configuração da página para Tablet / Mobile
st.set_page_config(
    page_title="Pulse Store - Gestão",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS Compacto (No-Scroll para Tablet)
st.markdown("""
<style>
    .block-container { padding-top: 0.8rem; padding-bottom: 0.8rem; padding-left: 0.8rem; padding-right: 0.8rem; }
    div[data-testid="stMetric"] { background-color: #1E1E24; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 2.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; border-radius: 6px; background-color: #262626; color: white; }
    .stTabs [aria-selected="true"] { background-color: #FF4B4B !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("🛍️ Pulse Store — Sistema de Gestão")

# Conexão com Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️️ Conexão com a planilha pendente nos Secrets do Streamlit Cloud.")
    st.stop()

# Função para carregar dados de uma aba
def carregar_dados(aba):
    try:
        df = conn.read(worksheet=aba, ttl=0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

# Função para salvar dados em uma aba
def salvar_dados(df, aba):
    conn.update(worksheet=aba, data=df)
    st.cache_data.clear()

# Carregar Dados das 3 abas
df_estoque = carregar_dados("estoque")
df_caixa = carregar_dados("caixa")
df_crediario = carregar_dados("crediario")

# Navegação por Abas Principais
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Nova Venda", "📦 Estoque", "💰 Caixa", "📋 Crediário"])

# --- TAB 1: NOVA VENDA ---
with tab1:
    st.subheader("Registrar Venda")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not df_estoque.empty and "Produto" in df_estoque.columns:
            produtos_disponiveis = df_estoque[df_estoque["Qtd"] > 0]["Produto"].tolist() if "Qtd" in df_estoque.columns else df_estoque["Produto"].tolist()
            prod_sel = st.selectbox("Selecione o Produto", [""] + produtos_disponiveis)
        else:
            prod_sel = st.text_input("Nome do Produto (Estoque Vazio)")

        qtd_venda = st.number_input("Quantidade", min_value=1, value=1, step=1)
        preco_venda = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0, step=5.0)

    with col2:
        pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Crediário"])
        cliente = st.text_input("Nome do Cliente (Obrigatório para Crediário)")
        
        total_venda = qtd_venda * preco_venda
        st.metric("Total da Venda", f"R$ {total_venda:,.2f}")

        if st.button("✅ FINALIZAR VENDA", type="primary"):
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Atualizar Caixa
            novo_registro_caixa = pd.DataFrame([{
                "Data": data_hoje,
                "Tipo": "Entrada",
                "Descrição": f"Venda: {prod_sel if prod_sel else 'Item'}",
                "Valor": total_venda,
                "Forma": pagamento,
                "Cliente": cliente
            }])
            df_caixa_atualizado = pd.concat([df_caixa, novo_registro_caixa], ignore_index=True)
            salvar_dados(df_caixa_atualizado, "caixa")

            # Se for Crediário, salvar no Crediário
            if pagamento == "Crediário":
                novo_crediario = pd.DataFrame([{
                    "Data": data_hoje,
                    "Cliente": cliente if cliente else "Não informado",
                    "Produto": prod_sel,
                    "Valor": total_venda,
                    "Status": "Pendente"
                }])
                df_crediario_atualizado = pd.concat([df_crediario, novo_crediario], ignore_index=True)
                salvar_dados(df_crediario_atualizado, "crediario")

            st.success("Venda registrada com sucesso!")
            st.rerun()

# --- TAB 2: ESTOQUE ---
with tab2:
    st.subheader("Gerenciamento de Estoque")
    if not df_estoque.empty:
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum produto cadastrado no estoque ainda.")

    with st.expander("➕ Adicionar Novo Produto"):
        novo_prod = st.text_input("Nome do Produto")
        novo_cat = st.selectbox("Categoria", ["Perfumes", "Tênis", "Roupas Dry Fit", "Acessórios", "Outros"])
        nova_qtd = st.number_input("Quantidade Inicial", min_value=1, value=1)
        novo_preco = st.number_input("Preço de Venda (R$)", min_value=0.0, value=0.0)

        if st.button("Guardar no Estoque"):
            novo_item = pd.DataFrame([{
                "Produto": novo_prod,
                "Categoria": novo_cat,
                "Qtd": nova_qtd,
                "Preço": novo_preco
            }])
            df_estoque_atualizado = pd.concat([df_estoque, novo_item], ignore_index=True)
            salvar_dados(df_estoque_atualizado, "estoque")
            st.success("Produto adicionado com sucesso!")
            st.rerun()

# --- TAB 3: CAIXA ---
with tab3:
    st.subheader("Fluxo de Caixa")
    if not df_caixa.empty and "Valor" in df_caixa.columns:
        total_caixa = df_caixa["Valor"].sum()
        st.metric("Total em Caixa", f"R$ {total_caixa:,.2f}")
        st.dataframe(df_caixa, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma movimentação no caixa registrada.")

# --- TAB 4: CREDIÁRIO ---
with tab4:
    st.subheader("Controle de Crediário (Fiado)")
    if not df_crediario.empty:
        st.dataframe(df_crediario, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro no crediário.")
