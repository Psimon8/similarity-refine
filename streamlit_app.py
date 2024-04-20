import streamlit as st
import pandas as pd
import re
import altair as alt  # Import Altair for advanced plotting

def parse_filter_format_keywords(list_str, threshold):
    if not isinstance(list_str, str):
        return [], 0, 0, 0  # Return empty values if not a string
    
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

    avg_similarity = total_similarity / count if count > 0 else 0
    return filtered_keywords, total_volume, avg_similarity, count

def main():
    st.title('Similarity Refine')

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        total_rows_of_imported_file = len(df)  # Store the total number of rows in the imported file
        threshold = st.slider('Enter the similarity threshold (%)', min_value=0, max_value=100, value=40, step=10)
        df[['Filtered Keywords', 'Total Volume', 'Avg Similarity', 'Keyword Count']] = df.apply(
            lambda x: parse_filter_format_keywords(x['Liste MC et %'], threshold), axis=1, result_type='expand')

        df_sorted = df.sort_values(by='Vol. mensuel', ascending=False)
        rows_to_remove = []
        unique_secondary_keywords = set()

        for index, row in df_sorted.iterrows():
            for keyword in row['Filtered Keywords']:
                keyword_text = keyword.split(' (')[0]
                unique_secondary_keywords.add(keyword_text)

            primary_keyword_text = row['Mot-clé'].split(' (')[0]
            if primary_keyword_text in unique_secondary_keywords:
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

        total_rows = len(df_final)
        total_secondary_keywords = df_final['Nombre Mots clés Secondaire'].sum()

        # Data for the bar chart
        data = pd.DataFrame({
            'Metrics': ['Total Primary Keywords', 'Total Secondary Keywords'],
            'Values': [total_rows, total_secondary_keywords]
        })

        # Create an Altair bar chart
        chart = alt.Chart(data).mark_bar().encode(
            x='Metrics',
            y=alt.Y('Values:Q', scale=alt.Scale(domain=[0, total_rows_of_imported_file]))
        ).properties(
            width=400,
            height=300
        )

        st.altair_chart(chart, use_container_width=True)

        st.dataframe(df_final)

        if st.button('Download Data'):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df_final.to_excel(output_file_name, index=False)
            with open(output_file_name, "rb") as file:
                st.download_button(label="Download Excel", data=file, file_name=output_file_name, mime="application/vnd.ms-excel")

if __name__ == "__main__":
    main()
