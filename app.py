import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ClientsideFunction

import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib

from datetime import date
import pandas_gbq
project_id = "eminent-hall-293522"


sql = """
    SELECT county_fips_code, prediction_date, new_confirmed, new_confirmed_ground_truth
    FROM `bigquery-public-data.covid19_public_forecasts.county_14d` 
    WHERE state_name="{state_name}"  AND county_name="{county_name}"
    """.format(state_name = "Pennsylvania", county_name = "Allegheny")
forecast_df = pandas_gbq.read_gbq(sql, project_id=project_id)

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server
app.config.suppress_callback_exceptions = True

# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()

# Read data
df_population_2019 = pd.read_csv("pop_est_2019.csv")
df_county_name = pd.read_csv("county_name.csv")
df_activity = pd.read_csv("activity.csv")
activity_list = df_activity["activity"].unique()

# df = pd.read_csv(DATA_PATH.joinpath("clinical_analytics.csv"))

state_list = sorted(df_county_name["state_name"].unique())
county_dict = {}
for i in state_list:
    df_county_name_idx = df_county_name["state_name"] == i
    county_dict[i] = sorted(df_county_name[df_county_name_idx]["county_name"].unique())


day_list = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]

# check_in_duration = df["Check-In Time"].describe()

# # Register all departments for callbacks
# all_departments = df["Department"].unique().tolist()
# wait_time_inputs = [
#     Input((i + "_wait_time_graph"), "selectedData") for i in all_departments
# ]
# score_inputs = [Input((i + "_score_graph"), "selectedData") for i in all_departments]



def general_risk():
    return html.Div(
        id="general_risk-card",
        children=[
            html.H5("Covid Exposure Risk Analysis"),
            # html.H3("Exposure Risk based on your historical trips and locations"),
            html.H3("Welcome to use the personalized COVID-19 exposure risk analysis"),
            html.Div(
                id="intro2",
                children="COVID-19 Exposure risk analysis based on your location and daily activities. Choose your daily activities to get your personalized advice.",
            ),
        ],
    )


def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.Br(),
            html.P("Select State"),
            dcc.Dropdown(
                id="state-select",
                options=[{"label": i, "value": i} for i in state_list],
                # value=state_list[0],
                value='Pennsylvania',
            ),
            html.Br(),
            html.P("Select County"),
            dcc.Dropdown(
                id="county-select",
                # options=[{"label": i, "value": i} for i in county_dict['Pennsylvania']],
                # value=state_list[0],
                value='Allegheny',
            ),
            html.Br(),
            html.P("Select Activity for Today"),
            dcc.Dropdown(
                id="activity-select",
                options=[{"label": i, "value": i} for i in activity_list],
                value=list(activity_list[1:4])+list(activity_list[-2:]),
                multi=True,
            ),
            html.Br(),
        ],
    )





@app.callback(
    dash.dependencies.Output('county-select', 'options'),
    [dash.dependencies.Input('state-select', 'value')]
)
def update_date_dropdown(name):
    return [{'label': i, 'value': i} for i in county_dict[name]]


