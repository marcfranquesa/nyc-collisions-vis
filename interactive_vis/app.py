import warnings

import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st

alt.data_transformers.disable_max_rows()
warnings.simplefilter(action="ignore", category=FutureWarning)


## INITIAL SETUP

st.set_page_config(page_title="NYC Collisions 2018", page_icon="📊", layout="wide")


@st.cache_data
def get_data():
    collisions = pd.read_csv("./processed-data/collisions_weather.csv")
    map_data = gpd.read_file("./processed-data/map.geojson")
    return collisions, map_data


collisions, map_data = get_data()

primary = "purple"
boroughs_colors = "boroughs"
schema = "schema"
vehicles_colors = "vehicles"

colors = {
    "green": "#ccebc5",
    "purple": "#bebada",
    "boroughs": {
        "Staten Island": "#8dd3c7",
        "Queens": "#fdb462",
        "Brooklyn": "#b3de69",
        "Manhattan": "#fb8072",
        "Bronx": "#80b1d3",
    },
    "vehicles": {
        "Ambulance": "#fccde5",
        "Fire truck": "#ffed6f",
        "Taxi": "#ccebc5",
    },
    "schema": "purples",
}


###### BARPLOTS

month_order = ["June", "July", "August", "September"]
month_selection = alt.selection_point(fields=["MONTH"], empty=True)

vehicle_order = ["Taxi", "Ambulance", "Fire truck"]
vehicle_selection = alt.selection_point(fields=["VEHICLE"], empty=True)

weather_order = ["Rainy", "Clear", "Partly cloudy", "Cloudy"]
weather_selection = alt.selection_point(fields=["WEATHER"], empty=True)

