import streamlit as st


def sidebar():
    with st.sidebar:
        st.markdown("# About")
        st.markdown(
            "Static visualization tool done for the Information Visualization course at GCED, UPC."
        )
        st.markdown(
            "View the project on [GitHub](https://github.com/marcfranquesa/vi-projects/tree/main/new-york-collisions)."
        )
        st.markdown("Made by Gerard Comas & Marc Franquesa.")
        st.markdown("---")


def main():
    st.set_page_config(page_title="NYC Collisions", page_icon="📊", layout="wide")
    st.header("📊 New York City Collisions")
    sidebar()
    


if __name__ == "__main__":
    main()