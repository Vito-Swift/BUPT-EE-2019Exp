from os.path import dirname, join
import numpy as np
import time
from bokeh.plotting import figure, curdoc
from bokeh.layouts import layout, Column
from exp_packages.utils import *
from bokeh.models.callbacks import CustomJS
from exp_packages.loadingOverlay import loadingOverlay_js
from bokeh.models import ColumnDataSource, Div, Range1d, LinearAxis
from bokeh.models.widgets import DateRangeSlider, Select, RadioButtonGroup, Slider, TextInput
from datetime import date
from exp_packages.SQLExecutor import SQLExecutor

query_loading_spinning = CustomJS(args=dict(), code=loadingOverlay_js + """
var spinHandle = loadingOverlay.activate();
setTimeout(function() {
   loadingOverlay.cancel(spinHandle);
},2000);
""")
slider_loading_spinning = CustomJS(args=dict(), code=loadingOverlay_js + """
var spinHandle = loadingOverlay.activate();
setTimeout(function() {
   loadingOverlay.cancel(spinHandle);
},4000);
""")
plot_loading_spinning = CustomJS(args=dict(), code=loadingOverlay_js + """
var spinHandle = loadingOverlay.activate();
setTimeout(function() {
   loadingOverlay.cancel(spinHandle);
},200);
""")


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
show_btnGroup = RadioButtonGroup(name="Loading",
                                 labels=["show", "hide"],
                                 active=1)
mb_btnGroup = RadioButtonGroup(name="mb_btngroup",
                               labels=["less than", "disable", "greater than"],
                               active=1,
                               margin=(0, 0, 20, 0))
mb_slider = Slider(title="Marginal Balance Change Ratio (%)", start=-100, end=100, value=0, step=10)
cp_btnGroup = RadioButtonGroup(name="cp_btngroup",
                               labels=["less than", "disable", "greater than"],
                               active=1,
                               margin=(0, 0, 20, 0))
cp_slider = Slider(title="Closing Price Change Ratio (%)", start=-100, end=100, value=0, step=10, )
date_range_slider = DateRangeSlider(title="Date range", value=(date_form(data_date[20]), date_form(data_date[-20])),
                                    start=date_form(data_date[0]), end=date_form(data_date[-1]), step=1)
stock_code_input = TextInput(title="Stock Code")
stock_name_input = TextInput(title="Stock Name")
stock_selector = Select(title="Choose Stock to Plot")

mb_source = ColumnDataSource(data={"date": [], "price": []})
cp_source = ColumnDataSource(data={"date": [], "price": []})

TOOLTIPS = [
    ("Title", "@title"),
    ("Date", "@date_str"),
    ("Price", "@price")
]
p = figure(x_axis_type="datetime",
           plot_height=500,
           plot_width=600,
           title="",
           toolbar_location=None,
           tools="",
           tooltips=TOOLTIPS,
           sizing_mode="scale_both")
p.grid.grid_line_alpha = 0.3
p.xaxis.axis_label = "Date"
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label = "Marginal Balance"
p.yaxis.axis_label_text_font_style = "bold"
p.left[0].formatter.use_scientific = False
p.line(x="date", y="price", source=mb_source, color="#33A02C", legend="Marginal Balance")
p.extra_y_ranges = {"closing_price": Range1d(start=-100, end=100)}
p.add_layout(LinearAxis(y_range_name="closing_price", axis_label_text_font_style="bold", axis_label="Closing Price"),
             "right")
p.line(x="date", y="price", source=cp_source, y_range_name="closing_price", color="orange", line_width=1.5,
       legend="Closing Price")


def select_stocks():
    selected_stock_code = stock_selector.value[:6]
    result = list(executor.fetch(constraint={"StockCode": " = '{}' ".format(selected_stock_code)}))

    for i in range(len(result)):
        if result[i][-1] == 0 or result[i][-2] == 0:
            result.pop(i)

    mb_data = {
        "title": ["Marginal Balance"] * len(result),
        "date": datetime([r[2][:10] for r in result]),
        "date_str": [r[2][:10] for r in result],
        "price": [r[3] for r in result],
    }
    cp_data = {
        "title": ["Closing Price"] * len(result),
        "date": datetime([r[2][:10] for r in result]),
        "date_str": [r[2][:10] for r in result],
        "price": [r[4] for r in result],
    }

    p.extra_y_ranges["closing_price"].start = int(min(cp_data["price"])) - 5
    p.extra_y_ranges["closing_price"].end = int(max(cp_data["price"])) + 5

    mb_source.data.update(ColumnDataSource(mb_data).data)
    cp_source.data.update(ColumnDataSource(cp_data).data)


