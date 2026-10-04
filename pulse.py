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

def ler_planilha_tentativas(abas_possiveis):
    for aba in abas_possiveis:
        try:
            df = conn.read(worksheet=aba, ttl=0)
            if df is not None and not df.empty:
                return df, aba
        except Exception:
            continue
    try:
        df = conn.read(ttl=0)
        return df if df is not None else pd.DataFrame(), "Padrão"
    except Exception:
        return pd.DataFrame(), "Nenhuma"

def salvar_aba(df, nome_aba):
    try:
        conn.update(worksheet=nome_aba, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar na aba {nome_aba}: {e}")

# ---------------------------------------------------------
# CARREGAMENTO E MAPEAMENTO INTELIGENTE DA PLANILHA PULSE
# ---------------------------------------------------------
# Abas reais do seu Google Sheets: Cad att, Perfumes Arabes, Cadastros, Registro de Fiados
df_estoque_bruto, aba_usada_est = ler_planilha_tentativas(["Cad att", "Perfumes Arabes", "Cadastros", "estoque"])
df_cred_bruto, aba_usada_cred = ler_planilha_tentativas(["Registro de Fiados", "crediario", "Fiados"])
df_caixa_bruto, aba_usada_caixa = ler_planilha_tentativas(["Outubro", "Setembro", "caixa", "Caixa"])

def encontrar_e_promover_cabecalho(df):
    if df.empty:
        return df
    
    keywords_cabecalho = ["categoria", "marca", "coluna 6", "nome", "produto", "preço de venda", "venda", "custo"]
    
    for idx in range(min(15, len(df))):
        linha_vals = [str(v).lower().strip() for v in df.iloc[idx].values]
        matches = sum(1 for kw in keywords_cabecalho if any(kw in v for v in linha_vals))
        if matches >= 2:
            novas_colunas = [str(v).strip() if pd.notna(v) and str(v).strip() != "" else f"Col_{i}" for i, v in enumerate(df.iloc[idx].values)]
            df_promovido = df.iloc[idx + 1:].copy().reset_index(drop=True)
            df_promovido.columns = novas_colunas
            return df_promovido
            
    return df

def tratar_num(val):
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).replace("R$", "").replace("\xa0", "").strip()
    if not s or s.lower() in ["none", "nan", "#div/0!", "-", "null"]:
        return 0.0
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def processar_estoque(df_bruto):
    df = encontrar_e_promover_cabecalho(df_bruto)
    if df.empty:
        return pd.DataFrame(columns=["Produto", "Categoria", "Qtd", "Preco_Custo", "Preco_Venda", "Lucro", "Valor_Total"])

    cols_lower = {str(c).lower().strip(): c for c in df.columns}

    col_cat_key = next((k for k in cols_lower if "categoria" in k), None)
    col_cat = cols_lower[col_cat_key] if col_cat_key else None

    col_marca_key = next((k for k in cols_lower if "marca" in k), None)
    col_marca = cols_lower[col_marca_key] if col_marca_key else None

    col_nome_key = next((k for k in cols_lower if k in ["coluna 6", "nome", "produto", "modelo", "descrição"]), None)
    if not col_nome_key:
        col_nome_key = next((k for k in cols_lower if "nome" in k or "produto" in k or "modelo" in k), None)
    col_nome = cols_lower[col_nome_key] if col_nome_key else None

    col_qtd_key = next((k for k in cols_lower if k in ["column", "column 12", "qtd", "quantidade", "nun"]), None)
    if not col_qtd_key:
        col_qtd_key = next((k for k in cols_lower if "qtd" in k or "quant" in k), None)
    col_qtd = cols_lower[col_qtd_key] if col_qtd_key else None

    col_custo_key = next((k for k in cols_lower if "custo" in k), None)
    col_custo = cols_lower[col_custo_key] if col_custo_key else None

    col_venda_key = next((k for k in cols_lower if "venda" in k or "preço de venda" in k), None)
    col_venda = cols_lower[col_venda_key] if col_venda_key else None

    dados_processados = []

    for _, row in df.iterrows():
        cat = str(row[col_cat]).strip() if col_cat and pd.notna(row[col_cat]) else "Outros"
        marca = str(row[col_marca]).strip() if col_marca and pd.notna(row[col_marca]) else ""
        nome = str(row[col_nome]).strip() if col_nome and pd.notna(row[col_nome]) else ""

        if cat.lower() in ["categoria", "total", "a vista", "nan", "none", ""] and not nome:
            continue
        if cat in ["TOTAL", "A VISTA"] or "R$" in cat:
            continue

        if marca and nome and marca.lower() not in nome.lower():
            prod = f"{marca} - {nome}"
        elif nome:
            prod = nome
        elif marca:
            prod = marca
        else:
            continue

        qtd = int(tratar_num(row[col_qtd])) if col_qtd else 1
        p_custo = tratar_num(row[col_custo]) if col_custo else 0.0
        p_venda = tratar_num(row[col_venda]) if col_venda else 0.0
        lucro = p_venda - p_custo
        v_total = p_venda * qtd

        dados_processados.append({
            "Produto": prod,
            "Categoria": cat if cat else "Geral",
            "Qtd": max(0, qtd),
            "Preco_Custo": p_custo,
            "Preco_Venda": p_venda,
            "Lucro": lucro,
            "Valor_Total": v_total
        })

    res_df = pd.DataFrame(dados_processados)
    if res_df.empty:
        return pd.DataFrame(columns=["Produto", "Categoria", "Qtd", "Preco_Custo", "Preco_Venda", "Lucro", "Valor_Total"])
    return res_df

