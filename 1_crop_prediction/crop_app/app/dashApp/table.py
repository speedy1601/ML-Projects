import polars as pl
from dash import Dash, html, dash_table
import os

cur_folder = os.path.dirname(os.path.realpath(__file__))
DATASET_PATH = os.path.join(cur_folder, "unique_crops_sample.csv")

crops:pl.DataFrame = pl.read_csv(source = DATASET_PATH).sort(by='crop_name')

app = Dash(__name__, requests_pathname_prefix="/dashboard/")

app.layout = html.Div(
    id = 'dashApp',
    children = [
        html.H1(id = 'firstH1', children = "Sample Data Table for 22 unique crops"),
        dash_table.DataTable(id = 'table1', data = crops.to_pandas().to_dict(orient = 'records')),
    ],
)

if __name__ == '__main__':
    app.run(debug=True)