from IPython.display import display
pd.options.display.max_columns = None
pd.options.display.max_rows = None
def generate_forecast_heatmap(county_pop, forecast_df):
    forecast_df = forecast_df.sort_values(by=['prediction_date'])
    first_day = datetime.datetime.strptime(str(list(forecast_df['prediction_date'])[0])[:10], '%Y-%m-%d')
    # end_day = datetime.datetime.strptime(str(list(forecast_df['prediction_date'])[-1])[:10], '%Y-%m-%d')


    

    x_axis = day_list  # 7 day time list
    # y_axis = ["Past\n2 Weeks","Past\nWeek","Current\nWeek","Next\nWeek","Next\n2 Weeks"]
    y_axis = ["Week 1","Week 2","Week 3","Week 4","Week 5"]
    # y_axis = [4,3,2,1,0]

    # Get z value : sum(number of records) based on x, y,

    z = np.zeros((5, 7))
    date = np.chararray((5, 7))
    z[:] = np.nan
    annotations = []

    weekday_idx = first_day.weekday()+1
    week_idx = 0
    day_idx = 0
    while day_idx < len(list(forecast_df['prediction_date'])) - 1:
        if weekday_idx == 7:
            weekday_idx = 0
            week_idx += 1
        annotate_curr = True
        if pd.isnull(list(forecast_df['new_confirmed'])[day_idx]):
            if not pd.isnull(list(forecast_df['new_confirmed_ground_truth'])[day_idx]):
                z[week_idx][weekday_idx] = int(list(forecast_df['new_confirmed_ground_truth'])[day_idx])
            else:
                annotate_curr = False
        else:
            z[week_idx][weekday_idx] = int(list(forecast_df['new_confirmed'])[day_idx])
        date[week_idx][weekday_idx] = str(list(forecast_df['prediction_date'])[day_idx])
        if annotate_curr:
            annotation_dict = dict(
                showarrow=False,
                text=str(list(forecast_df['prediction_date'])[day_idx])[:10] + "<br>" + str(z[week_idx][weekday_idx]),
                xref="x",
                yref="y",
                x=weekday_idx,
                y=week_idx,
                font=dict(family="sans-serif"),
            )
            annotations.append(annotation_dict)

        weekday_idx += 1
        day_idx += 1





    # Heatmap
    hovertemplate = "<b> %{y} %{x} <br><br> %{z} New confirmed cases"

    data = [
        dict(
            x=x_axis,
            y=y_axis,
            z=z,
            type="heatmap",
            name="",
            hovertemplate=hovertemplate,
            showscale=False,
            colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]],
        )
    ]

    shapes = []
    layout = dict(
        margin=dict(l=70, b=50, t=50, r=50),
        modebar={"orientation": "v"},
        font=dict(family="Open Sans"),
        annotations=annotations,
        shapes=shapes,
        xaxis=dict(
            side="top",
            ticks="",
            # ticklen=2,
            tickfont=dict(family="sans-serif"), ticksuffix=" "
            # tickcolor="#ffffff",
        ),
        yaxis=dict(
            side="left", ticks="", tickfont=dict(family="sans-serif"), ticksuffix=" "
        ),
        hovermode="closest",
        showlegend=False,
    )
    return {"data": data, "layout": layout}
    # return {"data": None, "layout": None}





