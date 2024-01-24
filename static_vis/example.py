import altair as alt
import streamlit as st

data = alt.Data(
    url="https://raw.githubusercontent.com/marcfranquesa/data/main/map.geojson",
    format=alt.DataFormat(property="features"),
)


base = (
    alt.Chart(data)
    .mark_geoshape()
    .project(type="albersUsa")
    .encode(
        color=alt.Color(
            "COLLISIONS / KM2:Q",
            scale=alt.Scale(scheme="purples"),
            legend=alt.Legend(title="Collisions per km2"),
        ),
    )
    .properties(width=600, height=600, title="NYC Community Districts")
)

# Streamlit app
st.title("GeoJson")
st.altair_chart(base)
