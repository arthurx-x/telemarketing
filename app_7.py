# Importando bibliotecas
import timeit
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import xlsxwriter

# Configurando o estilo do seaborn para gráficos mais agradáveis
sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})

# Função para carregar dados, permitindo arquivos CSV ou Excel
@st.cache_data(show_spinner=True)
def load_data(file_data: str, sep: str) -> pd.DataFrame:
    try:
        return pd.read_csv(filepath_or_buffer=file_data, sep=sep)
    except pd.errors.ParserError:
        return pd.read_excel(io=file_data)

# Função para filtrar dados com base em seleções multisseleção
@st.cache_data
def multiselect_filter(data: pd.DataFrame, col: str, selected: list[str]) -> pd.DataFrame:
    return data if "all" in selected else data[data[col].isin(selected)].reset_index(drop=True)

# Função para converter DataFrame para arquivo (CSV ou Excel)
@st.cache_data
def df_to_file(df: pd.DataFrame, file_format: str) -> bytes:
    output = BytesIO()
    if file_format == "csv":
        df.to_csv(index=False, path_or_buf=output)
    elif file_format == "excel":
        df.to_excel(excel_writer=pd.ExcelWriter(path=output, engine="xlsxwriter"), index=False, sheet_name="Sheet1")
    return output.getvalue()

# Função principal
def main():
    # Configuração da página do Streamlit
    st.set_page_config(page_title="Módulo 19", layout="wide", initial_sidebar_state="expanded")
    st.write("# Análise de Telemarketing 📊")
    st.markdown(body="---")

    # Barra lateral para upload de arquivo
    st.sidebar.markdown(body='<img src="https://raw.githubusercontent.com/rhatiro/Curso_EBAC-Profissao_Cientista_de_Dados/main/Mo%CC%81dulo_19_-_Streamlit_II/Exerci%CC%81cio_1/img/Bank-Branding.jpg" width=100%>', unsafe_allow_html=True)
    st.sidebar.write("## Suba o arquivo 📂")
    data_file_1 = st.sidebar.file_uploader(label="Dados de marketing bancário", type=["csv", "xlsx"])

    if data_file_1 is not None:
        start = timeit.default_timer()

        # Carregando dados e fazendo uma cópia
        bank_raw = load_data(file_data=data_file_1, sep=";")
        bank = bank_raw.copy()

        st.write("⏱️ Time:", timeit.default_timer() - start)

        st.write("## Antes dos filtros")
        st.write(bank_raw)
        st.write("Quantidade de linhas:", bank_raw.shape[0])
        st.write("Quantidade de colunas:", bank_raw.shape[1])

        # Formulário para seleção de gráfico, faixa etária e filtros multisseleção
        with st.sidebar.form(key="my_form"):
            graph_type = st.radio("Tipo de gráfico:", ("Barras 📊", "Pizza 🍕"))

            min_age, max_age = min(bank["age"]), max(bank["age"])
            idades = st.slider(label="Idade:", min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

            columns_to_multiselect = ["job", "marital", "default", "housing", "loan", "contact", "month", "day_of_week"]
            multiselect_options = {col: bank[col].unique().tolist() + ["all"] for col in columns_to_multiselect}

            selected_options = {col: st.multiselect(label=f"{col.capitalize()}:",
                                                    options=multiselect_options[col],
                                                    default=["all"]) for col in columns_to_multiselect}

            bank = (
                bank.query(f"age >= {idades[0]} and age <= {idades[1]}")
                .pipe(multiselect_filter, "job", selected_options["job"])
                .pipe(multiselect_filter, "marital", selected_options["marital"])
                .pipe(multiselect_filter, "default", selected_options["default"])
                .pipe(multiselect_filter, "housing", selected_options["housing"])
                .pipe(multiselect_filter, "loan", selected_options["loan"])
                .pipe(multiselect_filter, "contact", selected_options["contact"])
                .pipe(multiselect_filter, "month", selected_options["month"])
                .pipe(multiselect_filter, "day_of_week", selected_options["day_of_week"])
            )

            submit_button = st.form_submit_button(label="Aplicar ✅")

        st.write("## Após os filtros")
        st.write(bank)
        st.write("Quantidade de linhas:", bank.shape[0])
        st.write("Quantidade de colunas:", bank.shape[1])

        col1, col2 = st.columns(spec=2)

        # Botões de download para CSV e Excel
        csv = df_to_file(df=bank, file_format="csv")
        col1.write("### Download CSV")
        col1.download_button(label="📥 Baixar como arquivo .csv", data=csv, file_name="df_csv.csv", mime="text/csv")

        excel = df_to_file(df=bank, file_format="excel")
        col2.write("### Download Excel")
        col2.download_button(label="📥 Baixar como arquivo .xlsx", data=excel, file_name="df_excel.xlsx")

        st.markdown("---")

        # Análise da proporção de aceitação
        bank_raw_target_pct = bank_raw["y"].value_counts(normalize=True).to_frame() * 100
        bank_raw_target_pct = bank_raw_target_pct.sort_index()
        bank_target_pct = bank["y"].value_counts(normalize=True).to_frame() * 100
        bank_target_pct = bank_target_pct.sort_index()

        # Gráficos de barras ou pizza
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
        if graph_type == "Barras 📊":
            sns.barplot(x=bank_raw_target_pct.index, y="proportion", data=bank_raw_target_pct, ax=axes[0])
            axes[0].bar_label(container=axes[0].containers[0], fmt="%.2f%%")  # Adicionando formato de porcentagem
            axes[0].set_title(label="Dados brutos 📊", fontweight="bold")
            sns.barplot(x=bank_target_pct.index, y="proportion", data=bank_target_pct, ax=axes[1])
            axes[1].bar_label(container=axes[1].containers[0], fmt="%.2f%%")  # Adicionando formato de porcentagem
            axes[1].set_title(label="Dados filtrados 📊", fontweight="bold")
        else:
            bank_raw_target_pct.plot(kind="pie", autopct="%.2f%%", y="proportion", ax=axes[0])  # Adicionando formato de porcentagem
            axes[0].set_title("Dados brutos 🍕", fontweight="bold")
            bank_target_pct.plot(kind="pie", autopct="%.2f%%", y="proportion", ax=axes[1])  # Adicionando formato de porcentagem
            axes[1].set_title("Dados filtrados 🍕", fontweight="bold")
        st.write("## Proporção de aceite 📈")
        st.pyplot(plt)

if __name__ == "__main__":
    main()