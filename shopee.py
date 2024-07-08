import streamlit as st
import pandas as pd
from typing import Dict, Any

# Constants
COLUMN_MAPPING = {
    'order': {
        'ID do pedido': 'ID PEDIDO',
        'Data de criação do pedido': 'DATA VENDA',
        'Número de referência SKU': 'PRODUTO',
        'Quantidade': 'QUANTIDADE',
        'Preço acordado': 'PRECO'
    },
    'shopeepay': {
        'ID do pedido': 'ID PEDIDO',
        'Valor': 'VALOR RECEBIDO'
    }
}

FINAL_COLUMNS = ['DATA VENDA', 'ID PEDIDO', 'PRODUTO', 'QUANTIDADE', 'VALOR DA VENDA', 'VALOR DO PRODUTO', 'INSUMOS', 'VALOR RECEBIDO', 'SALDO']

def load_and_process_data(files: Dict[str, Any]) -> pd.DataFrame:
    try:
        dfs = {
            'order': pd.read_excel(files['order']),
            'shopeepay': pd.read_excel(files['shopeepay'], skiprows=17),
            'precos': pd.read_excel(files['precos'])
        }

        # Process order DataFrame
        order_df = dfs['order'].rename(columns=COLUMN_MAPPING['order'])
        order_df['VALOR DA VENDA'] = order_df['PRECO'] * order_df['QUANTIDADE']
        order_df['DATA VENDA'] = pd.to_datetime(order_df['DATA VENDA']).dt.date

        # Process shopeepay DataFrame
        shopeepay_df = dfs['shopeepay'].rename(columns=COLUMN_MAPPING['shopeepay'])

        # Merge DataFrames
        merged_df = pd.merge(order_df, shopeepay_df, on='ID PEDIDO', how='left')
        merged_df = pd.merge(merged_df, dfs['precos'], left_on='PRODUTO', right_on='SKU_Produto', how='left')

        # Calculate SALDO and finalize DataFrame
        merged_df['SALDO'] = merged_df['VALOR RECEBIDO'] - ((merged_df['Custo_Produto'] * merged_df['QUANTIDADE']) + merged_df['Embalagem'])
        merged_df = merged_df.rename(columns={'Custo_Produto': 'VALOR DO PRODUTO', 'Embalagem': 'INSUMOS'})
        
        return merged_df[FINAL_COLUMNS].dropna(subset=['VALOR RECEBIDO'])
    except KeyError as e:
        raise ValueError(f"Coluna esperada não encontrada: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro ao processar os dados: {e}")

def calculate_summary(df: pd.DataFrame) -> tuple:
    daily_summary = df.groupby('DATA VENDA').agg({
        'VALOR DA VENDA': 'sum',
        'SALDO': 'sum'
    }).reset_index().rename(columns={
        'DATA VENDA': 'Data',
        'VALOR DA VENDA': 'Total Vendas',
        'SALDO': 'Total Saldo'
    })
    
    return daily_summary, df['VALOR DA VENDA'].sum(), df['SALDO'].sum()

def main():
    st.set_page_config(layout="wide", page_title="Processador de Arquivos Excel")
    
    st.markdown("""
        <style>
        .main > div { padding-top: 2rem; }
        .stApp { max-width: 100%; }
        .block-container { padding: 1rem 1.5rem 0; }
        .card { border-radius: 5px; padding: 20px; margin-bottom: 20px; height: 100%; }
        .sales { background-color: #e6f3ff; color: #0066cc; }
        .profit { background-color: #e6fff0; color: #006633; }
        .loss { background-color: #ffe6e6; color: #cc0000; }
        .big-font { font-size: 36px !important; font-weight: bold; }
        .st-emotion-cache-1v0mbdj > img { display: none; }
        .stDataFrame { width: 100%; height: calc(50vh - 200px); }
        [data-testid="stHorizontalBlock"] { align-items: stretch; }
        .upload-boxes { display: flex; gap: 10px; }
        .upload-boxes > div { flex: 1; }
        .dataframe-container table { width: 100% !important; }
        .dataframe-container th:first-child, .dataframe-container td:first-child { display: none; }
        </style>
    """, unsafe_allow_html=True)

    st.title("Concilia Shopee")

    col1, col2, col3 = st.columns(3)
    files = {
        'order': col1.file_uploader("Upload arquivo Order.all", type="xlsx", key="order"),
        'shopeepay': col2.file_uploader("Upload arquivo ShopeePay", type="xlsx", key="shopeepay"),
        'precos': col3.file_uploader("Upload arquivo Preços", type="xlsx", key="precos")
    }

    if all(files.values()):
        try:
            merged_df = load_and_process_data(files)
            daily_summary, total_sales, total_profit = calculate_summary(merged_df)

            st.header("Resumo Mensal")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.dataframe(daily_summary, use_container_width=True, hide_index=True)
            with col2:
                profit_class = "profit" if total_profit >= 0 else "loss"
                st.markdown(f"""
                    <div class="card sales">
                        <h3>Total Vendas</h3>
                        <p class="big-font">R$ {total_sales:,.2f}</p>
                    </div>
                    <div class="card {profit_class}">
                        <h3>Total Saldo</h3>
                        <p class="big-font">R$ {total_profit:,.2f}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.header("Dados Mesclados")
            st.dataframe(merged_df, use_container_width=True, hide_index=True)

        except (ValueError, RuntimeError) as e:
            st.error(str(e))
    else:
        st.info("Por favor, faça o upload de todos os três arquivos para continuar.")

if __name__ == "__main__":
    main()
