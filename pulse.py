import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA (LAYOUT WIDE & MENU LATERAL RECOLHIDO POR PADRÃO)
# ==============================================================================
st.set_page_config(
    page_title="Pulse Store - Vendas & Gestão",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# ESTILIZAÇÃO CSS CUSTOMIZADA COMPACTA (DESIGN PERFEITO & REFINADO)
# ==============================================================================
st.markdown("""
<style>
    /* 1. Ajuste do Espaçamento Superior para não cortar o cabeçalho */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 99% !important;
    }

    /* 2. Redução do Espaçamento Vertical entre Blocos */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.35rem !important;
    }

    /* 3. Linhas Divisórias Ajustadas */
    hr, [data-testid="stDivider"] {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* 4. Fontes Globais Otimizadas */
    html, body, [data-testid="stAppViewContainer"] {
        font-size: 0.82rem !important;
    }

    h1 { font-size: 1.25rem !important; margin-bottom: 0.1rem !important; padding-top: 0 !important; font-weight: 800 !important; }
    h2 { font-size: 1.05rem !important; margin-bottom: 0.1rem !important; font-weight: 700 !important; }
    h3 { font-size: 0.95rem !important; margin-bottom: 0.1rem !important; font-weight: 700 !important; }
    h4 { font-size: 0.88rem !important; margin-bottom: 0.1rem !important; font-weight: 600 !important; }

    /* 5. Inputs e Seletores Compactos */
    label, .stWidgetLabel, [data-testid="stWidgetLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.1rem !important;
    }

    input, select, div[data-baseweb="select"], .stNumberInput input {
        font-size: 0.80rem !important;
        padding: 4px 8px !important;
        min-height: 30px !important;
    }

    /* 6. Botões Compactos */
    div.stButton > button {
        padding: 4px 10px !important;
        font-size: 0.82rem !important;
        min-height: 30px !important;
    }

    /* 7. Estilização do Menu Lateral (Fundo creme/marfim) */
    [data-testid="stSidebar"] {
        background-color: #F8F5F0 !important;
        border-right: 1px solid #E5DEC9;
    }

    .categoria-titulo {
        color: #4A2E1B;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 10px;
        margin-bottom: 4px;
        padding-bottom: 2px;
        border-bottom: 2px solid #D4AF37;
        display: block;
    }

    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #3D2314 0%, #22120A 100%) !important;
        color: #F8F3E6 !important;
        border: 1px solid #5A3620 !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 0.82rem !important;
        margin-bottom: 2px !important;
    }

    [data-testid="stSidebar"] div.stButton > button:hover {
        background: linear-gradient(135deg, #D4AF37 0%, #B38E20 100%) !important;
        color: #1A0D05 !important;
        border-color: #D4AF37 !important;
    }

    /* 8. Banner de Total do PDV Estilo Caixa Slim */
    .total-banner-pdv {
        background: linear-gradient(135deg, #5C1D24 0%, #3D1016 100%);
        color: #FFFFFF;
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.45rem;
        font-weight: 800;
        box-shadow: 0px 2px 6px rgba(92, 29, 36, 0.3);
        margin-top: 4px;
        margin-bottom: 4px;
        border: 1px solid #7D2932;
    }
</style>
""", unsafe_allow_html=True)

# Definição das colunas padrão do sistema
COLUNAS_ESTOQUE = ['Categoria', 'Quantidade', 'Tamanho', 'Marca', 'Produto', 'Custo (R$)', 'Preço Venda (R$)', 'Lucro (R$)', 'Fornecedor']
COLUNAS_CAIXA = ['ID', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor (R$)', 'Forma Pagamento']
COLUNAS_CREDIARIO = ['ID_Parcela', 'ID_Venda', 'Cliente', 'Telefone', 'CPF', 'Data_Venda', 'Parcela_Num', 'Total_Parcelas', 'Valor_Parcela (R$)', 'Vencimento', 'Status']

# --- CONEXÃO COM O GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

# --- CARREGAR LOGO DA LOJA ---
def carregar_logo():
    extensoes = ('.png', '.jpg', '.jpeg', '.webp', '.svg')
    ficheiros = [f for f in os.listdir('.') if f.lower().endswith(extensoes)]
    for f in ficheiros:
        if 'logo' in f.lower() or 'pulse' in f.lower():
            return f
    return ficheiros[0] if ficheiros else None

logo_path = carregar_logo()

# --- TOPO DE MARKETING & LOGO (VISÍVEL E ALINHADO) ---
col_logo, col_mkt = st.columns([0.8, 4.2])
with col_logo:
    if logo_path:
        st.image(logo_path, width=90)
    else:
        st.markdown("### ⚡ **PULSE STORE**")

with col_mkt:
    st.markdown("""
    <div style="background-color: #F8F5F0; padding: 8px 16px; border-radius: 8px; border-left: 5px solid #D4AF37; border: 1px solid #E5DEC9; margin-top: 2px;">
        <span style="font-size: 1.00rem; font-weight: 800; color: #3D2314;">⚡ PULSE STORE - VENDAS & GESTÃO</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="font-size: 0.82rem; color: #5A3620;">
            🛍️ <b>Site Oficial:</b> <a href="https://pulsestore35.lojavirtualnuvem.com.br/" target="_blank" style="color: #8B5A2B; font-weight: 700; text-decoration: underline;">pulsestore35.lojavirtualnuvem.com.br</a>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            📸 <b>Instagram:</b> <a href="https://www.instagram.com/pulsestore__/" target="_blank" style="color: #8B5A2B; font-weight: 700; text-decoration: underline;">@pulsestore__</a>
        </span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- FUNÇÕES DE CONVERSÃO E FORMATAÇÃO MONETÁRIA ---
def tratar_moeda(valor):
    if pd.isna(valor) or valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    val_str = str(valor).strip()
    if not val_str or val_str.lower() in ['none', 'nan', 'null', '#div/0!']:
        return 0.0
    val_str = val_str.replace('R$', '').replace('\xa0', '').replace(' ', '')
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except:
        return 0.0

def tratar_int(valor):
    if pd.isna(valor) or valor is None:
        return 0
    if isinstance(valor, (int, float)):
        return int(valor)
    val_str = str(valor).replace(',', '.').strip()
    val_clean = re.sub(r'[^0-9]', '', val_str.split('.')[0])
    try:
        return int(val_clean) if val_clean != '' else 0
    except:
        return 0

def safe_str(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ['nan', 'none', '<na>', 'null'] else s

def fmt_real(val):
    return f"R$ {val:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

# --- GERENCIADOR DE INTEGRAÇÃO COM GOOGLE SHEETS & FALLBACK LOCAL ---
def promover_cabecalho_se_necessario(df):
    if df.empty:
        return df
    keywords = ["categoria", "marca", "coluna 6", "produto", "preço de venda", "venda", "custo", "fornecedor"]
    for idx in range(min(12, len(df))):
        vals = [str(v).lower().strip() for v in df.iloc[idx].values]
        if sum(1 for kw in keywords if any(kw in v for v in vals)) >= 2:
            novas_cols = [str(v).strip() if pd.notna(v) and str(v).strip() != "" else f"Col_{i}" for i, v in enumerate(df.iloc[idx].values)]
            df_prom = df.iloc[idx + 1:].copy().reset_index(drop=True)
            df_prom.columns = novas_cols
            return df_prom
    return df

def carregar_dados(aba_nome, colunas_padrao, abas_alternativas=[]):
    df_raw = pd.DataFrame()
    if conn is not None:
        for aba in [aba_nome] + abas_alternativas:
            try:
                df_temp = conn.read(worksheet=aba, ttl=0)
                if df_temp is not None and not df_temp.empty:
                    df_raw = df_temp
                    break
            except Exception:
                continue
        if df_raw.empty:
            try:
                df_raw = conn.read(ttl=0)
            except Exception:
                pass

    local_csv = f"{aba_nome}.csv"
    if df_raw.empty and os.path.exists(local_csv):
        try:
            df_raw = pd.read_csv(local_csv)
        except Exception:
            pass

    if df_raw.empty:
        return pd.DataFrame(columns=colunas_padrao)

    df_raw = promover_cabecalho_se_necessario(df_raw)

    # Mapeamento inteligente para a aba de estoque
    if colunas_padrao == COLUNAS_ESTOQUE:
        cols_lower = {str(c).lower().strip(): c for c in df_raw.columns}
        col_cat = cols_lower.get(next((k for k in cols_lower if "categoria" in k), ""), "")
        col_marca = cols_lower.get(next((k for k in cols_lower if "marca" in k), ""), "")
        col_prod = cols_lower.get(next((k for k in cols_lower if k in ["coluna 6", "produto", "nome", "modelo"]), ""), "")
        col_tam = cols_lower.get(next((k for k in cols_lower if k in ["tamanho", "nun", "tam"]), ""), "")
        col_qtd = cols_lower.get(next((k for k in cols_lower if k in ["quantidade", "qtd", "column", "column 12"]), ""), "")
        col_custo = cols_lower.get(next((k for k in cols_lower if "custo" in k), ""), "")
        col_venda = cols_lower.get(next((k for k in cols_lower if "venda" in k), ""), "")
        col_forn = cols_lower.get(next((k for k in cols_lower if "fornecedor" in k), ""), "")

        if col_cat or col_prod or col_venda:
            dados = []
            for _, r in df_raw.iterrows():
                cat = safe_str(r[col_cat]) if col_cat else "Geral"
                marca = safe_str(r[col_marca]) if col_marca else ""
                prod = safe_str(r[col_prod]) if col_prod else ""
                if not prod and marca: prod = marca
                if not prod and not cat: continue
                if cat.upper() in ["TOTAL", "A VISTA"] or "R$" in cat: continue

                qtd = tratar_int(r[col_qtd]) if col_qtd else 1
                tam = safe_str(r[col_tam]) if col_tam else ""
                custo = tratar_moeda(r[col_custo]) if col_custo else 0.0
                venda = tratar_moeda(r[col_venda]) if col_venda else 0.0
                lucro = venda - custo
                forn = safe_str(r[col_forn]) if col_forn else ""

                dados.append({
                    'Categoria': cat if cat else "Geral",
                    'Quantidade': max(0, qtd),
                    'Tamanho': tam,
                    'Marca': marca if marca else "Pulse",
                    'Produto': prod,
                    'Custo (R$)': custo,
                    'Preço Venda (R$)': venda,
                    'Lucro (R$)': lucro,
                    'Fornecedor': forn
                })
            return pd.DataFrame(dados, columns=COLUNAS_ESTOQUE)

    # Garantir a presença das colunas padrão
    for c in colunas_padrao:
        if c not in df_raw.columns:
            df_raw[c] = 0 if ('R$' in c or c in ['Quantidade', 'ID', 'ID_Parcela', 'ID_Venda', 'Parcela_Num', 'Total_Parcelas']) else ''
    return df_raw[colunas_padrao].copy()

def salvar_dados(df, aba_nome):
    local_csv = f"{aba_nome}.csv"
    try:
        df.to_csv(local_csv, index=False)
    except Exception:
        pass

    if conn is not None:
        try:
            conn.update(worksheet=aba_nome, data=df)
            st.cache_data.clear()
        except Exception:
            pass

# Carregar bases de dados
df_estoque = carregar_dados("estoque", COLUNAS_ESTOQUE, abas_alternativas=["Cad att", "Perfumes Arabes", "Cadastros"])
df_caixa = carregar_dados("caixa", COLUNAS_CAIXA, abas_alternativas=["Outubro", "Setembro"])
df_crediario = carregar_dados("crediario", COLUNAS_CREDIARIO, abas_alternativas=["Registro de Fiados", "Fiados"])

# Normalização de tipos
if not df_estoque.empty:
    df_estoque['Categoria'] = df_estoque['Categoria'].apply(safe_str)
    df_estoque['Quantidade'] = df_estoque['Quantidade'].apply(tratar_int)
    df_estoque['Tamanho'] = df_estoque['Tamanho'].apply(safe_str)
    df_estoque['Marca'] = df_estoque['Marca'].apply(safe_str)
    df_estoque['Produto'] = df_estoque['Produto'].apply(safe_str)
    df_estoque['Custo (R$)'] = df_estoque['Custo (R$)'].apply(tratar_moeda)
    df_estoque['Preço Venda (R$)'] = df_estoque['Preço Venda (R$)'].apply(tratar_moeda)
    df_estoque['Lucro (R$)'] = df_estoque['Preço Venda (R$)'] - df_estoque['Custo (R$)']
    df_estoque['Fornecedor'] = df_estoque['Fornecedor'].apply(safe_str)

if not df_caixa.empty:
    df_caixa['Valor (R$)'] = df_caixa['Valor (R$)'].apply(tratar_moeda)

if not df_crediario.empty:
    df_crediario['Valor_Parcela (R$)'] = df_crediario['Valor_Parcela (R$)'].apply(tratar_moeda)

# --- INICIALIZAR CARRINHO NO SESSION STATE ---
if 'carrinho' not in st.session_state:
    st.session_state['carrinho'] = []

# --- MENU LATERAL CATEGORIZADO & ROBUSTO ---
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = "🛍️ Vendas Pulse"

with st.sidebar:
    if logo_path:
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("### ⚡ **PULSE STORE**")
    st.markdown("---")

    st.markdown('<p class="categoria-titulo">🛍️ Operacional & Vendas</p>', unsafe_allow_html=True)

    if st.button("🛍️️  Vendas Pulse", use_container_width=True, type="primary" if st.session_state['pagina'] == "🛍️ Vendas Pulse" else "secondary"):
        st.session_state['pagina'] = "🛍️ Vendas Pulse"

    if st.button("💳  Gestão de Crediário", use_container_width=True, type="primary" if st.session_state['pagina'] == "💳 Gestão de Crediário" else "secondary"):
        st.session_state['pagina'] = "💳 Gestão de Crediário"

    if st.button("📊  Dashboard Analítico", use_container_width=True, type="primary" if st.session_state['pagina'] == "📊 Dashboard Analítico" else "secondary"):
        st.session_state['pagina'] = "📊 Dashboard Analítico"

    st.markdown('<p class="categoria-titulo">📦 Gestão de Estoque</p>', unsafe_allow_html=True)

    if st.button("➕  Cadastrar Produto", use_container_width=True, type="primary" if st.session_state['pagina'] == "➕ Cadastrar Produto" else "secondary"):
        st.session_state['pagina'] = "➕ Cadastrar Produto"

    if st.button("📦  Tabela de Estoque (Excel)", use_container_width=True, type="primary" if st.session_state['pagina'] == "📦 Tabela de Estoque (Excel)" else "secondary"):
        st.session_state['pagina'] = "📦 Tabela de Estoque (Excel)"

    st.markdown('<p class="categoria-titulo">⚙️ Painel Administrativo</p>', unsafe_allow_html=True)

    if st.button("💰  Contabilidade & Caixa", use_container_width=True, type="primary" if st.session_state['pagina'] == "💰 Contabilidade & Caixa" else "secondary"):
        st.session_state['pagina'] = "💰 Contabilidade & Caixa"

    if st.button("🔍  Antiduplicação", use_container_width=True, type="primary" if st.session_state['pagina'] == "🔍 Antiduplicação" else "secondary"):
        st.session_state['pagina'] = "🔍 Antiduplicação"

    if st.button("📥  Importar 'Cad att' (Excel)", use_container_width=True, type="primary" if st.session_state['pagina'] == "📥 Importar 'Cad att' (Excel)" else "secondary"):
        st.session_state['pagina'] = "📥 Importar 'Cad att' (Excel)"

pagina = st.session_state['pagina']

# ==============================================================================
# PÁGINA 1: VENDAS PULSE (PDV MULTI-ITENS COMPACTO)
# ==============================================================================
if pagina == "🛍️ Vendas Pulse":
    st.title("🛍️ Vendas Pulse - Ponto de Venda (PDV)")

    if df_estoque.empty:
        st.warning("O seu estoque está vazio. Importe a sua planilha na aba 'Importar Cad att' ou cadastre novos produtos.")
    else:
        df_pdv = df_estoque.copy()
        df_pdv['Item_Select'] = (
            df_pdv['Marca'] + " | " +
            df_pdv['Produto'] + " " +
            df_pdv['Tamanho'].apply(lambda x: f"({x})" if x else "") +
            " - Est: " + df_pdv['Quantidade'].astype(str) + "un."
        )

        col_left, col_right = st.columns([1.1, 1.4])

        with col_left:
            st.markdown("#### 1. Buscar Produto")
            item_escolhido = st.selectbox("Pesquisar Produto do Estoque:", df_pdv['Item_Select'].unique(), key="sb_item_pdv")

            idx = df_pdv[df_pdv['Item_Select'] == item_escolhido].index[0]
            prod_row = df_pdv.loc[idx]

            qtd_ja_no_carrinho = sum([item['qtd'] for item in st.session_state['carrinho'] if item['idx_estoque'] == idx])
            estoque_disponivel_real = max(0, int(prod_row['Quantidade']) - qtd_ja_no_carrinho)

            c_info1, c_info2 = st.columns(2)
            c_info1.info(f"**Categoria:** {prod_row['Categoria']}")
            c_info2.success(f"**Disponível:** {estoque_disponivel_real} un.")

            st.divider()

            st.markdown("#### 2. Preço & Quantidade")
            c_p1, c_p2 = st.columns(2)

            preco_unitario_add = c_p1.number_input(
                "Preço Unitário (R$)",
                value=float(prod_row['Preço Venda (R$)']),
                min_value=0.0,
                step=5.0,
                format="%.2f",
                key=f"preco_add_{idx}"
            )

            max_qtd_add = max(1, estoque_disponivel_real)
            qtd_add = c_p2.number_input("Quantidade", min_value=1, max_value=max_qtd_add, value=1, step=1, key=f"qtd_add_{idx}")

            btn_add_cart = st.button("➕ ADICIONAR AO CARRINHO", use_container_width=True, type="primary")

            if btn_add_cart:
                if estoque_disponivel_real < qtd_add:
                    st.error("Quantidade solicitada excede o estoque disponível!")
                else:
                    item_existente = False
                    for item in st.session_state['carrinho']:
                        if item['idx_estoque'] == idx and item['preco_unitario'] == preco_unitario_add:
                            item['qtd'] += qtd_add
                            item_existente = True
                            break

                    if not item_existente:
                        st.session_state['carrinho'].append({
                            'idx_estoque': idx,
                            'categoria': prod_row['Categoria'],
                            'marca': prod_row['Marca'],
                            'produto': prod_row['Produto'],
                            'tamanho': prod_row['Tamanho'],
                            'preco_unitario': preco_unitario_add,
                            'custo_unitario': prod_row['Custo (R$)'],
                            'qtd': qtd_add,
                            'max_estoque': int(prod_row['Quantidade'])
                        })
                    st.toast("Item adicionado!", icon="🛒")
                    st.rerun()

        with col_right:
            st.markdown(f"#### 🛒 Carrinho de Compras ({len(st.session_state['carrinho'])} itens)")

            if not st.session_state['carrinho']:
                st.info("Carrinho vazio.")
            else:
                subtotal_carrinho = 0.0

                for i, item in enumerate(st.session_state['carrinho']):
                    subtotal_item = item['preco_unitario'] * item['qtd']
                    subtotal_carrinho += subtotal_item

                    nome_exibicao = f"**{item['marca']} {item['produto']}** " + (f"({item['tamanho']})" if item['tamanho'] else "")

                    c_det, c_qtd_ctrl, c_sub, c_del = st.columns([3.5, 2, 2, 1])

                    c_det.markdown(f"**Nº {i+1}** - {nome_exibicao}<br><small>{item['qtd']}x {fmt_real(item['preco_unitario'])}</small>", unsafe_allow_html=True)

                    c_q1, c_q2 = c_qtd_ctrl.columns(2)
                    if c_q1.button("➖", key=f"minus_{i}"):
                        if item['qtd'] > 1:
                            item['qtd'] -= 1
                        else:
                            st.session_state['carrinho'].pop(i)
                        st.rerun()

                    if c_q2.button("➕", key=f"plus_{i}"):
                        if item['qtd'] < item['max_estoque']:
                            item['qtd'] += 1
                        else:
                            st.warning("Limite do estoque atingido!")
                        st.rerun()

                    c_sub.markdown(f"**{fmt_real(subtotal_item)}**")

                    if c_del.button("❌", key=f"del_{i}"):
                        st.session_state['carrinho'].pop(i)
                        st.rerun()

                st.divider()

                c_limpar, c_desc = st.columns([1, 2])
                if c_limpar.button("🧹 Limpar Carrinho"):
                    st.session_state['carrinho'] = []
                    st.rerun()

                desconto_geral = c_desc.number_input("Desconto Geral (R$)", min_value=0.0, max_value=subtotal_carrinho, step=5.0, value=0.0)

                total_final = max(0.0, subtotal_carrinho - desconto_geral)

                st.markdown(f'<div class="total-banner-pdv">🛒 TOTAL: {fmt_real(total_final)}</div>', unsafe_allow_html=True)

                st.markdown("#### 3. Finalizar Venda")
                with st.form("form_finalizar_venda_pdv"):
                    forma_pagto = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Crediário (Fiado)"])

                    nome_cliente = ""
                    telefone_cliente = ""
                    cpf_cliente = ""
                    qtd_parcelas = 1
                    if forma_pagto == "Crediário (Fiado)":
                        st.markdown("**📝 Dados do Crediário**")
                        nome_cliente = st.text_input("Nome Completo:")
                        col_cred_a, col_cred_b = st.columns(2)
                        telefone_cliente = col_cred_a.text_input("Telefone / WhatsApp:")
                        cpf_cliente = col_cred_b.text_input("CPF:")
                        qtd_parcelas = st.number_input("Número de Parcelas:", min_value=1, max_value=12, value=1, step=1)
                        if qtd_parcelas > 1:
                            st.caption(f"Valor por parcela: {fmt_real(total_final / qtd_parcelas)}")

                    btn_finalizar = st.form_submit_button("✅ FINALIZAR COMPRA COMPLETA", type="primary", use_container_width=True)

                    if btn_finalizar:
                        if forma_pagto == "Crediário (Fiado)" and not nome_cliente.strip():
                            st.error("Informe o nome do cliente para a venda no Crediário.")
                        else:
                            id_venda = int(datetime.now().timestamp())
                            itens_resumo = []

                            for item in st.session_state['carrinho']:
                                idx_est = item['idx_estoque']
                                df_estoque.loc[idx_est, 'Quantidade'] -= item['qtd']
                                itens_resumo.append(f"{item['qtd']}x {item['marca']} {item['produto']}")

                            salvar_dados(df_estoque, "estoque")

                            desc_venda_completa = f"Venda PDV ({len(st.session_state['carrinho'])} itens): " + ", ".join(itens_resumo)

                            if forma_pagto != "Crediário (Fiado)":
                                nova_trans = pd.DataFrame([{
                                    'ID': id_venda,
                                    'Data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                                    'Tipo': 'Entrada',
                                    'Categoria': "Venda PDV (Multi-itens)",
                                    'Descrição': desc_venda_completa,
                                    'Valor (R$)': total_final,
                                    'Forma Pagamento': forma_pagto
                                }])
                                df_caixa_up = pd.concat([df_caixa, nova_trans], ignore_index=True)
                                salvar_dados(df_caixa_up, "caixa")
                            else:
                                val_parcela = total_final / qtd_parcelas
                                novas_parcelas = []
                                data_atual = datetime.now()

                                for p in range(1, qtd_parcelas + 1):
                                    vencimento = data_atual + timedelta(days=30 * p)
                                    novas_parcelas.append({
                                        'ID_Parcela': int(datetime.now().timestamp()) + p,
                                        'ID_Venda': id_venda,
                                        'Cliente': nome_cliente.strip(),
                                        'Telefone': telefone_cliente.strip(),
                                        'CPF': cpf_cliente.strip(),
                                        'Data_Venda': data_atual.strftime("%d/%m/%Y"),
                                        'Parcela_Num': p,
                                        'Total_Parcelas': qtd_parcelas,
                                        'Valor_Parcela (R$)': val_parcela,
                                        'Vencimento': vencimento.strftime("%d/%m/%Y"),
                                        'Status': 'Pendente'
                                    })
                                df_cred_up = pd.concat([df_crediario, pd.DataFrame(novas_parcelas)], ignore_index=True)
                                salvar_dados(df_cred_up, "crediario")

                            st.session_state['carrinho'] = []
                            st.balloons()
                            st.success("🎉 Venda finalizada com sucesso!")
                            st.rerun()

# ==============================================================================
# PÁGINA 2: GESTÃO DE CREDIÁRIO (BAIXA DE PARCELAS)
# ==============================================================================
elif pagina == "💳 Gestão de Crediário":
    st.title("💳 Gestão de Crediário / Fiado")

    if df_crediario.empty:
        st.info("Nenhuma venda no crediário foi realizada ainda.")
    else:
        pendentes = df_crediario[df_crediario['Status'] == 'Pendente']
        pagos = df_crediario[df_crediario['Status'] == 'Pago']

        total_pendente = pendentes['Valor_Parcela (R$)'].sum()
        total_pago = pagos['Valor_Parcela (R$)'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("🔴 Total a Receber", fmt_real(total_pendente))
        m2.metric("🟢 Total Recebido", fmt_real(total_pago))
        m3.metric("📋 Parcelas Pendentes", f"{len(pendentes)} parcelas")

        st.divider()

        col_f1, col_f2 = st.columns(2)
        clientes_lista = ["Todos"] + sorted(list(df_crediario['Cliente'].unique()))
        cliente_sel = col_f1.selectbox("Filtrar por Cliente:", clientes_lista)
        status_sel = col_f2.radio("Status da Parcela:", ["Pendentes", "Pagos", "Todos"], horizontal=True)

        df_view_cred = df_crediario.copy()
        if cliente_sel != "Todos":
            df_view_cred = df_view_cred[df_view_cred['Cliente'] == cliente_sel]
        if status_sel == "Pendentes":
            df_view_cred = df_view_cred[df_view_cred['Status'] == 'Pendente']
        elif status_sel == "Pagos":
            df_view_cred = df_view_cred[df_view_cred['Status'] == 'Pago']

        st.markdown("#### 📋 Lista de Parcelas")

        if df_view_cred.empty:
            st.write("Nenhuma parcela encontrada.")
        else:
            for idx_cred, row_cred in df_view_cred.iterrows():
                c_cli, c_parc, c_val, c_venc, c_stat, c_act = st.columns([3, 2, 2, 2, 2, 2])

                info_contato = []
                if safe_str(row_cred.get('Telefone', '')):
                    info_contato.append(f"📱 {row_cred['Telefone']}")
                if safe_str(row_cred.get('CPF', '')):
                    info_contato.append(f"📄 CPF: {row_cred['CPF']}")
                str_contato = " | ".join(info_contato)

                c_cli.markdown(f"👤 **{row_cred['Cliente']}**" + (f"<br><small>{str_contato}</small>" if str_contato else ""), unsafe_allow_html=True)
                c_parc.write(f"Parc. {row_cred['Parcela_Num']}/{row_cred['Total_Parcelas']}")
                c_val.write(fmt_real(row_cred['Valor_Parcela (R$)']))
                c_venc.write(f"📅 {row_cred['Vencimento']}")

                if row_cred['Status'] == 'Pendente':
                    c_stat.markdown("🔴 **Pendente**")
                    if c_act.button("✅ Dar Baixa", key=f"baixa_{row_cred['ID_Parcela']}"):
                        df_crediario.loc[idx_cred, 'Status'] = 'Pago'
                        salvar_dados(df_crediario, "crediario")

                        nova_tr = pd.DataFrame([{
                            'ID': int(datetime.now().timestamp()),
                            'Data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                            'Tipo': 'Entrada',
                            'Categoria': 'Recebimento Crediário',
                            'Descrição': f"Baixa Parcela {row_cred['Parcela_Num']}/{row_cred['Total_Parcelas']} - Cliente: {row_cred['Cliente']}",
                            'Valor (R$)': row_cred['Valor_Parcela (R$)'],
                            'Forma Pagamento': 'Crediário Recebido'
                        }])
                        df_caixa_up = pd.concat([df_caixa, nova_tr], ignore_index=True)
                        salvar_dados(df_caixa_up, "caixa")

                        st.success("Baixa efetuada com sucesso!")
                        st.rerun()
                else:
                    c_stat.markdown("🟢 **Pago**")
                    c_act.write("—")

# ==============================================================================
# PÁGINA 3: DASHBOARD ANALÍTICO (COMPACTO)
# ==============================================================================
elif pagina == "📊 Dashboard Analítico":
    st.title("📊 Dashboard Analítico & Margem de Lucro")

    if df_estoque.empty:
        st.info("💡 Sem dados para exibir no Dashboard.")
    else:
        cats_disponiveis = ["Todas as Categorias"] + sorted([c for c in df_estoque['Categoria'].dropna().unique() if c != ''])
        cat_selecionada = st.selectbox("🎯 Filtrar Dashboard por Categoria:", cats_disponiveis, key="filtro_cat_dash")

        if cat_selecionada != "Todas as Categorias":
            df_dash = df_estoque[df_estoque['Categoria'] == cat_selecionada].copy()
        else:
            df_dash = df_estoque.copy()

        if df_dash.empty:
            st.warning("Nenhum produto encontrado para a categoria selecionada.")
        else:
            total_cadastros = len(df_dash)
            total_pecas = int(df_dash['Quantidade'].sum())
            total_custo = (df_dash['Custo (R$)'] * df_dash['Quantidade']).sum()
            total_venda = (df_dash['Preço Venda (R$)'] * df_dash['Quantidade']).sum()
            total_lucro = total_venda - total_custo
            margem_global = (total_lucro / total_venda * 100) if total_venda > 0 else 0.0

            k1, k2, k3, k4, k5 = st.columns(5)

            with k1:
                st.markdown(f'''
                <div style="background: #1E1E1E; border: 1px solid #3D2314; border-top: 3px solid #D4AF37; border-radius: 6px; padding: 8px 6px; text-align: center;">
                    <span style="font-size: 0.78rem; color: #CCCCCC; font-weight: 700;">📦 Cadastros</span><br>
                    <span style="font-size: 1.05rem; font-weight: 800; color: #FFFFFF;">{total_cadastros} itens</span><br>
                    <span style="font-size: 0.75rem; color: #51CF66; font-weight: 700;">↑ {total_pecas} peças</span>
                </div>
                ''', unsafe_allow_html=True)

            with k2:
                st.markdown(f'''
                <div style="background: #1E1E1E; border: 1px solid #3D2314; border-top: 3px solid #FF6B6B; border-radius: 6px; padding: 8px 6px; text-align: center;">
                    <span style="font-size: 0.78rem; color: #CCCCCC; font-weight: 700;">💵 Capital Custo</span><br>
                    <span style="font-size: 1.00rem; font-weight: 800; color: #FF6B6B;">{fmt_real(total_custo)}</span><br>
                    <span style="font-size: 0.72rem; color: #888888;">Custo Total</span>
                </div>
                ''', unsafe_allow_html=True)

            with k3:
                st.markdown(f'''
                <div style="background: #1E1E1E; border: 1px solid #3D2314; border-top: 3px solid #4DABF7; border-radius: 6px; padding: 8px 6px; text-align: center;">
                    <span style="font-size: 0.78rem; color: #CCCCCC; font-weight: 700;">🏷️ Capital Venda</span><br>
                    <span style="font-size: 1.00rem; font-weight: 800; color: #4DABF7;">{fmt_real(total_venda)}</span><br>
                    <span style="font-size: 0.72rem; color: #888888;">Venda Total</span>
                </div>
                ''', unsafe_allow_html=True)

            with k4:
                st.markdown(f'''
                <div style="background: #1E1E1E; border: 1px solid #3D2314; border-top: 3px solid #51CF66; border-radius: 6px; padding: 8px 6px; text-align: center;">
                    <span style="font-size: 0.78rem; color: #CCCCCC; font-weight: 700;">📈 Lucro Bruto</span><br>
                    <span style="font-size: 1.00rem; font-weight: 800; color: #51CF66;">{fmt_real(total_lucro)}</span><br>
                    <span style="font-size: 0.72rem; color: #888888;">Retorno Estimado</span>
                </div>
                ''', unsafe_allow_html=True)

            with k5:
                st.markdown(f'''
                <div style="background: #1E1E1E; border: 1px solid #3D2314; border-top: 3px solid #FCC419; border-radius: 6px; padding: 8px 6px; text-align: center;">
                    <span style="font-size: 0.78rem; color: #CCCCCC; font-weight: 700;">🎯 Margem Média</span><br>
                    <span style="font-size: 1.05rem; font-weight: 800; color: #FCC419;">{margem_global:.1f}%</span><br>
                    <span style="font-size: 0.72rem; color: #888888;">Margem Bruta</span>
                </div>
                ''', unsafe_allow_html=True)

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🏆 TOP 10 Produtos em Estoque")
                df_top = df_dash.copy()
                df_top['Item_Nome'] = df_top['Marca'] + " " + df_top['Produto'] + " " + df_top['Tamanho'].apply(lambda x: f"({x})" if x else "")
                df_top_grouped = df_top.groupby('Item_Nome', as_index=False)['Quantidade'].sum().sort_values(by='Quantidade', ascending=False).head(10)

                if not df_top_grouped.empty:
                    st.bar_chart(df_top_grouped.set_index('Item_Nome')['Quantidade'])
                    st.dataframe(df_top_grouped.rename(columns={'Item_Nome': 'Produto', 'Quantidade': 'Qtd Numérica'}), use_container_width=True, hide_index=True)

            with col2:
                st.markdown("#### 📊 Margem de Lucro Média por Categoria")
                df_cat_m = df_dash.copy()
                df_cat_grp = df_cat_m.groupby('Categoria', as_index=False).agg({
                    'Custo (R$)': 'sum',
                    'Preço Venda (R$)': 'sum',
                    'Quantidade': 'sum'
                })
                df_cat_grp['Margem (%)'] = ((df_cat_grp['Preço Venda (R$)'] - df_cat_grp['Custo (R$)']) / df_cat_grp['Preço Venda (R$)'] * 100).fillna(0)

                st.bar_chart(df_cat_grp.set_index('Categoria')['Margem (%)'])
                st.dataframe(df_cat_grp, use_container_width=True, hide_index=True)

# ==============================================================================
# PÁGINA 4: CADASTRAR PRODUTO
# ==============================================================================
elif pagina == "➕ Cadastrar Produto":
    st.title("➕ Cadastrar Novo Produto no Estoque")

    with st.form("form_cadastrar_produto"):
        c1, c2, c3 = st.columns(3)
        categoria = c1.selectbox("Categoria:", ["Perfumes", "Papetes", "Bonés", "Tênis", "Roupas Dry Fit", "Acessórios", "Outros"])
        marca = c2.text_input("Marca:")
        produto = c3.text_input("Nome do Produto / Modelo:")

        c4, c5, c6 = st.columns(3)
        tamanho = c4.text_input("Tamanho / Variação (ex: Uni, 41/42, M):")
        quantidade = c5.number_input("Quantidade Inicial:", min_value=1, value=1, step=1)
        fornecedor = c6.text_input("Fornecedor:")

        c7, c8 = st.columns(2)
        custo = c7.number_input("Preço de Custo (R$):", min_value=0.0, value=0.0, step=5.0)
        venda = c8.number_input("Preço de Venda (R$):", min_value=0.0, value=0.0, step=5.0)

        lucro_previsto = venda - custo
        margem_prevista = (lucro_previsto / venda * 100) if venda > 0 else 0.0

        st.info(f"💡 **Retorno Previsto:** Lucro de {fmt_real(lucro_previsto)} por unidade ({margem_prevista:.1f}% de margem).")

        btn_cadastrar = st.form_submit_button("✅ Cadastrar Produto", type="primary", use_container_width=True)

        if btn_cadastrar:
            if not produto.strip():
                st.error("O nome do produto é obrigatório.")
            else:
                novo_prod = pd.DataFrame([{
                    'Categoria': categoria.strip(),
                    'Quantidade': int(quantidade),
                    'Tamanho': tamanho.strip(),
                    'Marca': marca.strip() if marca.strip() else "Pulse",
                    'Produto': produto.strip(),
                    'Custo (R$)': float(custo),
                    'Preço Venda (R$)': float(venda),
                    'Lucro (R$)': float(lucro_previsto),
                    'Fornecedor': fornecedor.strip()
                }])
                df_estoque_up = pd.concat([df_estoque, novo_prod], ignore_index=True)
                salvar_dados(df_estoque_up, "estoque")
                st.success(f"🎉 Produto **{produto}** cadastrado e sincronizado com sucesso!")
                st.rerun()

# ==============================================================================
# PÁGINA 5: TABELA DE ESTOQUE (EXCEL)
# ==============================================================================
elif pagina == "📦 Tabela de Estoque (Excel)":
    st.title("📦 Tabela Geral de Estoque")

    if df_estoque.empty:
        st.info("Nenhum produto em estoque.")
    else:
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)
        csv_data = df_estoque.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Tabela em CSV/Excel", data=csv_data, file_name="estoque_pulse.csv", mime="text/csv")

# ==============================================================================
# PÁGINA 6: CONTABILIDADE & CAIXA
# ==============================================================================
elif pagina == "💰 Contabilidade & Caixa":
    st.title("💰 Fluxo de Caixa e Contabilidade")

    entradas = df_caixa[df_caixa['Tipo'] == 'Entrada']['Valor (R$)'].sum() if not df_caixa.empty else 0.0
    saidas = df_caixa[df_caixa['Tipo'] == 'Saída']['Valor (R$)'].sum() if not df_caixa.empty else 0.0
    saldo = entradas - saidas

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Entradas Totais", fmt_real(entradas))
    c2.metric("🔴 Saídas / Despesas", fmt_real(saidas))
    c3.metric("💵 Saldo Atual em Caixa", fmt_real(saldo))

    st.divider()

    st.markdown("#### 📝 Lançamento Manual no Caixa")
    with st.form("form_caixa_manual"):
        ca1, ca2, ca3 = st.columns(3)
        tipo_tr = ca1.selectbox("Tipo de Movimentação:", ["Entrada", "Saída"])
        cat_tr = ca2.text_input("Categoria (ex: Suprimento, Aluguel, Embalagem):")
        valor_tr = ca3.number_input("Valor (R$):", min_value=0.01, step=10.0)

        ca4, ca5 = st.columns(2)
        desc_tr = ca4.text_input("Descrição detalhada:")
        forma_tr = ca5.selectbox("Forma de Pagamento:", ["Pix", "Dinheiro", "Cartão", "Transferência"])

        btn_caixa = st.form_submit_button("✅ Registrar Transação", type="primary")

        if btn_caixa:
            nova_tr = pd.DataFrame([{
                'ID': int(datetime.now().timestamp()),
                'Data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'Tipo': tipo_tr,
                'Categoria': cat_tr.strip() if cat_tr.strip() else "Geral",
                'Descrição': desc_tr.strip(),
                'Valor (R$)': float(valor_tr),
                'Forma Pagamento': forma_tr
            }])
            df_caixa_up = pd.concat([df_caixa, nova_tr], ignore_index=True)
            salvar_dados(df_caixa_up, "caixa")
            st.success("Transação registrada com sucesso!")
            st.rerun()

    st.divider()
    st.markdown("#### 📋 Histórico de Transações")
    if not df_caixa.empty:
        st.dataframe(df_caixa, use_container_width=True, hide_index=True)

# ==============================================================================
# PÁGINA 7: ANTIDUPLICAÇÃO
# ==============================================================================
elif pagina == "🔍 Antiduplicação":
    st.title("🔍 Verificação de Antiduplicação de Produtos")

    if df_estoque.empty:
        st.info("Estoque vazio.")
    else:
        df_dups = df_estoque[df_estoque.duplicated(subset=['Marca', 'Produto', 'Tamanho'], keep=False)]
        if df_dups.empty:
            st.success("🎉 Nenhuma duplicata encontrada no estoque!")
        else:
            st.warning(f"Foram encontrados {len(df_dups)} registros duplicados no estoque.")
            st.dataframe(df_dups, use_container_width=True)

            if st.button("🧹 Mesclar e Limpar Duplicatas"):
                df_clean = df_estoque.groupby(['Categoria', 'Marca', 'Produto', 'Tamanho', 'Fornecedor'], as_index=False).agg({
                    'Quantidade': 'sum',
                    'Custo (R$)': 'mean',
                    'Preço Venda (R$)': 'mean',
                    'Lucro (R$)': 'mean'
                })
                salvar_dados(df_clean, "estoque")
                st.success("Duplicatas limpas e quantidades mescladas com sucesso!")
                st.rerun()

# ==============================================================================
# PÁGINA 8: IMPORTAR 'CAD ATT' (EXCEL)
# ==============================================================================
elif pagina == "📥 Importar 'Cad att' (Excel)":
    st.title("📥 Importar Planilha 'Cad att'")

    uploaded_file = st.file_uploader("Selecione o arquivo Excel ou CSV da loja:", type=['xlsx', 'xls', 'csv'])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_imp = pd.read_csv(uploaded_file)
            else:
                df_imp = pd.read_excel(uploaded_file)

            st.write("Preview do arquivo carregado:")
            st.dataframe(df_imp.head(10), use_container_width=True)

            if st.button("🚀 Confirmar e Substituir Estoque Atual", type="primary"):
                df_imp_prom = promover_cabecalho_se_necessario(df_imp)
                salvar_dados(df_imp_prom, "estoque")
                st.success("Planilha importada e sincronizada com sucesso no Google Drive e no sistema!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
