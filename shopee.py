import streamlit as st
import pandas as pd
import plotly.express as px

def load_excel(file, skiprows=0):
    """Load an Excel file into a DataFrame."""
    return pd.read_excel(file, skiprows=skiprows)

def process_dataframe(df, columns, add_total=False):
    """Rename columns in the DataFrame and optionally add a 'Total do Pedido' column."""
    df = df.rename(columns={old: new for old, new in columns.items() if old in df.columns})
    if add_total and 'Preço acordado' in df.columns and 'Quantidade' in df.columns:
        df['Total do Pedido'] = df['Preço acordado'] * df['Quantidade']
    return df

def merge_dataframes(order_df, shopeepay_df, precos_df):
    """Merge the order, ShopeePay, and price DataFrames into a single DataFrame and calculate profit."""
    merged_df = pd.merge(order_df, shopeepay_df, on='ID Pedido', how='left')
    merged_df = pd.merge(merged_df, precos_df, left_on='Número de referência SKU', right_on='SKU_Produto', how='left')
    merged_df['Lucro'] = merged_df['Valor Recebido'] - merged_df['Custo_Produto'] - merged_df['Embalagem']
    return merged_df

def display_dataframe(df):
    """Display the DataFrame excluding the 'Número de referência SKU' column."""
    return df.drop(columns=['Número de referência SKU'], errors='ignore')

def main():
    st.title("Processador de Arquivos Excel com Dados Mesclados")

    files = {
        'Order.all': st.file_uploader("Upload arquivo Order.all", type="xlsx", key="order"),
        'ShopeePay': st.file_uploader("Upload arquivo ShopeePay", type="xlsx", key="shopeepay"),
        'Preços': st.file_uploader("Upload arquivo Preços", type="xlsx", key="precos")
    }

    if all(files.values()):
        try:
            order_df = process_dataframe(load_excel(files['Order.all']), {
                'ID do pedido': 'ID Pedido',
                'Data de criação do pedido': 'Data de criação do pedido',
                'Nome do Produto': 'Nome do Produto',
                'Número de referência SKU': 'Número de referência SKU',
                'Preço acordado': 'Preço acordado',
                'Quantidade': 'Quantidade'
            }, add_total=True)
            
            shopeepay_df = process_dataframe(load_excel(files['ShopeePay'], skiprows=17), {
                'ID do pedido': 'ID Pedido',
                'Valor': 'Valor Recebido'
            })
            
            precos_df = load_excel(files['Preços'])

            merged_df = merge_dataframes(order_df, shopeepay_df, precos_df)
            columns_to_display = ['ID Pedido', 'Data de criação do pedido', 'Nome do Produto', 'SKU_Produto', 
                                  'Preço acordado', 'Quantidade', 'Custo_Produto', 'Embalagem', 
                                  'Total do Pedido', 'Valor Recebido', 'Lucro']
            merged_df = merged_df[[col for col in columns_to_display if col in merged_df.columns]]

            st.subheader("Dados Mesclados de Todos os Arquivos")
            st.dataframe(display_dataframe(merged_df))

            csv = merged_df.to_csv(index=False)
            st.download_button(
                label="Baixar dados mesclados como CSV",
                data=csv,
                file_name="merged_data.csv",
                mime="text/csv",
            )

            st.subheader("Soma dos Valores")
            total_pedido_sum = merged_df['Total do Pedido'].sum()
            valor_recebido_sum = merged_df['Valor Recebido'].sum()
            lucro_sum = merged_df['Lucro'].sum()

            st.write(f"Soma do Total do Pedido: {total_pedido_sum:.2f}")
            st.write(f"Soma do Valor Recebido: {valor_recebido_sum:.2f}")
            st.write(f"Soma do Lucro: {lucro_sum:.2f}")

            # Adicionando gráficos
            st.subheader("Visualizações Gráficas")

            fig_total = px.bar(merged_df, x='ID Pedido', y='Total do Pedido', title='Total do Pedido por ID')
            st.plotly_chart(fig_total)

            fig_valor = px.bar(merged_df, x='ID Pedido', y='Valor Recebido', title='Valor Recebido por ID')
            st.plotly_chart(fig_valor)

            fig_lucro = px.bar(merged_df, x='ID Pedido', y='Lucro', title='Lucro por ID')
            st.plotly_chart(fig_lucro)

        except Exception as e:
            st.error(f"Erro ao processar os arquivos: {str(e)}")
    else:
        st.info("Por favor, faça o upload de todos os três arquivos para continuar.")

if __name__ == "__main__":
    main()
