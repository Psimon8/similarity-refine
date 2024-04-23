import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Similarity Refine",
    page_icon="🥥"
)

def parse_filter_format_keywords(list_str, threshold):
    if not isinstance(list_str, str):
        return [], 0, 0, 0
    
    keywords_list = list_str.split(" | ")
    filtered_keywords = []
    total_volume = 0
    total_similarity = 0
    count = 0

    for keyword_str in keywords_list:
        match = re.match(r"(.+) \((\d+)\): (\d+\.\d+) %", keyword_str)
        if match:
            keyword, volume, similarity = match.groups()
            volume = int(volume)
            similarity = float(similarity)
            if similarity >= threshold:
                filtered_keywords.append(f"{keyword} ({volume}): {similarity} %")
                total_volume += volume
                total_similarity += similarity
                count += 1

    avg_similarity = total_similarity / count si count > 0 else 0
    return filtered_keywords, total_volume, avg_similarity, count

def main():
    st.title("Similarity Refine")

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        threshold = st.slider(
            'Enter the similarity threshold (%)', min_value=0, max_value=100, value=40, step=10
        )
        
        df[['Filtered Keywords', 'Total Volume', 'Avg Similarity', 'Keyword Count']] = df.apply(
            lambda x: parse_filter_format_keywords(x['Liste MC et %'], threshold), axis=1, result_type='expand'
        )

        df_sorted = df.sort_values(by='Vol. mensuel', ascending=False)
        rows_to_remove = []
        unique_secondary_keywords = set()

        # Correction de la faute de frappe : utilisation de `iterrows()`
        for index, row in df_sorted.iterrows():
            for keyword in row['Filtered Keywords']:
                unique_secondary_keywords.add(keyword.split(' (')[0])

            if row['Mot-clé'].split(' (')[0] in unique_secondary_keywords:
                rows_to_remove.append(index)

        df_filtered = df_sorted.drop(rows_to_remove)
        
        final_columns = {
            'Mot-clé': 'Nombre Mots clés Principal',
            'Vol. mensuel': 'Volume du mots clé principal',
            'Total Volume': 'Volume cumulé des mots clés secondaire',
            'Avg Similarity': '% moyen des degre de similarité des mots clés secondaire',
            'Keyword Count': 'Nombre Mots clés Secondaire'
        }
        df_final = df_filtered.rename(columns=final_columns)

        # Déplacer "Liste MC et %" à la fin
        column_order = [col for col in df_final.columns if col != 'Liste MC et %']
        column_order.append('Liste MC et %')
        df_final = df_final[column_order]

        total_primary_keywords = len(df_final)
        total_secondary_keywords = df_final['Nombre Mots clés Secondaire'].sum()
        total_primary_volume = df_final['Volume du mots clé principal'].sum()
        total_secondary_volume = df_final['Volume cumulé des mots clés secondaire'].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Primary Keywords", total_primary_keywords)
            st.metric("Total Secondary Keywords", total_secondary_keywords)
            st.metric("Total Primary Volume", total_primary_volume)
            st.metric("Total Cumulative Secondary Volume", total_secondary_volume)

        with col2:
            data = {
                'Metrics': ['Primary', 'Secondary'],
                'Values': [total_primary_keywords, total_secondary_keywords]
            }
            st.bar_chart(pd.DataFrame(data).set_index('Metrics'))

        with col3:
            data = {
                'Metrics': ['Primary', 'Secondary'],
                'Values': [total_primary_volume, total_secondary_volume]
            }
            st.bar_chart(pd.DataFrame(data).set_index('Metrics'))

        st.dataframe(df_final)

        if st.button("Download Data"):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df_final.to_excel(output_file_name, index=False)
            with open(output_file_name, "rb") as file, 
                st.download_button(
                    label="Download Excel",
                    data=file,
                    file_name=output_file_name,
                    mime="application/vnd.ms-excel",
                )

if __name__ == "__main__":
    main()
