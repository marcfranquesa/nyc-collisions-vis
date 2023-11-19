import tempfile
from typing import Dict, List, Tuple

import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


class WeekChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        moments: List[str],
        colors: Dict[str, str],
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.before, self.after, self.all_time = moments
        self.colors = colors
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.weekends = ["Saturday", "Sunday"]
        self.weekdayorder = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        self.weekdays_df, self.weekends_df = self._process_data(collisions)

    def _process_data(
        self, collisions: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        days_df = (
            collisions.groupby(["CRASH WEEKDAY", "AFTER COVID"])
            .size()
            .reset_index(name="counts")
        )

        days_df["MOMENT"] = np.where(days_df["AFTER COVID"], self.after, self.before)

        weekdays_df = days_df[days_df["CRASH WEEKDAY"].isin(self.weekdays)]
        weekends_df = days_df[days_df["CRASH WEEKDAY"].isin(self.weekends)]

        return weekdays_df, weekends_df

    def make_plot(self) -> alt.Chart:
        weekdays_ch = (
            alt.Chart(self.weekdays_df)
            .mark_bar(opacity=self.secondary_opactiy)
            .encode(
                x=alt.X(
                    "CRASH WEEKDAY:O",
                    axis=alt.Axis(labelAngle=0, title=None),
                    sort=self.weekdayorder,
                ),
                xOffset="MOMENT:O",
                y=alt.Y(
                    "counts:Q",
                    axis=alt.Axis(title="Collisions / Means", grid=True),
                    scale=alt.Scale(domain=[0, 13000]),
                ),
                color=alt.Color(
                    "MOMENT:O",
                    scale=alt.Scale(
                        domain=list(self.colors.keys()),
                        range=list(self.colors.values()),
                    ),
                ),
            )
            .properties(title=alt.Title("Weekdays", fontSize=10, fontWeight=600))
        )

        averages_weekday = (
            alt.Chart(self.weekdays_df)
            .mark_rule(opacity=self.main_opactiy)
            .encode(y="mean(counts):Q", size=alt.value(2), color=alt.Color("MOMENT:O"))
        )

        weekends_ch = (
            alt.Chart(self.weekends_df)
            .mark_bar(opacity=self.secondary_opactiy)
            .encode(
                x=alt.X(
                    "CRASH WEEKDAY:O",
                    axis=alt.Axis(labelAngle=0, title=None),
                    sort=self.weekdayorder,
                ),
                xOffset="MOMENT:O",
                y=alt.Y(
                    "counts:Q",
                    axis=alt.Axis(
                        title=None, labels=False, domain=False, ticks=False, grid=True
                    ),
                    scale=alt.Scale(domain=[0, 13000]),
                ),
                color=alt.Color(
                    "MOMENT:O",
                    scale=alt.Scale(
                        domain=list(self.colors.keys()),
                        range=list(self.colors.values()),
                    ),
                    legend=alt.Legend(title=None),
                ),
            )
            .properties(title=alt.Title("Weekends", fontSize=10, fontWeight=600))
        )

        averages_weekend = (
            alt.Chart(self.weekends_df)
            .mark_rule(opacity=self.main_opactiy)
            .encode(y="mean(counts):Q", size=alt.value(2), color="MOMENT:O")
        )

        return (weekdays_ch + averages_weekday).properties(width=318, height=300) | (
            weekends_ch + averages_weekend
        ).properties(width=136, height=300)


class VehiclesChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        moments: List[str],
        colors: Dict[str, str],
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.before, self.after, self.all_time = moments
        self.colors = colors
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.vehicles = self._process_data(collisions)

        self.maximum = max(self.vehicles["COLLISIONS"])
        self.minimum = min(self.vehicles["COLLISIONS"])
        self.mean = self.vehicles["COLLISIONS"].mean()

    def _process_data(self, collisions: pd.DataFrame) -> pd.DataFrame:
        vehicles = collisions.groupby(["VEHICLE"]).size().reset_index(name="counts")

        vehicles = collisions[
            ["VEHICLE", "NUMBER OF PERSONS INJURED", "NUMBER OF PERSONS KILLED"]
        ]
        vehicles = vehicles[vehicles["VEHICLE"] != "Unknown"]

        vehicles = (
            vehicles.groupby("VEHICLE")
            .agg(
                {
                    "VEHICLE": "count",
                    "NUMBER OF PERSONS INJURED": "sum",
                    "NUMBER OF PERSONS KILLED": "sum",
                }
            )
            .rename(columns={"VEHICLE": "COLLISIONS"})
            .reset_index()
        )

        total_collisions = vehicles["COLLISIONS"].sum()

        vehicles["% COLLISIONS"] = vehicles["COLLISIONS"] / total_collisions * 100

        total_injured = vehicles["NUMBER OF PERSONS INJURED"].sum()
        total_killed = vehicles["NUMBER OF PERSONS KILLED"].sum()

        vehicles["% INJURED"] = (
            vehicles["NUMBER OF PERSONS INJURED"] / total_injured * 100
        )
        vehicles["% KILLED"] = vehicles["NUMBER OF PERSONS KILLED"] / total_killed * 100

        vehicles["INJURED PER COLLISION"] = (
            vehicles["NUMBER OF PERSONS INJURED"] / vehicles["COLLISIONS"]
        )
        vehicles["KILLED PER COLLISION"] = (
            vehicles["NUMBER OF PERSONS KILLED"] / vehicles["COLLISIONS"]
        )

        return vehicles

    def make_plot(self) -> alt.Chart:
        def parse(i):
            if i < 1000:
                return f"{i}"
            return f"{int(i//1000)},{int(i%1000)}"

        legend_labels = f"datum.label == '{parse(self.maximum)}' ? '{parse(self.maximum)}   (max)' : datum.label == '{parse(self.minimum)}' ? '{parse(self.minimum)}        (min)' : '{parse(self.mean)}   (mean)'"
        scatter = (
            alt.Chart(self.vehicles)
            .mark_circle(color=self.colors[self.all_time])
            .encode(
                x=alt.X(
                    "INJURED PER COLLISION:Q",
                    axis=alt.Axis(title="Injuries per collision", tickCount=10),
                ),
                y=alt.Y(
                    "KILLED PER COLLISION:Q",
                    axis=alt.Axis(title="Deaths per collision"),
                ),
                size=alt.Size(
                    "COLLISIONS:Q",
                    scale=alt.Scale(range=[10, 700]),
                    legend=alt.Legend(
                        title="Total collisions",
                        values=[self.minimum, self.mean, self.maximum],
                        labelExpr=legend_labels,
                    ),
                ),
            )
        )

        # Lets add labels for each vehicle
        labels = scatter.mark_text(align="right", dx=-15, dy=0).encode(
            text="VEHICLE:N", size=alt.value(10)
        )

        return (scatter + labels).properties(
            title="Vehicle Danger", width=590, height=300
        )


class HourChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        moments: List[str],
        colors: Dict[str, str],
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.before, self.after, self.all_time = moments
        self.colors = colors
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.time_df, self.time_all_df = self._process_data(collisions)

    def _process_data(
        self, collisions: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        time_df = collisions
        time_df["HOUR"] = pd.to_datetime(time_df["CRASH DATETIME"]).dt.hour
        time_df = (
            time_df.groupby(["HOUR", "AFTER COVID"]).size().reset_index(name="counts")
        )

        time_df["MOMENT"] = np.where(time_df["AFTER COVID"], self.after, self.before)

        time_all_df = time_df.groupby(["HOUR"]).sum().reset_index()

        return time_df, time_all_df

    def make_plot(self) -> alt.Chart:
        time_ch = (
            alt.Chart(self.time_df)
            .mark_bar(opacity=self.secondary_opactiy)
            .encode(
                x=alt.X(
                    "HOUR:O", axis=alt.Axis(labelAngle=0, tickOffset=-10), title="Hour"
                ),
                y=alt.Y("counts:Q", title="Collisions / Mean"),
                color=alt.Color(
                    "MOMENT:O",
                    scale=alt.Scale(
                        domain=list(self.colors.keys()),
                        range=list(self.colors.values()),
                    ),
                    legend=alt.Legend(title=None),
                ),
                order=alt.Order("MOMENT:O", sort="ascending"),
            )
        )

        averages_weekend = (
            alt.Chart(self.time_all_df)
            .mark_rule(opacity=self.main_opactiy, color=self.colors[self.all_time])
            .encode(
                y="mean(counts):Q",
                size=alt.value(2),
            )
        )

        return (time_ch + averages_weekend).properties(title="Collisions by Hour")


class MapChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        map_data: pd.DataFrame,
        moments: List[str],
        colors: Dict[str, str],
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.before, self.after, self.all_time = moments
        self.colors = colors
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.labels = {"boro_cd": ["105", "205"], "LABELS": ["Midtown", "Fordham"]}

        self.map_data = map_data
        self.top, self.horse, self.gokart = self._process_data(collisions, map_data)

    def _process_data(
        self, collisions: pd.DataFrame, map_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        top = map_data.sort_values(by="COLLISIONS / KM2", ascending=False).head(4)
        top[["LATITUDE", "LONGITUDE"]] = top["geometry"].centroid.apply(
            lambda x: pd.Series([x.y, x.x])
        )
        top = top.merge(
            pd.DataFrame(self.labels), left_on="boro_cd", right_on="boro_cd"
        )
        top.loc[top["LABELS"] == "Fordham", ["LATITUDE", "LONGITUDE"]] = [
            40.849746,
            -73.89958,
        ]
        return (
            top,
            collisions[collisions["ORIGINAL VEHICLE"] == "Horse"],
            collisions[collisions["ORIGINAL VEHICLE"] == "Go kart"],
        )

    def make_plot(self) -> alt.Chart:
        base = (
            alt.Chart(self.map_data)
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

        text_labels = (
            alt.Chart(self.top)
            .mark_text(angle=0, dx=0, dy=0, fill="white", size=9)
            .encode(
                longitude="LONGITUDE:Q",
                latitude="LATITUDE:Q",
                text="LABELS:N",
            )
        )

        horse = (
            alt.Chart(self.horse)
            .mark_text(text="🐎", size=18)
            .encode(
                longitude="LONGITUDE:Q",
                latitude="LATITUDE:Q",
            )
        )

        gokart = (
            alt.Chart(self.gokart)
            .mark_text(text="🏎️", size=18)
            .encode(
                longitude="LONGITUDE:Q",
                latitude="LATITUDE:Q",
            )
        )

        return base + horse + gokart + text_labels


class WeatherChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        weather: pd.DataFrame,
        moments: List[str],
        colors: Dict[str, str],
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.before, self.after, self.all_time = moments
        self.colors = colors
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.conditionorder = ["Perfect", "Moderate", "Bad", "Terrible"]

        self.nbins = 3
        self.base = {
            "sknt": 0,
            "p01i": 0,
            "vsby": 16.093440,
        }
        self.weather = self._process_data(collisions, weather)

    def _process_data(
        self, collisions: pd.DataFrame, weather: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        collisions_weather = collisions[["CRASH DATETIME", *list(self.base.keys())]]
        dfs = []
        for name, base_value in self.base.items():
            base_bin = collisions_weather.loc[collisions_weather[name] == base_value]
            rest = collisions_weather.loc[collisions_weather[name] != base_value]
            bins = pd.cut(rest.dropna(subset=[name])[name], bins=self.nbins)
            midpoints = bins.apply(lambda x: x.mid.round(2))
            grouped = rest.groupby(midpoints)
            grouped = grouped.size().reset_index(name="counts")
            if base_value > 0:
                grouped = grouped.sort_index(ascending=False)

            df = pd.DataFrame({name: [base_value], "counts": [len(base_bin)]})
            df = pd.concat([df, grouped]).reset_index(drop=True)

            base_bin_w = weather.loc[weather[name] == base_value]
            rest_w = weather.loc[weather[name] != base_value]
            bins_w = pd.cut(rest_w.dropna(subset=[name])[name], bins=self.nbins)
            midpoints_w = bins_w.apply(lambda x: x.mid.round(2))
            grouped_w = rest_w.groupby(midpoints_w)
            grouped_w = grouped_w.size().reset_index(name="counts")
            if base_value > 0:
                grouped_w = grouped_w.sort_index(ascending=False)
            df_w = pd.DataFrame({name: [base_value], "counts": [len(base_bin_w)]})
            df_w = pd.concat([df_w, grouped_w]).reset_index(drop=True)

            df = pd.merge(df, df_w, on=name)
            df["COLLISIONS / HOUR"] = df["counts_x"] / df["counts_y"]
            df.loc[:, "WEATHER"] = name
            df = df[["COLLISIONS / HOUR", "WEATHER"]]
            df["CONDITION"] = self.conditionorder
            dfs.append(df)

        return pd.concat(dfs)

    def make_plot(self) -> alt.Chart:
        axis_y_labels = "datum.label == 'p01i' ? 'Rain' : datum.label == 'sknt' ? 'Wind' : 'Visbility'"

        return (
            alt.Chart(self.weather)
            .mark_rect()
            .encode(
                x=alt.X(
                    "CONDITION:O",
                    axis=alt.Axis(
                        title="Condition",
                        labels=True,
                        labelAngle=0,
                        domain=True,
                        ticks=True,
                        grid=False,
                    ),
                    sort=self.conditionorder,
                ),
                y=alt.Y(
                    "WEATHER:O", axis=alt.Axis(title="Weather", labelExpr=axis_y_labels)
                ),
                color=alt.Color(
                    "COLLISIONS / HOUR:Q",
                    scale=alt.Scale(scheme="purples"),
                    legend=alt.Legend(title="Collisions per Hour"),
                ),
            )
            .properties(title="Different Weather Conditions", width=481, height=300)
            .resolve_legend(color="independent")
        )


class FactorChart:
    def __init__(
        self,
        collisions: pd.DataFrame,
        main_opactiy: int,
        secondary_opacity: int,
    ) -> None:
        self.main_opactiy = main_opactiy
        self.secondary_opactiy = secondary_opacity

        self.factors1, self.factors2 = self._process_data(collisions)

    def _process_data(
        self, collisions: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        factors = collisions[["VEHICLE", "FACTOR", "ORIGINAL FACTOR"]]
        factors1_vehicle = (
            factors.groupby(["VEHICLE"]).size().reset_index(name="counts_vehicle")
        )
        factors1 = (
            factors.groupby(["VEHICLE", "FACTOR"]).size().reset_index(name="counts")
        )
        factors1 = factors1[
            (factors1["VEHICLE"] != "Unknown") & (factors1["FACTOR"] != "Unspecified")
        ]

        factors1 = factors1.merge(factors1_vehicle, on="VEHICLE")
        factors1["PERCENTAGE"] = factors1["counts"] / factors1["counts_vehicle"] * 100

        factors2 = factors[factors["FACTOR"] == "Driving Infraction"]
        factors2_vehicle = (
            factors2.groupby(["VEHICLE"]).size().reset_index(name="counts_vehicle")
        )
        factors2 = (
            factors2.groupby(["VEHICLE", "ORIGINAL FACTOR"])
            .size()
            .reset_index(name="counts")
        )
        factors2 = factors2[(factors2["VEHICLE"] != "Unknown")]

        factors2 = factors2.merge(factors2_vehicle, on="VEHICLE")
        factors2["PERCENTAGE"] = factors2["counts"] / factors2["counts_vehicle"] * 100

        return factors1, factors2

    def make_plot(self) -> alt.Chart:
        factors1 = (
            alt.Chart(self.factors1)
            .mark_rect()
            .encode(
                x=alt.X("FACTOR:O", axis=alt.Axis(title="Factor", labelAngle=30)),
                y=alt.Y("VEHICLE:O", axis=alt.Axis(title="Vehicle")),
                color=alt.Color(
                    "PERCENTAGE:Q",
                    scale=alt.Scale(scheme="tealblues"),
                    legend=alt.Legend(title="Percentage of Collisions"),
                ),
            )
            .properties(
                title="Factors Contributing to Collisions", width=522, height=300
            )
        )
        factors2 = (
            alt.Chart(self.factors2)
            .mark_rect()
            .encode(
                x=alt.X(
                    "ORIGINAL FACTOR:O", axis=alt.Axis(title="Factor", labelAngle=30)
                ),
                y=alt.Y("VEHICLE:O", axis=alt.Axis(title=None)),
                color=alt.Color(
                    "PERCENTAGE:Q",
                    scale=alt.Scale(scheme="tealblues"),
                    legend=alt.Legend(
                        title=["Percentage of Collisions due", "to Driving Infractions"]
                    ),
                ),
            )
            .properties(
                title="Driving Infractions contributing to Collisions",
                width=522,
                height=300,
            )
        )

        return (factors1 | factors2).resolve_legend(color="independent")


class Sidebar:
    def __init__(self) -> None:
        self.st = st.sidebar

    def show(self):
        self.st.markdown("# About")
        self.st.markdown(
            "Static visualization tool done for the Information Visualization course at GCED, UPC."
        )
        self.st.markdown(
            "View the code on [GitHub](https://github.com/marcfranquesa/vi-projects/tree/main/new-york-collisions)."
        )
        self.st.markdown("Made by Gerard Comas & Marc Franquesa.")
        self.st.markdown("---")


class Center:
    def __init__(self) -> None:
        self.st = st
        self.before = "Summer 2018 (Before Covid)"
        self.after = "Summer 2020 (After Covid)"
        self.all_time = "All"
        self.moments = [self.before, self.after, self.all_time]
        self.colors = {
            self.before: "#fdc086",  # Before COVID
            self.after: "#7fc97f",  # After COVID
            self.all_time: "#beaed4",  # Both
        }
        self.main_opactiy = 1
        self.secondary_opactiy = 0.5

        self.collisions, self.map_data, self.weather = self._load_data()

        if "charts" not in st.session_state:
            self.week = WeekChart(
                self.collisions,
                self.moments,
                self.colors,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            self.vehicles = VehiclesChart(
                self.collisions,
                self.moments,
                self.colors,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            self.hours = HourChart(
                self.collisions,
                self.moments,
                self.colors,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            self.map = MapChart(
                self.collisions,
                self.map_data,
                self.moments,
                self.colors,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            self.weatherchart = WeatherChart(
                self.collisions,
                self.weather,
                self.moments,
                self.colors,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            self.factors = FactorChart(
                self.collisions,
                self.main_opactiy,
                self.secondary_opactiy,
            ).make_plot()
            st.session_state["charts"] = [
                self.week,
                self.vehicles,
                self.hours,
                self.map,
                self.weatherchart,
                self.factors,
            ]
        else:
            (
                self.week,
                self.vehicles,
                self.hours,
                self.map,
                self.weatherchart,
                self.factors,
            ) = st.session_state["charts"]

    def _load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        return (
            pd.read_csv("./new-york-collisions/processed-data/collisions.csv"),
            gpd.read_file("./new-york-collisions/processed-data/map.geojson"),
            pd.read_csv("./new-york-collisions/processed-data/weather.csv"),
        )

    def show(self) -> None:
        self.st.header("📊 New York City Collisions")

        # final_chart = (
        #     (
        #         (
        #             (self.map | (self.week & self.hours))
        #             & (self.vehicles | self.weatherchart)
        #             .resolve_scale(color="independent")
        #             .resolve_legend(size="independent")
        #         )
        #         & self.factors
        #     )
        #     .resolve_scale(color="independent")
        #     .resolve_legend(size="independent")
        # ).configure_legend(symbolOpacity=1)

        final_chart = (
            (
                (
                    (self.map & self.vehicles)
                    .resolve_scale(color="independent")
                    .resolve_legend(size="independent")
                    | (self.weatherchart & (self.week & self.hours))
                )
                & self.factors
            )
            .resolve_legend(size="independent")
            .resolve_scale(color="independent")
            .configure_legend(symbolOpacity=1)
        )

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html"
        ) as arquivo:
            final_chart.save(arquivo.name)
            arquivo.flush()
            HtmlFile = open(arquivo.name, "r", encoding="utf-8")

            # Load HTML file in HTML component for display on Streamlit page
            components.html(HtmlFile.read(), height=2000)

        # If choropleth maps worked in streamlit:
        # self.st.altair_chart(final_chart, use_container_width=False, theme=None)


class Screen:
    def __init__(self) -> None:
        self.st = st

    def _config(self) -> None:
        self.st.set_page_config(
            page_title="NYC Collisions", page_icon="📊", layout="wide"
        )

    def show(self) -> None:
        self._config()
        Sidebar().show()
        Center().show()


if __name__ == "__main__":
    Screen().show()
