from os.path import dirname, join
import numpy as np
from bokeh.plotting import figure, curdoc
from bokeh.layouts import layout, Column
from bokeh.models import ColumnDataSource, Div
from bokeh.models.widgets import DateRangeSlider, Select, RadioButtonGroup, Slider, TextInput
from datetime import date
from exp_packages.SQLExecutor import SQLExecutor
from exp_packages.utils import *
from exp_packages.load_spinning import spinner_script


def datetime(x):
    return np.array(x, dtype=np.datetime64)


desc = Div(text=open(join(dirname(__file__), "description.html")).read(), sizing_mode="stretch_width")


# Database Essentials
server, username, password, database = get_database_info_from_config('./exp.conf')
executor = SQLExecutor(server, username, password, database)
executor.connect()
data_date = [d[:10] for d in executor.fetch(timeIntervalOnly=True)]
date_form = lambda d: date(*map(int, d.split('-')))

# Widgets
mb_btnGroup = RadioButtonGroup(name="mb_btngroup",
                               labels=["less than", "disable", "greater than"],
                               active=1,
                               margin=(0, 0, 20, 0))
mb_slider = Slider(title="Marginal Balance Change Ratio (%)", start=-100, end=100, value=0, step=10)
cp_btnGroup = RadioButtonGroup(name="cp_btngroup",
                               labels=["less than", "disable", "greater than"],
                               active=1,
                               margin=(0, 0, 20, 0))
cp_slider = Slider(title="Closing Price Change Ratio (%)", start=-100, end=100, value=0, step=10)
date_range_slider = DateRangeSlider(title="Date range", value=(date_form(data_date[20]), date_form(data_date[-20])),
                                    start=date_form(data_date[0]), end=date_form(data_date[-1]), step=1)
stock_code_input = TextInput(title="Stock Code")
stock_name_input = TextInput(title="Stock Name")
stock_selector = Select(title="Choose Stock to Plot")
option_btnGroup = RadioButtonGroup(name="Data Type",
                                   labels=["Marginal Balance", " Closing Price "],
                                   active=0)

source = ColumnDataSource(data={"date": [], "price": []})
TOOLTIPS = [
    ("Title", "@title"),
    ("Date", "@date"),
    ("Price", "@price")
]
p = figure(x_axis_type="datetime",
           plot_height=500,
           plot_width=600,
           title="",
           toolbar_location=None,
           tooltips=TOOLTIPS,
           sizing_mode="scale_both")
p.grid.grid_line_alpha = 0.3
p.xaxis.axis_label = "Date"
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label = "Price"
p.yaxis.axis_label_text_font_style = "bold"
p.line(x="date", y="price", source=source, color="#33A02C")


def select_stocks():
    selected_stock_code = stock_selector.value[:6]
    result = executor.fetch(constraint={"StockCode": " = '{}' ".format(selected_stock_code)})

    idx = 3 if option_btnGroup.active == 0 else 4
    data = {
        "date": datetime([r[2][:10] for r in result]),
        "price": [r[idx] for r in result],
    }
    source.data.update(ColumnDataSource(data).data)


def sql_result_to_dict(result):
    ret = {result[i][0]: list() for i in range(len(result))}
    for i in range(len(result)):
        ret[result[i][0]].append(result[i])
    return ret


def update():
    query = dict()
    query["StockCode"] = "LIKE '%{}%'".format(stock_code_input.value) if stock_code_input.value != "" else "LIKE '%%'"
    query["StockName"] = "LIKE '%{}%'".format(stock_name_input.value) if stock_name_input.value != "" else "LIKE '%%'"
    sql_result = executor.fetch(constraint=query)
    sql_dict = sql_result_to_dict(sql_result)

    if cp_btnGroup.active != 1:
        operator = ["<", None, ">"][cp_btnGroup.active]
        ratio = lambda stock_data_list: (get_fist_positive_closing_value(stock_data_list) - stock_data_list[-1][
            -1]) / \
                                        get_fist_positive_closing_value(stock_data_list)
        filtered_dict = {
            stock: sql_dict[stock]
            for stock in sql_dict
            if eval(str(100 * ratio(sql_dict[stock])) + operator + str(cp_slider.value))
        }
        sql_dict = filtered_dict
    if mb_btnGroup.active != 1:
        operator = ["<", None, ">"][mb_btnGroup.active]
        ratio = lambda stock_data_list: (get_fist_positive_marginal_balance(stock_data_list) - stock_data_list[-1][
            -2]) / \
                                        get_fist_positive_marginal_balance(stock_data_list)
        filtered_dict = {
            stock: sql_dict[stock]
            for stock in sql_dict
            if eval(str(100 * ratio(sql_dict[stock])) + operator + str(mb_slider.value))
        }
        sql_dict = filtered_dict
    stock_selector.options = ["{} - {}".format(key, sql_dict[key][0][1]) for key in sql_dict]
    select_stocks()


controls = [mb_slider, mb_btnGroup, cp_slider, cp_btnGroup, date_range_slider, stock_code_input, stock_name_input,
            stock_selector, option_btnGroup]
btngroups = [cp_btnGroup, mb_btnGroup, option_btnGroup]
ssgroups = [c for c in controls if c not in btngroups]
for control in ssgroups:
    control.on_change('value', lambda attr, old, new: update())
for control in btngroups:
    control.on_change('active', lambda attr, old, new: update())
stock_selector.on_change('value', lambda attr, old, new: select_stocks())

inputs = Column(*controls, width=320, height=600)
inputs.sizing_mode = "fixed"

l = layout([
    [desc],
    [inputs, p]
], sizing_mode="scale_both")

curdoc().add_root(l)
curdoc().title = "An Interactive Stock Explorer for Stock Data"
