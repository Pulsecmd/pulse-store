import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (OTIMIZADA PARA TABLET / MOBILE)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pulse Store — Gestão & Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS Compacto e Moderno (No-Scroll para Tablet)
st.markdown("""
<style>
    .block-container { padding: 0.6rem 1rem; }
    .stMetric { background-color: #1A1D24; padding: 12px; border-radius: 10px; border: 1px solid #2D323E; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 2.8rem; background-color: #0066FF; color: white; }
    .stButton > button:hover { background-color: #0052CC; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 18px; border-radius: 8px; background-color: #1E222D; color: #A0AAB8; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #0066FF !important; color: #FFFFFF !important; }
    .card-alerta { background-color: #2D1A1A; border: 1px solid #FF4D4D; padding: 10px; border-radius: 8px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Pulse Store — Gestão Cloud")

# ---------------------------------------------------------
# CONEXÃO COM GOOGLE SHEETS
# ---------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("⚠️ Conexão pendente nos Secrets do Streamlit Cloud.")
    st.stop()

def carregar_aba(nome_aba=None):
    try:
        if nome_aba:
            df = conn.read(worksheet=nome_aba, ttl=0)
        else:
            df = conn.read(ttl=0)
        return df.dropna(how="all") if df is not None else pd.DataFrame()
    except Exception:
        try:
            df = conn.read(ttl=0)
            return df.dropna(how="all") if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

def salvar_aba(df, nome_aba):
    try:
        conn.update(worksheet=nome_aba, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar na aba {nome_aba}: {e}")

# Carregamento dos Dados
df_bruto = carregar_aba("estoque")
if df_bruto.empty:
    df_bruto = carregar_aba()

# Tratar e padronizar o Estoque (Adaptado para a planilha PULSE)
def tratar_estoque(df):
    if df.empty:
        return pd.DataFrame(columns=["Produto", "Categoria", "Qtd", "Preco_Custo", "Preco_Venda", "Lucro", "Valor_Total"])
    
    # Se os cabeçalhos estiverem na linha 5/6 da planilha
    if "Categoria" not in df.columns:
        for idx, row in df.iterrows():
            if "Categoria" in row.values:
                df.columns = df.iloc[idx]
                df = df.iloc[idx+1:].reset_index(drop=True)
                break

    df = df.dropna(subset=["Categoria"]).copy() if "Categoria" in df.columns else df.copy()

    # Mapeamento dinâmico de colunas
    col_cat = "Categoria" if "Categoria" in df.columns else df.columns[0]
    col_qtd = "Column" if "Column" in df.columns else ("Qtd" if "Qtd" in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0]))
    col_marca = "Marca" if "Marca" in df.columns else ""
    col_nome = "Coluna 6" if "Coluna 6" in df.columns else ("Produto" if "Produto" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[0]))
    col_custo = [c for c in df.columns if "custo" in str(c).lower()]
    col_venda = [c for c in df.columns if "venda" in str(c).lower()]

    col_custo_str = col_custo[0] if col_custo else "Preço de custo"
    col_venda_str = col_venda[0] if col_venda else "Preço de Venda"

    # Criar nome do produto unificado (Marca + Modelo)
    if col_marca and col_marca in df.columns:
        df["Produto"] = df[col_marca].fillna("").astype(str) + " " + df[col_nome].fillna("").astype(str)
    else:
        df["Produto"] = df[col_nome].astype(str)

    # Limpeza numérica
    def limpar_num(val):
        if pd.isna(val): return 0.0
        s = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
        try: return float(s)
        except: return 0.0

    df["Qtd"] = df[col_qtd].apply(lambda x: int(limpar_num(x))) if col_qtd in df.columns else 1
    df["Preco_Custo"] = df[col_custo_str].apply(limpar_num) if col_custo_str in df.columns else 0.0
    df["Preco_Venda"] = df[col_venda_str].apply(limpar_num) if col_venda_str in df.columns else 0.0
    df["Lucro"] = df["Preco_Venda"] - df["Preco_Custo"]
    df["Categoria"] = df[col_cat].fillna("Outros").astype(str).str.strip()
    df["Valor_Total"] = df["Preco_Venda"] * df["Qtd"]

    return df[["Produto", "Categoria", "Qtd", "Preco_Custo", "Preco_Venda", "Lucro", "Valor_Total"]]

df_estoque = tratar_estoque(df_bruto)
df_caixa = carregar_aba("caixa")
df_crediario = carregar_aba("crediario")

# ---------------------------------------------------------
# INTERFACE DE NAVEGAÇÃO
# ---------------------------------------------------------
tab_dash, tab_venda, tab_est, tab_caixa, tab_cred = st.tabs([
    "📊 Dashboard", "🛒 Nova Venda", "📦 Estoque", "💰 Caixa", "📋 Crediário"
])

# --- 1. DASHBOARD ANALÍTICO ---
with tab_dash:
    st.subheader("Painel Geral de Desempenho")
    
    # Extração e ordenação segura de categorias
    if not df_estoque.empty:
        cats = [str(c).strip() for c in df_estoque["Categoria"].dropna().unique() if str(c).strip() != ""]
        categorias_unicas = ["Todas"] + sorted(list(set(cats)))
    else:
        categorias_unicas = ["Todas"]

    cat_filtro = st.selectbox("🔍 Filtrar por Categoria", categorias_unicas)
    
    df_dash = df_estoque if cat_filtro == "Todas" else df_estoque[df_estoque["Categoria"] == cat_filtro]
    
    # Cálculo das métricas
    total_itens = int(df_dash["Qtd"].sum()) if not df_dash.empty else 0
    valor_estoque = float(df_dash["Valor_Total"].sum()) if not df_dash.empty else 0.0
    lucro_estimado = float((df_dash["Qtd"] * df_dash["Lucro"]).sum()) if not df_dash.empty else 0.0
    vendas_hoje = float(df_caixa["Valor"].astype(float).sum()) if not df_caixa.empty and "Valor" in df_caixa.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Itens no Estoque", f"{total_itens} un")
    c2.metric("💰 Valor do Estoque", f"R$ {valor_estoque:,.2f}")
    c3.metric("📈 Lucro Potencial", f"R$ {lucro_estimado:,.2f}")
    c4.metric("💵 Entradas Caixa", f"R$ {vendas_hoje:,.2f}")

    st.markdown("---")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write("### Resumo por Categoria")
        if not df_dash.empty:
            resumo_cat = df_dash.groupby("Categoria").agg(
                Quantidade=("Qtd", "sum"),
                Valor_Total=("Valor_Total", "sum")
            ).reset_index()
            st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado encontrado para a categoria selecionada.")
    
    with col_b:
        st.write("### ⚠️ Estoque Baixo (≤ 1 un)")
        estoque_baixo = df_dash[df_dash["Qtd"] <= 1] if not df_dash.empty else pd.DataFrame()
        if not estoque_baixo.empty:
            for _, row in estoque_baixo.head(10).iterrows():
                st.markdown(f"<div class='card-alerta'><b>{row['Produto']}</b><br>Qtd: {row['Qtd']} un | R$ {row['Preco_Venda']:.2f}</div>", unsafe_allow_html=True)
        else:
            st.success("Estoque normal!")

# --- 2. NOVA VENDA ---
with tab_venda:
    st.subheader("Registrar Venda")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not df_estoque.empty:
            prods_disponiveis = df_estoque[df_estoque["Qtd"] > 0]
            lista_produtos = sorted([str(p) for p in prods_disponiveis["Produto"].unique() if str(p).strip() != ""])
            prod_sel = st.selectbox("Selecione o Produto", [""] + lista_produtos)
            
            # Auto-preencher preço
            preco_default = 0.0
            if prod_sel:
                filtro_prod = df_estoque[df_estoque["Produto"] == prod_sel]
                if not filtro_prod.empty:
                    preco_default = float(filtro_prod.iloc[0]["Preco_Venda"])
        else:
            prod_sel = st.text_input("Nome do Produto")
            preco_default = 0.0

        qtd_venda = st.number_input("Quantidade", min_value=1, value=1, step=1)
        preco_venda = st.number_input("Valor Unitário (R$)", min_value=0.0, value=preco_default, step=5.0)

    with col2:
        pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Crediário"])
        cliente = st.text_input("Nome do Cliente (Obrigatório para Crediário)")
        
        total_venda = qtd_venda * preco_venda
        st.metric("Total da Venda", f"R$ {total_venda:,.2f}")

        if st.button("✅ FINALIZAR VENDA"):
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Registro no Caixa
            novo_caixa = pd.DataFrame([{
                "Data": data_hoje, "Tipo": "Entrada", "Descrição": f"Venda: {prod_sel}",
                "Valor": total_venda, "Forma": pagamento, "Cliente": cliente
            }])
            df_caixa_atual = pd.concat([df_caixa, novo_caixa], ignore_index=True)
            salvar_aba(df_caixa_atual, "caixa")

            # Se for Crediário
            if pagamento == "Crediário":
                novo_cred = pd.DataFrame([{
                    "Data": data_hoje, "Cliente": cliente if cliente else "Cliente",
                    "Produto": prod_sel, "Valor": total_venda, "Status": "Pendente"
                }])
                df_cred_atual = pd.concat([df_crediario, novo_cred], ignore_index=True)
                salvar_aba(df_cred_atual, "crediario")

            st.success("Venda registrada com sucesso!")
            st.rerun()

# --- 3. ESTOQUE ---
with tab_est:
    st.subheader("Lista Geral do Estoque")
    if not df_estoque.empty:
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum produto cadastrado no estoque.")

# --- 4. CAIXA ---
with tab_caixa:
    st.subheader("Movimentações do Caixa")
    if not df_caixa.empty:
        st.dataframe(df_caixa, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma movimentação registrada no caixa.")

# --- 5. CREDIÁRIO ---
with tab_cred:
    st.subheader("Controle de Crediário")
    if not df_crediario.empty:
        st.dataframe(df_crediario, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de crediário.")
