import streamlit as st
import pandas as pd

COLUMN_MAPPINGS = {
    "order.all": {'ID do pedido': 'ID do pedido_0', 'Data de criação': 'Data de criação do pedido', 
                'Nome do produto': 'Nome do Produto', 'Número de referência': 'Número de referência SKU', 
                'Preço acordado': 'Preço acordado', 'Quantidade': 'Quantidade'},
    "shopeepay": {'ID do pedido': 'ID do pedido_61', 'Valor': 'Valor'},
    "preços": {'Custo do Produto': 'Custo_Produto'}
}

FINAL_COLUMNS = {
    'ID do pedido_0': 'ID do pedido',
    'Data de criação do pedido': 'Data de criação do pedido',
    'Nome do Produto': 'Nome do Produto',
    'Número de referência SKU': 'Número de referência SKU',
    'Preço acordado': 'Preço',
    'Quantidade': 'Quantidade',
    'TOTAL VENDA': 'Valor Total',
    'Custo_Produto': 'CUSTO',
    'CUSTO TOTAL': 'CUSTO TOTAL',
    'Valor': 'RECEBIDO',
    'LIQUIDO': 'LIQUIDO'
}

def read_file(file, skip_rows=None):
    return pd.read_csv(file, skiprows=skip_rows) if file.name.endswith('.csv') else pd.read_excel(file, skiprows=skip_rows)

def create_result_card(value):
    style = 'positive' if value > 0 else 'negative' if value < 0 else 'zero'
    colors = {
        'positive': ("rgba(220, 252, 231, 0.7)", "rgb(22, 163, 74)", "rgba(34, 197, 94, 0.3)"),
        'negative': ("rgba(254, 226, 226, 0.7)", "rgb(220, 38, 38)", "rgba(248, 113, 113, 0.3)"),
        'zero': ("rgba(241, 245, 249, 0.7)", "rgb(71, 85, 105)", "rgba(148, 163, 184, 0.3)")
    }
    bg, text, border = colors[style]
    value_str = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"""
        <div style="padding:1.5rem;border-radius:1rem;background-color:{bg};margin:1.5rem 0;text-align:center;
                    box-shadow:0 4px 6px -1px {border},0 2px 4px -1px rgba(0,0,0,0.06);border:1px solid {border}">
            <h3 style="margin:0;color:{text};font-size:1.2rem;font-weight:600;letter-spacing:0.025em;text-transform:uppercase">RESULTADO</h3>
            <p style="margin:0.75rem 0 0 0;color:{text};font-size:2rem;font-weight:700;letter-spacing:-0.025em">{value_str}</p>
        </div>"""

def main():
    st.set_page_config(page_title="Concilia Shopee", layout="wide")
    st.title("Concilia Shopee")
    
    files = st.file_uploader("Adicione Order.all, ShopeePay, e Preços", accept_multiple_files=True)
    if not files:
        st.info("Adicione os 3 arquivos")
        return

    try:
        dfs = {}
        for file in files:
            for key in COLUMN_MAPPINGS:
                if key.lower() in file.name.lower():
                    skip_rows = 17 if "shopeepay" in key.lower() else None
                    df = read_file(file, skip_rows)
                    dfs[key] = df.rename(columns=COLUMN_MAPPINGS[key])

        if len(dfs) != 3:
            st.warning("Faltam arquivos")
            return

        merged_df = (pd.merge(dfs["order.all"], dfs["shopeepay"], 
                            left_on='ID do pedido_0', right_on='ID do pedido_61')
                    .merge(dfs["preços"], left_on='Número de referência SKU', 
                        right_on='SKU', how='left'))

        merged_df['Data de criação do pedido'] = pd.to_datetime(merged_df['Data de criação do pedido']).dt.date
        merged_df['TOTAL VENDA'] = merged_df['Preço acordado'] * merged_df['Quantidade']
        merged_df['CUSTO TOTAL'] = (merged_df['Custo_Produto'] * merged_df['Quantidade']) + 1
        merged_df['LIQUIDO'] = merged_df['Valor'] - merged_df['CUSTO TOTAL']

        result_df = merged_df[FINAL_COLUMNS.keys()].rename(columns=FINAL_COLUMNS)
        
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        st.markdown(create_result_card(result_df['LIQUIDO'].sum()), unsafe_allow_html=True)
        st.download_button("Baixar resultados", result_df.to_csv(index=False), 
                        "dados_concilia_shopee.csv", "text/csv")

    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
