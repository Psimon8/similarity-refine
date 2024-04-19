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

    # Ensure output is consistent even if no keywords match
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

        # Input for threshold
        threshold = st.number_input('Enter the similarity threshold (%)', min_value=0.0, value=40.0, step=0.1)
        
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
            # Adding secondary keywords to the set
            for keyword in row['Filtered Keywords']:
                keyword_text = keyword.split(' (')[0]  # Extracting only the textual part
                unique_secondary_keywords.add(keyword_text)

            # Checking if the primary keyword is in the set of secondary keywords
            primary_keyword_text = row['Mot-clé'].split(' (')[0]
            if primary_keyword_text in unique_secondary_keywords:
                rows_to_remove.append(index)

        # Removing identified rows
        df_filtered = df_sorted.drop(rows_to_remove)

        # Assuming final_columns are defined as required
        final_columns = {
            'Mot-clé': 'Mots clé principal',
            'Vol. mensuel': 'Volume du mots clé principal',
            'Total Volume': 'Volume cumulé des mots clés secondaire',
            'Avg Similarity': '% moyen des degre de similarité des mots clés secondaire',
            'Keyword Count': 'Nombre de mots clés secondaire'
        }
        df_final = df_filtered.rename(columns=final_columns)

        # Extraction des mots-clés formatés dans des colonnes séparées
        for i in range(1, df_final['Nombre de mots clés secondaire'].max() + 1):
            df_final[f'Colonne F{i}'] = df_final['Filtered Keywords'].apply(lambda x: x[i-1] if len(x) >= i else None)

        # Suppression de la colonne 'Filtered Keywords'
        df_final.drop('Filtered Keywords', axis=1, inplace=True)

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
