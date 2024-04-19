import streamlit as st
import openpyxl
import pandas as pd
import re

def parse_filter_format_keywords(list_str, threshold):
    if not isinstance(list_str, str):
        # Return empty values for each expected output column if input is not a string
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

    if count == 0:
        return [], 0, 0, 0

    avg_similarity = total_similarity / count if count > 0 else 0
    return filtered_keywords, total_volume, avg_similarity, count

def main():
    st.title('Similarity Refine')

    # File uploader
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        # Slider for threshold
        threshold = st.slider('Enter the similarity threshold (%)', min_value=10, max_value=100, value=40, step=10)

        # Process the file
        df[['Filtered Keywords', 'Total Volume', 'Avg Similarity', 'Keyword Count']] = df.apply(
            lambda x: parse_filter_format_keywords(x['Liste MC et %'], threshold), axis=1, result_type='expand')

        # Sorting the DataFrame by monthly volume in descending order
        df_sorted = df.sort_values(by='Vol. mensuel', ascending=False)

        # Creating a list to store indices of rows to remove
        rows_to_remove = []

        # Creating a set to store unique secondary keywords
        unique_secondary_keywords = set()

        # Iterating over the DataFrame to identify rows to remove
        for index, row in df_sorted.iterrows():
            for keyword in row['Filtered Keywords']:
                keyword_text = keyword.split(' (')[0]
                unique_secondary_keywords.add(keyword_text)

            primary_keyword_text = row['Mot-clé'].split(' (')[0]
            if primary_keyword_text in unique_secondary_keywords:
                rows_to_remove.append(index)

        # Removing identified rows
        df_filtered = df_sorted.drop(rows_to_remove)

        final_columns = {
            'Mot-clé': 'Mots clé principal',
            'Vol. mensuel': 'Volume du mots clé principal',
            'Total Volume': 'Volume cumulé des mots clés secondaire',
            'Avg Similarity': '% moyen des degre de similarité des mots clés secondaire',
            'Keyword Count': 'Nombre de mots clés secondaire'
        }
        df_final = df_filtered.rename(columns=final_columns)

        # Display bar chart for row count and keyword count sum
        data = {
            'Row Count': [len(df_final)],
            'Total Keywords': [df_final['Nombre de mots clés secondaire'].sum()]
        }
        st.bar_chart(data)
        
        # Display DataFrame in Streamlit
        st.dataframe(df_final)

        # Button to download the processed data
        if st.button('Download Data'):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df_final.to_excel(output_file_name, index=False)
            with open(output_file_name, "rb") as file:
                st.download_button(
                    label="Download Excel",
                    data=file,
                    file_name=output_file_name,
                    mime="application/vnd.ms-excel"
                )

if __name__ == "__main__":
    main()
