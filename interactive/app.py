import warnings

import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st

alt.data_transformers.disable_max_rows()
warnings.simplefilter(action="ignore", category=FutureWarning)


@st.cache_data
def get_data():
    collisions = pd.read_csv("./processed-data/collisions_weather.csv")
    map_data = gpd.read_file("./processed-data/map.geojson")
    return collisions, map_data


collisions, map_data = get_data()

primary = "green"
secondary = ""

colors = {
    primary: "#66c2a4",
    secondary: "",
}

collisions["VALID"] = collisions["VALID"].astype("int64")


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
            "MONTH:O", sort=month_order, axis=alt.Axis(title="Month", labelAngle=0)
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
        ),
        y=alt.Y("sum(VALID):Q", axis=alt.Axis(title="Collisions")),
        opacity=alt.condition(vehicle_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("VEHICLE:N", title="Vehicle"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
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
        x=alt.X("VEHICLE:N", sort=vehicle_order),
        y=alt.Y("sum(VALID):Q"),
        text=alt.Text("VEHICLE EMOJI:N"),
        opacity=alt.condition(vehicle_selection, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("VEHICLE:N", title="Vehicle"),
            alt.Tooltip("sum(VALID):Q", title="Collisions"),
        ],
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
        x=alt.X("WEATHER:N", sort=weather_order),
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


ny_map_selection = alt.selection_point(fields=["BOROUGH"], empty=True)

collisions_borough = (
    collisions.groupby(["MONTH", "VEHICLE", "WEATHER", "BOROUGH"])
    .agg({"VALID": "sum"})
    .reset_index()
)
map_data = map_data[["BOROUGH", "AREA_KM2", "geometry"]]

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
                scale=alt.Scale(scheme="greens"),
                legend=alt.Legend(title="Collisions per km2"),
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
            "sumValid:Q", scale=alt.Scale(scheme="greens"), title="Collisions"
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
)


hour_selection = alt.selection_point(encodings=["x"], nearest=True, value=12)

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

# Base chart
hours = (
    alt.Chart(hours_df)
    .mark_line()
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X(
            "HOUR:Q",
            axis=alt.Axis(title="Hour", labelAngle=0),
            scale=alt.Scale(domain=[0, 23]),
        ),
        y=alt.Y("sum(VALID):Q", axis=alt.Axis(title="Collisions")),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
        color=alt.Color("BOROUGH:N", legend=alt.Legend(title="Borough")),
        tooltip=alt.value(None),
    )
    .properties(
        title=[
            "Collisions per Hour and Location (filtered by barplots and heatmap)",
            "",
        ],
        width=700,
        height=300,
    )
)

# Label for max value
max_text = (
    alt.Chart(hours_df)
    .mark_text(size=10, clip=False, align="left", dy=-10, dx=5)
    .transform_filter(
        month_selection
        & weather_selection
        & vehicle_selection
        & day_selection
        & ~hour_selection
    )
    .encode(
        x=alt.X("HOUR:Q", sort=weekdayorder, scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        text="LOCATION AT HOUR:N",
        color=alt.Color("BOROUGH:N", legend=None),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
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
    .transform_filter(alt.datum.rank == 1)
)

max_text += (
    alt.Chart(hours_df)
    .mark_circle(opacity=0, size=50)
    .transform_filter(
        month_selection
        & weather_selection
        & vehicle_selection
        & day_selection
        & ~hour_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q"),
        color=alt.Color("BOROUGH:N"),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
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
    .mark_text(align="left", dx=5, dy=-5, size=10)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sum(VALID):Q"),
        text=alt.condition(hour_selection, "sum(VALID):Q", alt.value("")),
        opacity=alt.value(0),
        color=alt.Color("BOROUGH:N"),
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
        color=alt.Color("BOROUGH:N"),
        opacity=alt.condition(ny_map_selection, alt.value(1), alt.value(0.2)),
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
    # only label the top ranked data point per year
    .transform_filter(alt.datum.rank == 1)
)

# Adds tooltip to each point in data, note that if more than
# one borough has the same value, it will show them all
tooltip = (
    alt.Chart(hours_df)
    .mark_circle(opacity=0, size=200)
    .transform_filter(
        month_selection & weather_selection & vehicle_selection & day_selection
    )
    .encode(
        x=alt.X("HOUR:Q", axis=alt.Axis(labelAngle=0), scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("sumValid:Q", axis=alt.Axis(title="Total collisions")),
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

hours = hours + max_text + hour_rule + tooltip


final_chart = (
    (months | vehicles | weather)
    & (ny_map_st | weekdays)
    .resolve_legend(color="independent")
    .resolve_scale(color="independent")
    & (hours)
).resolve_legend(color="independent")

st.altair_chart(final_chart, use_container_width=False, theme=None)