import plotly.graph_objects as go
bar_coloway = [
    "#fa4f56",
    "#8dd3c7",
    "#ffffb3",
    "#bebada",
    "#80b1d3",
    "#fdb462",
    "#b3de69",
    "#fccde5",
    "#d9d9d9",
    "#bc80bd",
    "#ccebc5",
    "#ffed6f",
]
def make_original_property_graph(activity_selected, county_pop, forecast_df):
    filtered_activity = df_activity[df_activity["activity"].isin(activity_selected)]
    filtered_activity = filtered_activity.sort_values("danger")

    


    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    # forecast_df = forecast_df.sort_values(by=['prediction_date'])


    base_rate = float(forecast_df['new_confirmed'][forecast_df['prediction_date'] == today_str]) / county_pop * 10000

    bar_fig = []
    former_rate = 0
    total_act_points = 0
    for ds_idx in range(len(activity_selected)):
        total_act_points += list(filtered_activity["danger"])[ds_idx]
        total_rate = np.power(total_act_points * base_rate, 3) 
        partial_rate = total_rate - former_rate
        former_rate = total_rate
        bar_fig.append(
            go.Bar(
                name=list(filtered_activity["activity"])[ds_idx],
                x=["Your risk"],
                y=[partial_rate],
                marker=dict(opacity=0.8, line=dict(color="#ddd")),
                orientation="v",
            )
        )

    fig = go.Figure(
        data=bar_fig,
        layout=dict(
            barmode="stack",
            colorway=bar_coloway,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(traceorder="reversed", font=dict(size=9),
                # yanchor="top",y=0.99,
                # xanchor="left",x=0.01,
            ),
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig














# @app.callback(
#     [Output("data-table", "columns"), Output("data-table", "data")],
#     [Input("activity-select", "value")],
# )
# def update_data_table(subjects, rows, records):
#     columns = [{"name": "Time (hr)", "id": "time", "type": "numeric"}] + [
#         {
#             "name": "Subj{} Conc (uM)".format(subject + 1),
#             "id": str(subject),
#             "type": "numeric",
#         }
#         for subject in range(subjects)
#     ]

#     #   adjust number of rows
#     change = rows - len(records)
#     if change > 0:
#         for i in range(change):
#             records.append({c["id"]: "" for c in columns})
#     elif change < 0:
#         records = records[:rows]

#     #   delete column data if needed
#     valid_column_ids = ["time"] + [str(x) for x in range(subjects)]
#     for record in records:
#         invalid_column_ids = set(record.keys()) - set(valid_column_ids)
#         for col_id in invalid_column_ids:
#             record.pop(col_id)

#     return columns, records

table_header_style = {
    "backgroundColor": "rgb(2,21,70)",
}

test_record = pd.DataFrame.from_dict({'Suggestion':['aaa'],"Content":['bbb']})

import dash_table


df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')

app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(
            id="header",
            children=[
                html.Img(id="logo", src=app.get_asset_url("PAID.png"),style = {"height":"100%"}),
                html.H2(children="Prevention Alarm for Infectious Disease"),
            ],
        ),
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children= [general_risk(), generate_control_card()] + [
                # html.Div(
                #     dash_table.DataTable(
                #     id='table',
                #     columns=[{"name": i, "id": i} for i in df.columns],
                #     data=df.to_dict('records'),
                # )),
                html.Div(
                    dash_table.DataTable(
                        id='data-table',
                        columns=[{"name": i, "id": i} for i in test_record.columns],
                        style_header={'height': 0, 'padding': 0, 'border': 'none'},  # Make headers invisible
                        style_data={'whiteSpace': 'normal'},
                        css=[{'selector': '.dash-cell div.dash-cell-value',
                                        'rule': 'display: inline; font-family:sans-serif; white-space: inherit; text-align: left; overflow: inherit; text-overflow: inherit;'}],
                        data=test_record.to_dict('records'),
                    )
                ),]
        ),
        # Right column
        html.Div(
            id="right-column",
            className="eight columns",
            children=[
                # Patient Volume Heatmap
                html.Div(
                    id="forecast_new_confirm_card",
                    children=[
                        html.B("Daily confirm cases in the county (history and prediction)"),
                        html.Hr(),
                        dcc.Graph(id="forecast_new_confirm_hm"),
                    ],
                ),
                html.Div(
                    id="potential_rate_based_activity",
                    children=[
                        html.B("Your risk during COVID-19"),
                        html.Hr(),
                        dcc.Graph(id="potential_rate-chart")
                    ],
                )

            ]
        ),
    ],
)

suggestions = {
    'a': """social distancing: stay at least 6 feet (about 2 arms’ length) from other people who are not from your household in both indoor and outdoor spaces. """, 
    'b': """masking: wear masks, which have two or more layers, over both mouth and nose in public settings, like on public and mass transportation, at events and gatherings, and anywhere they will be around other people. """,
    'c': """hand washing/sanitizing: Wash your hands often with soap and water for at least 20 seconds especially after you have been in a public place, or after blowing your nose, coughing, or sneezing."""
}

# // Spread happens when an infected person coughs, sneezes, or talks, and droplets from their mouth or nose are launched into the air and land in the mouths or noses of people nearby. The droplets can also be inhaled into the lungs. Social distancing helps limit opportunities to come in contact with contaminated surfaces and infected people outside the home.
# // Masks are recommended as a simple barrier to help prevent respiratory droplets from traveling into the air and onto other people when the person wearing the mask coughs, sneezes, talks, or raises their voice. This is called source control. COVID-19 spreads mainly among people who are in close contact with one another (within about 6 feet), so the use of masks is particularly important in settings where people are close to each other or where social distancing is difficult to maintain. wearing a cloth mask as the minimum is recommended. 
# // Washing hands can keep you healthy and prevent the spread of respiratory and diarrheal infections from one person to the next. During the Coronavirus Disease 19 (COVID-19) pandemic, keeping hands clean is especially important to help prevent the virus from spreading.