bars_df = (
    collisions.groupby(
        ["MONTH", "VEHICLE", "VEHICLE EMOJI", "WEATHER", "WEATHER EMOJI"]
    )
    .agg({"VALID": "sum"})
    .reset_index()
)
months = (
    alt.Chart(bars_df)
    .mark_bar(color=colors[primary])
    .encode(
        x=alt.X(
            "MONTH:O",
            sort=month_order,
            axis=alt.Axis(title="Month", labelAngle=0),
            scale=alt.Scale(domain=month_order),
        ),
        y=alt.Y("sum(VALID):Q", axis=alt.Axis(title="Collisions")),
        opacity=alt.condition(month_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("MONTH:O", title="Month"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
    )
    .add_params(month_selection)
    .transform_filter(vehicle_selection & weather_selection)
    .properties(
        title=alt.Title(
            ["Collisions per Month", "(filtered by vehicle and weather)"], dy=-0
        ),
        width=250,
        height=175,
    )
)

vehicles = (
    alt.Chart(bars_df)
    .mark_bar(color=colors[primary])
    .encode(
        x=alt.X(
            "VEHICLE:N",
            sort=vehicle_order,
            axis=alt.Axis(
                title="Vehicle", labels=False, domain=False, ticks=False, grid=False
            ),
            scale=alt.Scale(domain=vehicle_order),
        ),
        y=alt.Y("sum(VALID):Q", axis=alt.Axis(title="Collisions")),
        opacity=alt.condition(vehicle_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("VEHICLE:N", title="Vehicle"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
        # color=alt.Color(
        #     "VEHICLE:N",
        #     scale=alt.Scale(
        #             range=list(colors[vehicles_colors].values()),
        #             domain=list(colors[vehicles_colors].keys())
        #     ),
        #     legend=None
        # ),
    )
    .add_params(vehicle_selection)
    .transform_filter(month_selection & weather_selection)
    .properties(
        title=alt.Title(
            ["Collisions per Vehicle", "(filtered by month and weather)"], dy=-0
        ),
        width=200,
        height=175,
    )
)

vehicles += (
    alt.Chart(bars_df)
    .mark_text(size=18, align="center", dy=-8)
    .encode(
        x=alt.X("VEHICLE:N", sort=vehicle_order, scale=alt.Scale(domain=vehicle_order)),
        y=alt.Y("sum(VALID):Q"),
        text=alt.Text("VEHICLE EMOJI:N"),
        opacity=alt.condition(vehicle_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("VEHICLE:N", title="Vehicle"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
        color=alt.Color(legend=None),
    )
    .add_params(vehicle_selection)
    .transform_filter(month_selection & weather_selection)
)

weather = (
    alt.Chart(bars_df)
    .mark_bar(color=colors[primary])
    .encode(
        x=alt.X(
            "WEATHER:N",
            sort=weather_order,
            axis=alt.Axis(
                title="Weather", labels=False, domain=False, ticks=False, grid=False
            ),
            scale=alt.Scale(domain=weather_order),
        ),
        y=alt.Y("sum(VALID):Q", axis=alt.Axis(title="Collisions")),
        opacity=alt.condition(weather_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("WEATHER:N", title="Weather"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
    )
    .add_params(weather_selection)
    .transform_filter(month_selection & vehicle_selection)
    .properties(
        title=alt.Title(
            ["Collisions per Weather", "(filtered by month and vehicle)"], dy=-0
        ),
        width=200,
        height=175,
    )
)

weather += (
    alt.Chart(bars_df)
    .mark_text(size=18, align="center", dy=-8)
    .encode(
        x=alt.X("WEATHER:N", sort=weather_order, scale=alt.Scale(domain=weather_order)),
        y=alt.Y("sum(VALID):Q"),
        text=alt.Text("WEATHER EMOJI:N"),
        opacity=alt.condition(weather_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("WEATHER:N", title="Weather"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
    )
    .add_params(weather_selection)
    .transform_filter(month_selection & vehicle_selection)
)


###### MAP

ny_map_selection = alt.selection_point(fields=["BOROUGH"], empty=True)

collisions_borough = (
    collisions.groupby(["MONTH", "VEHICLE", "WEATHER", "BOROUGH"])
    .agg({"VALID": "sum"})
    .reset_index()
)
map_data = map_data[["BOROUGH", "AREA_KM2", "geometry"]]

ny_map = (
    alt.Chart(collisions_borough)
    .mark_geoshape(stroke="gray")
    .project(type="albersUsa")
    .transform_lookup(
        lookup="BOROUGH",
        from_=alt.LookupData(
            data=map_data, key="BOROUGH", fields=["geometry", "type", "AREA_KM2"]
        ),
    )
    .transform_filter(month_selection & weather_selection & vehicle_selection)
    .transform_aggregate(
        sumCollisions="sum(VALID)", groupby=["BOROUGH", "AREA_KM2", "geometry", "type"]
    )
    .transform_calculate(COLLISIONS_KM2="datum.sumCollisions / datum.AREA_KM2")
    .encode(
        color=alt.condition(
            ny_map_selection,
            alt.Color(
                "COLLISIONS_KM2:Q",
                scale=alt.Scale(scheme=colors[schema], type="log"),
                legend=alt.Legend(title=["Collisions per km2", "(log scale)"]),
            ),
            alt.value("lightgray"),
        ),
        tooltip=[
            alt.Tooltip("BOROUGH:N", title="Borough"),
            alt.Tooltip("COLLISIONS_KM2:Q", title="Collisions per km2"),
            alt.Tooltip("sumCollisions:Q", title="Collisions"),
        ],
    )
    .properties(width=300, height=300, title=["NYC Boroughs", "(filtered by barplots)"])
    .add_params(ny_map_selection)
)

collisions_borough_st = collisions_borough.merge(map_data, on="BOROUGH", how="left")
collisions_borough_st = collisions_borough_st[
    ["MONTH", "VEHICLE", "WEATHER", "BOROUGH", "AREA_KM2", "VALID"]
]

map_data_st = alt.Data(
    url="https://data.cityofnewyork.us/resource/7t3b-ywvw.geojson",
    format=alt.DataFormat(property="features"),
)

ny_map_st = (
    alt.Chart(collisions_borough_st)
    .mark_geoshape(stroke="gray")
    .project(type="albersUsa")
    .transform_lookup(
        lookup="BOROUGH",
        from_=alt.LookupData(
            data=map_data_st, key="properties.boro_name", fields=["geometry", "type"]
        ),
    )
    .transform_filter(month_selection & weather_selection & vehicle_selection)
    .transform_aggregate(
        sumCollisions="sum(VALID)", groupby=["BOROUGH", "AREA_KM2", "geometry", "type"]
    )
    .transform_calculate(COLLISIONS_KM2="datum.sumCollisions / datum.AREA_KM2")
    .encode(
        color=alt.condition(
            ny_map_selection,
            alt.Color(
                "COLLISIONS_KM2:Q",
                scale=alt.Scale(scheme=colors[schema], type="log"),
                legend=alt.Legend(title=["Collisions per km2", "(log scale)"]),
            ),
            alt.value("lightgray"),
        ),
        tooltip=[
            alt.Tooltip("BOROUGH:N", title="Borough"),
            alt.Tooltip("COLLISIONS_KM2:Q", title="Collisions per km2"),
            alt.Tooltip("sumCollisions:Q", title="Collisions"),
        ],
    )
    .properties(width=300, height=300, title=["NYC Boroughs", "(filtered by barplots)"])
    .add_params(ny_map_selection)
)


# Fixes boroughs not appearing when df not full
base_map = (
    alt.Chart(map_data_st)
    .mark_geoshape(stroke="gray")
    .transform_calculate(
        collisions="0",
    )
    .encode(
        color=alt.condition(
            ny_map_selection, alt.value("white"), alt.value("lightgray")
        ),
        tooltip=[
            alt.Tooltip("properties.boro_name:N", title="Borough"),
            alt.Tooltip("collisions:Q", title="Collisions per km2"),
            alt.Tooltip("collisions:Q", title="Collisions"),
        ],
    )
    .add_params(ny_map_selection)
)

ny_map = base_map + ny_map
ny_map_st = base_map + ny_map_st


###### HEATMAP

weekdayorder = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Default Mon to make it "quicker" to answer Q3
day_selection = alt.selection_point(fields=["CRASH WEEKDAY"], value="Mon")

weekdays_df = (
    collisions.groupby(
        [
            "CRASH DAY",
            "CRASH WEEKDAY",
            "CRASH WEEK NUMBER",
            "MONTH",
            "VEHICLE",
            "WEATHER",
            "DAY",
            "BOROUGH",
        ]
    )
    .agg({"VALID": "sum"})
    .reset_index()
)

# Base chart
weekdays = (
    alt.Chart(weekdays_df)
    .mark_rect()
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & ny_map_selection
    )
    .encode(
        x=alt.X(
            "CRASH WEEKDAY:O",
            title="Day of week",
            sort=weekdayorder,
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y("CRASH WEEK NUMBER:O", title="Week of year"),
        color=alt.Color(
            "sumValid:Q", scale=alt.Scale(scheme=colors[schema]), title="Collisions"
        ),
        opacity=alt.condition(day_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("CRASH DAY:O", title="Crash day"),
            alt.Tooltip("sumValid:Q", title="Collisions"),
        ],
    )
    .transform_aggregate(
        groupby=["CRASH DAY", "CRASH WEEKDAY", "CRASH WEEK NUMBER"],
        sumValid="sum(VALID):Q",
    )
    .add_params(day_selection)
    .properties(
        title=["Collisions per Week and Weekday", "(filtered by barplots and map)"],
        width=300,
        height=300,
    )
)

# Adding the asterisk to max value
weekdays += (
    alt.Chart(weekdays_df)
    .mark_text(align="center", text="*", color="white", dy=3, size=15)
    .encode(
        x=alt.X("CRASH WEEKDAY:O", sort=weekdayorder),
        y=alt.Y("CRASH WEEK NUMBER:O"),
        tooltip=[alt.Tooltip("LABEL:N", title=" ")],
    )
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & ny_map_selection
    )
    .transform_aggregate(
        groupby=["CRASH DAY", "CRASH WEEKDAY", "CRASH WEEK NUMBER"],
        sumValid="sum(VALID):Q",
    )
    # ignore if no collisions, prevents labelling every
    # data point when filtering
    .transform_filter(alt.datum.sumValid != 0)
    .transform_window(
        sort=[alt.SortField(field="sumValid", order="descending")],
        rank="rank()",
    )
    # only label the top ranked data point per year
    .transform_filter(alt.datum.rank == 1)
    .transform_calculate(LABEL="'Max value'")
)

weekdays_empty = (
    alt.Chart(weekdays_df)
    .transform_filter(month_selection)
    .mark_rect(color="white", stroke="grey", strokeWidth=0.5)
    .transform_calculate(
        collisions="0",
    )
    .encode(
        x=alt.X(
            "CRASH WEEKDAY:O",
            title="Day of week",
            sort=weekdayorder,
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y("CRASH WEEK NUMBER:O", title="Week of year"),
        tooltip=[
            alt.Tooltip("CRASH DAY:O", title="Day"),
            alt.Tooltip("collisions:Q", title="Collisions"),
        ],
        # Grid opacity
        opacity=alt.condition(day_selection, alt.value(0.05), alt.value(0)),
    )
)

weekdays = weekdays_empty + weekdays

###### LINE CHART


hours_df = (
    collisions.groupby(
        [
            "CRASH DAY",
            "CRASH WEEKDAY",
            "MONTH",
            "VEHICLE",
            "WEATHER",
            "BOROUGH",
            "DAY",
            "HOUR",
            "CRASH HOUR",
            "LOCATION AT HOUR",
        ]
    )
    .agg({"VALID": "sum"})
    .reset_index()
)

hour_selection = alt.selection_point(
    encodings=["x"], nearest=True, value=12, empty=True
)

# Base chart
hours = (
    alt.Chart(hours_df)
    .mark_line()
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .transform_aggregate(
        groupby=["HOUR", "CRASH HOUR", "LOCATION AT HOUR", "BOROUGH"],
        sumValid="sum(VALID):Q",
    )
    # Fill in missing values
    .transform_impute(
        impute="sumValid",
        key="HOUR",
        keyvals=list(range(24)),
        value=0,
        frame=[-1, 1],
        groupby=["BOROUGH"],
    )
    .encode(
        x=alt.X(
            "HOUR:Q",
            axis=alt.Axis(title="Hour", labelAngle=0),
            scale=alt.Scale(domain=[0, 23]),
        ),
        y=alt.Y(
            "sumValid:Q",
            axis=alt.Axis(title="Collisions"),
        ),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
        color=alt.Color(
            "BOROUGH:N",
            legend=None,  # alt.Legend(title="Borough"),
            scale=alt.Scale(
                range=list(colors[boroughs_colors].values()),
                domain=list(colors[boroughs_colors].keys()),
            ),
        ),
        # Fixes weird bug in streamlit
        tooltip=alt.value(None),
    )
    .properties(
        title=["Collisions per Hour and Location (filtered by barplots and heatmap)"],
        width=700,
        height=300,
    )
    # Too laggy
    # .interactive()
)

max_values = (
    alt.Chart(hours_df)
    .mark_circle(opacity=0, size=50)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        color=alt.Color(
            "BOROUGH:N",
            scale=alt.Scale(
                range=list(colors[boroughs_colors].values()),
                domain=list(colors[boroughs_colors].keys()),
            ),
        ),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
        # Fixes weird bug in streamlit
        tooltip=alt.value(None),
    )
    .transform_aggregate(
        groupby=["BOROUGH", "HOUR", "LOCATION AT HOUR"],
        sumValid="sum(VALID):Q",
    )
    # ignore if no collisions, prevents labelling every
    # data point when filtering
    .transform_filter(alt.datum.sumValid != 0)
    .transform_window(
        sort=[alt.SortField(field="sumValid", order="descending")],
        rank="rank()",
    )
    # only label the top ranked data point per year
    .transform_filter(alt.datum.rank == 1)
)

# Label for max value
max_values += (
    alt.Chart(hours_df)
    .mark_text(fontSize=20, clip=False, angle=(180 - 45), text="→", dy=5, dx=-15)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", sort=weekdayorder, scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        color=alt.Color(
            "BOROUGH:N",
            legend=None,
            scale=alt.Scale(
                range=list(colors[boroughs_colors].values()),
                domain=list(colors[boroughs_colors].keys()),
            ),
        ),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
        # Fixes weird bug in streamlit
        tooltip=[alt.Tooltip("LABEL:N", title=" ")],
    )
    .transform_aggregate(
        groupby=["BOROUGH", "HOUR", "LOCATION AT HOUR"],
        sumValid="sum(VALID):Q",
    )
    # ignore if no collisions, prevents labelling every
    # data point when filtering
    .transform_filter(alt.datum.sumValid != 0)
    .transform_window(
        sort=[alt.SortField(field="sumValid", order="descending")],
        rank="rank()",
    )
    .transform_filter(alt.datum.rank == 1)
    .transform_calculate(LABEL="'Max value'")
)

# Rule to easily mark all values in the same hour
hour_rule = (
    alt.Chart(hours_df)
    .mark_rule(color="gray", strokeDash=[10, 10])
    .transform_filter(
        month_selection
        & weather_selection
        & vehicle_selection
        & day_selection
        & hour_selection
    )
    .encode(
        x=alt.X("HOUR:Q", scale=alt.Scale(domain=[0, 23])),
    )
)

# Void chart, without it, the interaction doesn't work well
hour_rule += (
    alt.Chart(hours_df)
    .mark_text(opacity=0)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sum(VALID):Q"),
        color=alt.Color(
            "BOROUGH:N",
            scale=alt.Scale(
                range=list(colors[boroughs_colors].values()),
                domain=list(colors[boroughs_colors].keys()),
            ),
        ),
        # Fixes weird bug in streamlit
        tooltip=alt.value(None),
    )
    .add_params(hour_selection)
)

# Circle mark on max value in selected hour
hour_rule += (
    alt.Chart(hours_df)
    .mark_circle(size=50)
    .transform_filter(
        month_selection
        & weather_selection
        & vehicle_selection
        & day_selection
        & hour_selection
    )
    .encode(
        x=alt.X("HOUR:Q", scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        color=alt.Color(
            "BOROUGH:N",
            scale=alt.Scale(
                range=list(colors[boroughs_colors].values()),
                domain=list(colors[boroughs_colors].keys()),
            ),
        ),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
        # Fixes weird bug in streamlit
        tooltip=alt.value(None),
    )
    .transform_aggregate(
        groupby=["BOROUGH", "HOUR"],
        sumValid="sum(VALID):Q",
    )
    .transform_filter(alt.datum.sumValid != 0)
    .transform_window(
        sort=[alt.SortField(field="sumValid", order="descending")],
        rank="rank()",
    )
    # only label the top ranked data point
    .transform_filter(alt.datum.rank == 1)
)

# Adds tooltip to each point in data, note that if more than
# one borough has the same value, it will show them all
tooltip = (
    alt.Chart(hours_df)
    .mark_circle(opacity=0, size=50)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        opacity=alt.value(0),
        tooltip=[
            alt.Tooltip("first_bo:N", title="Boroughs"),
            alt.Tooltip("sec_bo:N", title=" "),
            alt.Tooltip("thi_bo:N", title=" "),
            alt.Tooltip("fo_bo:N", title=" "),
            alt.Tooltip("fi_bo:N", title=" "),
            alt.Tooltip("CRASH HOUR:N", title="Hour"),
            alt.Tooltip("COL:Q", title="Collisions"),
        ],
    )
    .transform_aggregate(
        groupby=["HOUR", "CRASH HOUR", "BOROUGH"],
        sumValid="sum(VALID):Q",
    )
    .transform_aggregate(
        groupby=["HOUR", "CRASH HOUR", "sumValid"],
        VALUES="values(BOROUGH):N",
        COUNT="count():Q",
        COL="max(sumValid)",
    )
    .transform_calculate(
        first_bo="datum.VALUES[0].BOROUGH",
        sec_bo="datum.COUNT > 1 ? datum.VALUES[1].BOROUGH : ''",
        thi_bo="datum.COUNT > 2 ? datum.VALUES[2].BOROUGH : ''",
        fo_bo="datum.COUNT > 3 ? datum.VALUES[3].BOROUGH : ''",
        fi_bo="datum.COUNT > 4 ? datum.VALUES[4].BOROUGH : ''",
    )
)

hours = hours + max_values + hour_rule + tooltip


###### SCATTER

factor_df = (
    collisions.groupby(
        [
            "CRASH DAY",
            "CRASH WEEKDAY",
            "MONTH",
            "VEHICLE",
            "WEATHER",
            "BOROUGH",
            "ORIGINAL FACTOR",
            "FACTOR",
        ]
    )
    .agg(
        {
            "VALID": "sum",
            "NUMBER OF PERSONS INJURED": "sum",
            "NUMBER OF PERSONS KILLED": "sum",
        }
    )
    .reset_index()
)

factor_selection = alt.selection_point(fields=["ORIGINAL FACTOR"], empty=True)

factors = (
    alt.Chart(factor_df)
    .mark_circle(color=colors[primary], size=125, opacity=1)
    .transform_filter(month_selection & weather_selection & vehicle_selection)
    .transform_aggregate(
        sumValid="sum(VALID):Q",
        sumInjured="sum(NUMBER OF PERSONS INJURED):Q",
        groupby=["ORIGINAL FACTOR", "BOROUGH"],
    )
    .transform_calculate(
        INJURED_PER_COLLISION="datum['sumInjured'] / datum['sumValid']"
    )
    .encode(
        x=alt.X(
            "INJURED_PER_COLLISION:Q",
            axis=alt.Axis(title="Average injuries per collision", tickCount=10),
        ),
        y=alt.Y("sumValid:Q", axis=alt.Axis(title="Collisions")),
        color=alt.condition(
            ny_map_selection & factor_selection,
            alt.Color(
                "BOROUGH:N",
                legend=alt.Legend(title="Borough"),
                scale=alt.Scale(
                    range=list(colors[boroughs_colors].values()),
                    domain=list(colors[boroughs_colors].keys()),
                ),
            ),
            alt.value("lightgray"),
        ),
        tooltip=[
            alt.Tooltip("ORIGINAL FACTOR:N", title="Factor"),
            alt.Tooltip("sumValid:Q", title="Collisions"),
            alt.Tooltip(
                "INJURED_PER_COLLISION:Q", title="Average injuries per collision"
            ),
        ],
    )
    .properties(
        title=["Driving infractions and their danger", "(filtered by barplots)"],
        width=700,
        height=300,
    )
    .add_params(factor_selection)
    # Too laggy
    # .interactive()
)


if __name__ == "__main__":
    with st.sidebar:
        st.markdown("# About")
        st.markdown(
            "Interactive visualization tool done for the Information Visualization course at GCED, UPC."
        )
        st.markdown("Made by Gerard Comas & Marc Franquesa.")
        st.markdown("---")
        st.markdown(
            "Interactions take longer than desired, especially those that filter."
        )
        st.markdown("---")
        st.markdown("☕")

    st.header("📊 New York City Collisions (Summer 2018)")

    st.altair_chart(
        (
            months.properties(width=355)
            | weather.properties(width=315)
            | vehicles.properties(width=315)
        )
        & (
            (
                ny_map_st.properties(width=400, height=350)
                | factors.properties(width=550, height=300)
            )
            & (weekdays | hours.properties(width=700))
        ),
        use_container_width=False,
        theme=None,
    )
