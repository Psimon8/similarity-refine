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
    st.title('Keyword Analysis Tool')

    # File uploader
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        # Input for threshold
        threshold = st.number_input('Enter the similarity threshold (%)', min_value=0.0, value=40.0, step=0.1)
        
        # Process the file
        df[['Filtered Keywords', 'Total Volume', 'Avg Similarity', 'Keyword Count']] = df.apply(
            lambda x: parse_filter_format_keywords(x['Liste MC et %'], threshold), axis=1, result_type='expand')

        # Display DataFrame in Streamlit
        st.dataframe(df)

        # Button to download the processed data
        if st.button('Download Data'):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df.to_excel(output_file_name, index=False)
            with open(output_file_name, "rb") as file:
                btn = st.download_button(
                    label="Download Excel",
                    data=file,
                    file_name=output_file_name,
                    mime="application/vnd.ms-excel"
                )

if __name__ == "__main__":
    main()