df_estoque = processar_estoque(df_estoque_bruto)
df_caixa = df_caixa_bruto
df_crediario = df_cred_bruto

# ---------------------------------------------------------
# INTERFACE DO SISTEMA
# ---------------------------------------------------------
tab_dash, tab_venda, tab_est, tab_caixa, tab_cred = st.tabs([
    "📊 Dashboard", "🛒 Nova Venda", "📦 Estoque", "💰 Caixa", "📋 Crediário"
])

# --- 1. DASHBOARD ---
with tab_dash:
    st.subheader("Painel Geral de Desempenho")
    
    if not df_estoque.empty:
        cats = sorted(list(set([str(c).strip() for c in df_estoque["Categoria"].unique() if str(c).strip() not in ["", "nan", "None"]])))
        categorias_unicas = ["Todas"] + cats
    else:
        categorias_unicas = ["Todas"]

    cat_filtro = st.selectbox("🔍 Filtrar por Categoria", categorias_unicas)
    
    df_dash = df_estoque if cat_filtro == "Todas" else df_estoque[df_estoque["Categoria"] == cat_filtro]
    
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
                st.markdown(f"<div class='card-alerta'><b>{row['Produto']}</b><br>Categoria: {row['Categoria']}<br>Qtd: {row['Qtd']} un | R$ {row['Preco_Venda']:.2f}</div>", unsafe_allow_html=True)
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
            
            novo_caixa = pd.DataFrame([{
                "Data": data_hoje, "Tipo": "Entrada", "Descrição": f"Venda: {prod_sel}",
                "Valor": total_venda, "Forma": pagamento, "Cliente": cliente
            }])
            df_caixa_atual = pd.concat([df_caixa, novo_caixa], ignore_index=True)
            salvar_aba(df_caixa_atual, "caixa")

            if pagamento == "Crediário":
                novo_cred = pd.DataFrame([{
                    "Data": data_hoje, "Cliente": cliente if cliente else "Cliente",
                    "Produto": prod_sel, "Valor": total_venda, "Status": "Pendente"
                }])
                df_cred_atual = pd.concat([df_crediario, novo_cred], ignore_index=True)
                salvar_aba(df_cred_atual, "Registro de Fiados")

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
    st.subheader("Controle de Crediário (Registro de Fiados)")
    if not df_crediario.empty:
        st.dataframe(df_crediario, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de crediário.")