@app.callback(
    [Output("data-table", "data")],
    [Input("activity-select", "value")],
)
def update_data_table(activities):
    filtered_activity = df_activity[df_activity["activity"].isin(activities)]
    filtered_activity = filtered_activity.sort_values("danger")
    reconsider = []
    for ds_idx in range(len(activities)):
        if list(filtered_activity["danger"])[ds_idx] >= 6:
            reconsider.append(list(filtered_activity["activity"])[ds_idx])
    records = []
    if len(reconsider) > 0:
        records.append('We suggest you to reconsider these activities since they are with high risk: ' + "; ".join(reconsider))
        
    columns=[
        {
            "name": "Suggestion",
            "id": "advice_index",
            "type": "numeric",
        }
        ,
        {
            "name": "Content",
            "id": "sugg",
            "type": "string",
        }
    ]

    if len(list(filtered_activity['activity'])) >= 1:
        danger_most_activity = list(filtered_activity['activity'])[-1]
        for i in list(list(df_activity[df_activity['activity'] == danger_most_activity]['suggest'])[0]):
            records.append(suggestions[i])

    # #   adjust number of rows
    # change = rows - len(records)
    # if change > 0:
    #     for i in range(change):
    #         records.append({c["id"]: "" for c in columns})
    # elif change < 0:
    #     records = records[:rows]

    records_pd = pd.DataFrame.from_dict({'Suggestion':list(range(1,1+len(records))),"Content":records})

    # records_dict = {}
    # idx = 0
    # for i in records:
    #     records_dict[idx] = i
    #     idx += 1
    # print(records_dict)

    return [records_pd.to_dict('records')]












@app.callback(
    Output("forecast_new_confirm_hm", "figure"),
    [
        Input("state-select", "value"),
        Input("county-select", "value"),
    ],
)
def update_heatmap(state_name, county_name):
    sql = """
        SELECT county_fips_code, prediction_date, new_confirmed, new_confirmed_ground_truth
        FROM `bigquery-public-data.covid19_public_forecasts.county_14d` 
        WHERE state_name="{state_name}"  AND county_name="{county_name}"
        """.format(state_name = state_name, county_name = county_name)
    forecast_df = pandas_gbq.read_gbq(sql, project_id=project_id)
    county_fips_code = forecast_df['county_fips_code'][0]
    county_pop = int(df_population_2019[df_population_2019['fips'] == county_fips_code]['population'])

    # Return to original hm(no colored annotation) by resetting
    try:
        return generate_forecast_heatmap(county_pop, forecast_df)
    except:
        return None



@app.callback(
    Output("potential_rate-chart", "figure"),
    [Input("activity-select", "value"),
        Input("state-select", "value"),
        Input("county-select", "value"),],
)
def update_geodemo_chart(activity_selected, state_name, county_name):
    sql = """
        SELECT county_fips_code, prediction_date, new_confirmed, new_confirmed_ground_truth
        FROM `bigquery-public-data.covid19_public_forecasts.county_14d` 
        WHERE state_name="{state_name}"  AND county_name="{county_name}"
        """.format(state_name = state_name, county_name = county_name)
    forecast_df = pandas_gbq.read_gbq(sql, project_id=project_id)
    county_fips_code = forecast_df['county_fips_code'][0]
    county_pop = int(df_population_2019[df_population_2019['fips'] == county_fips_code]['population'])
    try:
        return make_original_property_graph(activity_selected, county_pop, forecast_df)
    except:
        return None




# Run the server
if __name__ == "__main__":
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0', port=8080, debug=True)
