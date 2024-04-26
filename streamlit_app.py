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
                filtered_keywords.append(f"{keyword} ({volume}): {similarity:.2f} %")
                total_volume += volume
                total_similarity += similarity
                count += 1

    avg_similarity = total_similarity / count if count > 0 else 0
    return filtered_keywords, total_volume, avg_similarity, count

def main():
    st.title("Similarity Refine")

    uploaded_file = st.file_uploader("Choisissez un fichier")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        threshold = st.slider(
            "Entrez le seuil de similarité (%)", min_value=0, max_value=100, value=40, step=10
        )

        df[["Filtered Keywords", "Total Volume", "Avg Similarity", "Keyword Count"]] = df.apply(
            lambda x: parse_filter_format_keywords(x["Liste MC et %"], threshold), axis=1, result_type="expand"
        )

        df_sorted = df.sort_values(by="Vol. mensuel", ascending=False)
        rows_to_remove = []
        unique_secondary_keywords = set()

        # Supprimer les lignes où les mots-clés primaires se dupliquent
        for index, row in df_sorted.iterrows():
            primary_keyword_text = row["Mot-clé"].split(" (")[0]
            if primary_keyword_text in unique_secondary_keywords:
                rows_to_remove.append(index)
            else:
                for keyword in row["Filtered Keywords"]:
                    keyword_text = keyword.split(" (")[0]
                    unique_secondary_keywords.add(keyword_text)


        df_filtered = df_sorted.drop(rows_to_remove)

        # Ajouter une colonne pour les mots-clés secondaires concaténés
        df_filtered["Secondary Keywords Concatenated"] = df_filtered["Filtered Keywords"].apply(
            lambda x: " | ".join(x) if isinstance(x, list) else ""
        )

        # Supprimer la colonne "Filtered Keywords"
        df_filtered = df_filtered.drop(columns=["Filtered Keywords"])

        # Réorganiser les colonnes pour intervertir "Secondary Keywords Concatenated" et "(List all Keywords & %)"
        new_column_order = [
            "Main Keyword",
            "SV Main Keyword",
            "Secondary Keywords",
            "SV Secondary Keyword Cumulated",
            "AVG % Similarity Secondary Keyword",
            "Numbers Secondary Keyword",
            "Secondary Keywords Concatenated",
            "(List all Keywords & %)"
        ]
        df_final = df_filtered.reindex(columns=new_column_order)

        # Ajouter des métriques et des graphiques
        total_primary_keywords = len(df_final)
        total_secondary_keywords = df_final["Numbers Secondary Keyword"].sum()
        total_primary_volume = df_final["SV Main Keyword"].sum()
        total_secondary_volume = df_final["SV Secondary Keyword Cumulated"].sum()

        # Afficher les métriques et des graphiques
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Primary Keywords", total_primary_keywords)
            st.metric("Total Secondary Keywords", total_secondary_keywords)
            st.metric("Total Primary Volume", total_primary_volume)
            st.metric("Total Cumulative Secondary Volume", total_secondary_volume)

        with col2:
            st.text("Nombre de Mots Clés")
            data = {
                "Metrics": ["Primary", "Secondary"],
                "Values": [total_primary_keywords, total_secondary_keywords],
            }
            st.bar_chart(pd.DataFrame(data).set_index("Metrics"))

        with col3:
            st.text("Volume de Recherche")
            data = {
                "Metrics": ["Primary", "Secondary"],
                "Values": [total_primary_volume, total_secondary_volume],
            }
            st.bar_chart(pd.DataFrame(data).set_index("Metrics"))

        # Afficher le DataFrame final
        st.dataframe(df_final)

        # Bouton de téléchargement pour le fichier final
        if st.button("Télécharger les données"):
            output_file_name = f"processed_data_threshold_{threshold}.xlsx"
            df_final.to_excel(output_file_name, index=False)

            with open(output_file_name, "rb") as file:
                st.download_button(
                    "Télécharger Excel",
                    data=file,
                    file_name=output_file_name,
                    mime="application/vnd.ms-excel",
                )

if __name__ == "__main__":
    main()
