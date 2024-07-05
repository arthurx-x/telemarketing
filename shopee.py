import streamlit as st
import pandas as pd

def load_excel(file, skiprows=0):
    return pd.read_excel(file, skiprows=skiprows)

def process_order_all(df):
    columns = {
        'ID do pedido': 'ID Pedido',
        'Nome do Produto': 'Nome do Produto',
        'Número de referência SKU': 'Número de referência SKU',
        'Preço acordado': 'Preço acordado',
        'Quantidade': 'Quantidade'
    }
    df = df.rename(columns={old: new for old, new in columns.items() if old in df.columns})
    df['Total Pedido'] = df['Preço acordado'] * df['Quantidade']
    return df[columns.values()]

def process_shopeepay(df):
    columns = {
        'ID do pedido': 'ID Pedido',
        'Valor': 'Valor Recebido'
    }
    return df.rename(columns=columns)[columns.values()]

def merge_data(order_df, shopeepay_df, precos_df):
    merged = pd.merge(order_df, shopeepay_df, on='ID Pedido', how='left')
    merged = pd.merge(merged, precos_df, left_on='Número de referência SKU', right_on='SKU_Produto', how='left')
    
    column_order = ['ID Pedido', 'Nome do Produto', 'Número de referência SKU', 'SKU_Produto', 
                    'Preço acordado', 'Quantidade', 'Total Pedido', 'Valor Recebido', 
                    'Custo_Produto', 'Embalagem']
    
    return merged[[col for col in column_order if col in merged.columns]]

def calculate_additional_columns(df):
    df['Custo_Total'] = ((df['Preço acordado'] * df['Quantidade']) - df['Valor Recebido']) + df['Custo_Produto'] + df['Embalagem']
    df['Custo %'] = (100 / (df['Preço acordado'] * df['Quantidade'])) * df['Custo_Total']
    df['Lucro'] = df['Valor Recebido'] - df['Custo_Produto'] - df['Embalagem']
    df['Lucro %'] = (100 / (df['Preço acordado'] * df['Quantidade'])) * df['Lucro']
    return df

def main():
    st.title("Processador de Arquivos Excel com Dados Mesclados e Cálculos Adicionais")

    files = {
        'Order.all': st.file_uploader("Upload arquivo Order.all", type="xlsx", key="order"),
        'ShopeePay': st.file_uploader("Upload arquivo ShopeePay", type="xlsx", key="shopeepay"),
        'Preços': st.file_uploader("Upload arquivo Preços", type="xlsx", key="precos")
    }

    if all(files.values()):
        try:
            order_df = process_order_all(load_excel(files['Order.all']))
            shopeepay_df = process_shopeepay(load_excel(files['ShopeePay'], skiprows=17))
            precos_df = load_excel(files['Preços'])

            merged_df = merge_data(order_df, shopeepay_df, precos_df)
            calculated_df = calculate_additional_columns(merged_df.copy())

            st.subheader("Dados Mesclados e Calculados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Tabela Original")
                st.dataframe(merged_df)

            with col2:
                st.write("Tabela com Cálculos Adicionais")
                st.dataframe(calculated_df[['ID Pedido', 'Custo_Total', 'Custo %', 'Lucro', 'Lucro %']])

            # Calculando e exibindo a soma do Custo Total e do Lucro
            soma_custo_total = calculated_df['Custo_Total'].sum()
            soma_lucro = calculated_df['Lucro'].sum()

            st.subheader("Resumo Financeiro")
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Soma do Custo Total", f"R$ {soma_custo_total:.2f}")
            with col4:
                st.metric("Soma do Lucro", f"R$ {soma_lucro:.2f}")

            csv = calculated_df.to_csv(index=False)
            st.download_button(
                label="Baixar dados completos como CSV",
                data=csv,
                file_name="merged_and_calculated_data.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Erro ao processar os arquivos: {str(e)}")
    else:
        st.info("Por favor, faça o upload de todos os três arquivos para continuar.")

if __name__ == "__main__":
    main()