def sql_result_to_dict(result):
    ret = {result[i][0]: list() for i in range(len(result))}
    for i in range(len(result)):
        ret[result[i][0]].append(result[i])
    return ret


last_slide_time = time.time()


def slider_latency():
    global last_slide_time
    if time.time() - last_slide_time > 1.5:
        last_slide_time = time.time()
        update()


def update():
    show_btnGroup.active = 0

    if isinstance(date_range_slider.value[0], (int, float)):
        start_date, end_date = time.strftime('%Y-%m-%d', time.localtime(date_range_slider.value[0] / 1000)), \
                               time.strftime('%Y-%m-%d', time.localtime(date_range_slider.value[1] / 1000))
    else:
        start_date, end_date = date_range_slider.value

    query = dict()
    query["StockCode"] = "LIKE '%{}%'".format(stock_code_input.value) if stock_code_input.value != "" else "LIKE '%%'"
    query["StockName"] = "LIKE '%{}%'".format(stock_name_input.value) if stock_name_input.value != "" else "LIKE '%%'"
    query["DataDate"] = "BETWEEN '{}' AND '{}'".format(start_date, end_date)

    sql_result = executor.fetch(constraint=query)
    sql_dict = sql_result_to_dict(sql_result)

    if cp_btnGroup.active != 1:
        operator = ["<", None, ">"][cp_btnGroup.active]
        ratio = lambda stock_data_list: (- get_fist_positive_closing_value(
            stock_data_list) + get_last_positive_closing_value(stock_data_list)) / \
                                        get_fist_positive_closing_value(stock_data_list)

        filtered_dict = {
            stock: sql_dict[stock]
            for stock in sql_dict
            if ratio(sql_dict[stock]) != 0 and
               eval(str(100 * ratio(sql_dict[stock])) + operator + str(cp_slider.value))
        }
        sql_dict = filtered_dict

    if mb_btnGroup.active != 1:
        operator = ["<", None, ">"][mb_btnGroup.active]
        ratio = lambda stock_data_list: (- get_fist_positive_marginal_balance(
            stock_data_list) + get_last_positive_marginal_balance(stock_data_list)) / \
                                        get_fist_positive_marginal_balance(stock_data_list)
        filtered_dict = {
            stock: sql_dict[stock]
            for stock in sql_dict
            if ratio(sql_dict[stock]) != 0 and
               eval(str(100 * ratio(sql_dict[stock])) + operator + str(mb_slider.value))
        }
        sql_dict = filtered_dict
    stock_selector.options = ["{} - {}".format(key, sql_dict[key][0][1]) for key in sql_dict]

    if stock_selector.options:
        stock_selector.value = stock_selector.options[0]
        select_stocks()

    show_btnGroup.active = 1


controls = [mb_slider, mb_btnGroup, cp_slider, cp_btnGroup, date_range_slider, stock_code_input, stock_name_input,
            stock_selector]
btngroups = [cp_btnGroup, mb_btnGroup]
ssgroups = [stock_code_input, stock_name_input]
slidergroups = [mb_slider, cp_slider, date_range_slider]

for control in slidergroups:
    control.callback_policy = 'mouseup'
    control.callback = query_loading_spinning
    control.on_change('value', lambda attr, old, new: slider_latency())

for control in ssgroups:
    control.on_change('value', lambda attr, old, new: update())
    control.js_on_change('value', query_loading_spinning)

for control in btngroups:
    control.on_change('active', lambda attr, old, new: update())
    control.js_on_change('active', query_loading_spinning)

stock_selector.on_change('value', lambda attr, old, new: select_stocks())
stock_selector.js_on_change('value', plot_loading_spinning)
update()

inputs = Column(*controls, width=320, height=600)
inputs.sizing_mode = "fixed"

l = layout([
    [desc],
    [inputs, p]
], sizing_mode="stretch_both")

curdoc().add_root(l)
curdoc().title = "An Interactive Explorer for Stock Data"
