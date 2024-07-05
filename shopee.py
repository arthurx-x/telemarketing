import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any

@st.cache_data
def load_excel(file: Any, skiprows: int = 0) -> pd.DataFrame:
    return pd.read_excel(file, skiprows=skiprows)

def process_dataframes(order_df: pd.DataFrame, shopeepay_df: pd.DataFrame, precos_df: pd.DataFrame) -> pd.DataFrame:
    # Renomear colunas
    column_mapping = {
        'ID do pedido': 'ID Pedido',
        'Nome do Produto': 'Nome do Produto',
        'Número de referência SKU': 'SKU',
        'Preço acordado': 'Preço Acordado',
        'Quantidade': 'Quantidade',
        'Valor': 'Valor Recebido'
    }
    order_df = order_df.rename(columns=column_mapping)
    shopeepay_df = shopeepay_df.rename(columns=column_mapping)

    # Mesclar dataframes
    df = pd.merge(order_df, shopeepay_df[['ID Pedido', 'Valor Recebido']], on='ID Pedido', how='left')
    df = pd.merge(df, precos_df, left_on='SKU', right_on='SKU_Produto', how='left')

    # Calcular colunas adicionais
    df['Total Pedido'] = df['Preço Acordado'] * df['Quantidade']
    df['Custo Total'] = df['Custo_Produto'] + df['Embalagem']
    df['Lucro'] = df['Valor Recebido'] - df['Custo Total']
    df['Margem (%)'] = (df['Lucro'] / df['Valor Recebido']) * 100

    return df

def create_summary(df: pd.DataFrame) -> Dict[str, float]:
    return {
        'Total Vendas': df['Valor Recebido'].sum(),
        'Custo Total': df['Custo Total'].sum(),
        'Lucro Total': df['Lucro'].sum(),
        'Margem Média (%)': df['Margem (%)'].mean()
    }

def plot_top_products(df: pd.DataFrame, metric: str, top_n: int = 10) -> px.bar:
    top_products = df.groupby('Nome do Produto')[metric].sum().nlargest(top_n).reset_index()
    fig = px.bar(top_products, x='Nome do Produto', y=metric, title=f'Top {top_n} Produtos por {metric}')
    return fig

def main():
    st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
    st.title("Dashboard de Análise de Vendas")

    files = {
        'Order.all': st.file_uploader("Upload arquivo Order.all", type="xlsx", key="order"),
        'ShopeePay': st.file_uploader("Upload arquivo ShopeePay", type="xlsx", key="shopeepay"),
        'Preços': st.file_uploader("Upload arquivo Preços", type="xlsx", key="precos")
    }

    if all(files.values()):
        try:
            order_df = load_excel(files['Order.all'])
            shopeepay_df = load_excel(files['ShopeePay'], skiprows=17)
            precos_df = load_excel(files['Preços'])

            df = process_dataframes(order_df, shopeepay_df, precos_df)

            st.subheader("Dados Processados")
            st.dataframe(df)

            summary = create_summary(df)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Vendas", f"R$ {summary['Total Vendas']:,.2f}")
            col2.metric("Custo Total", f"R$ {summary['Custo Total']:,.2f}")
            col3.metric("Lucro Total", f"R$ {summary['Lucro Total']:,.2f}")
            col4.metric("Margem Média", f"{summary['Margem Média (%)']:.2f}%")

            st.subheader("Análise de Produtos")
            metric = st.selectbox("Selecione a métrica", ['Valor Recebido', 'Quantidade', 'Lucro'])
            fig = plot_top_products(df, metric)
            st.plotly_chart(fig, use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label="Baixar dados como CSV",
                data=csv,
                file_name="dados_processados.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Erro ao processar os arquivos: {str(e)}")
    else:
        st.info("Por favor, faça o upload de todos os três arquivos para continuar.")

if __name__ == "__main__":
    main()