import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Similarity Refine",
    page_icon="🥥"
)

# Fonction pour filtrer et formater les mots-clés
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
    st.title('Similarity Refine')

    uploaded_file = st.file_uploader("Choisissez un fichier")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        threshold = st.slider('Entrez le seuil de similarité (%)', min_value=0, max_value=100, valeur=40, pas=10)

        df[['Filtered Keywords', 'Total Volume', 'Avg Similarity', 'Keyword Count']] = df.apply(
            lambda x: parse_filter_format_keywords(x['Liste MC et %'], threshold), axis=1, result_type='expand'
        )

        df_sorted = df.sort_values(by='Vol. mensuel', ascending=False)
        rows_to_remove = []
        unique_secondary_keywords = set()

        # Supprimer les lignes où les mots-clés primaires se dupliquent
        pour index, row in df_sorted.iterrows():
            primary_keyword_text = row['Mot-clé'].split(' (')[0]
            if primary_keyword_text in unique_secondary_keywords:
                rows_to_remove.append(index)
            else:
                pour keyword in row['Filtered Keywords']:
                    keyword_text = keyword.split(' (')[0]
                    unique_secondary_keywords.add(keyword_text)

        df_filtered = df_sorted.drop(rows_to_remove)

        # Ajouter une colonne pour les mots-clés secondaires concaténés
        df_filtered['Secondary Keywords Concatenated'] = df_filtered['Filtered Keywords'].apply(
            lambda x: " | ".join(x) if isinstance(x, list) else ""
        )

        # Renommer les colonnes existantes
        final_columns = {
            'Mot-clé': 'Nombre Mots clés Principal',
            'Vol. mensuel': 'Volume du mots clé principal',
            'Total Volume': 'Volume cumulé des mots clés secondaire',
            'Avg Similarity': '% moyen des degrés de similarité des mots clés secondaire',
            'Keyword Count': 'Nombre Mots clés Secondaire'
        }
        df_final = df_filtered.rename(columns=final_columns)

        # Insérer la colonne pour les mots-clés secondaires concaténés
        volume_col_index = df_final.columns.get_loc('Volume du mots clé principal')
        df_final.insert(volume_col_index + 1, 'Mots clés secondaires concaténés', df_filtered['Secondary Keywords Concatenated'])

        # Déplacer "Liste MC et %" après "Nombre Mots clés Secondaire"
        if 'Liste MC et %' not in df_final.columns:
            keyword_count_index = df_final.columns.get_loc('Nombre Mots clés Secondaire')
            df_final.insert(keyword_count_index + 1, 'Liste MC et %', df['Liste MC et %'])

        # Ajouter des métriques et des visualisations
        total_primary_keywords = len(df_final)
        total_secondary_keywords = df_final['Nombre Mots clés Secondaire'].sum()
        total_primary_volume = df_final['Volume du mots clé principal'].sum()
        total_secondary_volume = df_final['Volume cumulé des mots clés secondaire'].sum()

        # Afficher les métriques et les graphiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Total Primary Keywords", value=total_primary_keywords)
            st.metric(label="Total Secondary Keywords", value=total_secondary_keywords)
            st.metric(label="Total Primary Volume", value=total_primary_volume)
            st.metric(label="Total Cumulative Secondary Volume", value=total_secondary_volume)

        with col2:
            st.text("Nombre de Mots Clés")
            data = {
                'Metrics': ['Primary', 'Secondary'],
                'Values': [total_primary_keywords, total_secondary_keywords]
            }
            st.bar_chart(pd.DataFrame(data).set_index('Metrics'))
                
        with col3:
            st.text("Volume de Recherche")
            data = {
                'Metrics': ['Primary', 'Secondary'],
                'Values': [total_primary_volume, total_secondary_volume]
            }
            st.bar_chart(pd.DataFrame(data).set_index('Metrics'))

        # Afficher le DataFrame final
        st.dataframe(df_final)

        # Bouton de téléchargement pour le fichier final
        if st.button('Télécharger les données'):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df_final.to_excel(output_file_name, index=False)
            
            with open(output_file_name, "rb") as file:
                st.download_button(
                    label="Télécharger Excel",
                    data=file,
                    file_name=output_file_name,
                    mime="application/vnd.ms-excel"
                )

if __name__ == "__main__":
    main()
