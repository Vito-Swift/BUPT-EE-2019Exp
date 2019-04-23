from bokeh.io import output_file, show
from bokeh.core.properties import value
from bokeh.layouts import layout
from bokeh.plotting import figure, curdoc
from bokeh.layouts import widgetbox, column, row
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Button, RadioButtonGroup, Select, TextInput, RadioGroup
from bokeh.models.widgets import DataTable, TableColumn, Panel, Tabs, Paragraph
from bokeh.transform import dodge
from functools import partial
from exp_packages.utils import *
import numpy as np
import pandas as pd


def datetime(x):
    return np.array(x, dtype=np.datetime64)


class QueryPage:
    page_width = 600
    section_width = 600
    semi_width = 225
    button_width = 600
    layout = None
    searchGrowthRate = False
    searchStockCode = True
    executor = None
    title = "Stock Statistic System - Query Page"

    def __init__(self, executor):
        """
        Declaration of widgets and database interfaces
        :param executor: SQLExecutor Instance
        """
        self.executor = executor
        self.btngroup_growth_rate = None
        self.growth_rate_input = None
        self.start_time_select = None
        self.end_time_select = None
        self.optiongroup_stock = None
        self.stock_input = None
        self.btn_search = None
        self.dataTable = None
        self.date = None
        self.source = ColumnDataSource({"date": [], "cpdata": [], "mbdata": []})

    def initUI(self):
        """
        Initialization of widgets, layouts and events in the Query Page
        :return: None
        """

        # Fetch The List of Available Dates
        self.date = [d[:10] for d in self.executor.fetch(timeIntervalOnly=True)]

        # Growth Constraint Section
        self.btngroup_growth_rate = RadioButtonGroup(name="growth_rate", active=1,
                                                     labels=["less than", "equal to", "more than"],
                                                     width=self.section_width)
        self.growth_rate_input = TextInput(value="", width=self.section_width)
        self.growth_rate_input.on_change('value', self.__changeGrowthRate)
        self.start_time_select = Select(title="Start at", options=self.date,
                                        value=self.date[-30], width=self.semi_width)
        self.end_time_select = Select(title="End at", options=self.date,
                                      value=self.date[-1], width=self.semi_width, align="end")

        # Stock Search Section
        self.optiongroup_stock = RadioGroup(labels=["Stock Code", "Stock Name"],
                                            active=0,
                                            width=self.section_width,
                                            inline=True)
        self.optiongroup_stock.on_change('active', self.__changeSearchType)
        self.stock_input = TextInput(value="", width=self.section_width)

        # Search Button
        self.btn_search = Button(label="Search", width=self.button_width, margin=(0, 0, 20, 0), button_type="primary")
        self.btn_search.on_click(self.__search)

        # Data Table
        column = [
            TableColumn(field="stock_code", title="Stock Code"),
            TableColumn(field="stock_name", title="Stock Name")
        ]
        self.dataTable = DataTable(source=ColumnDataSource(),
                                   columns=column,
                                   width=self.page_width,
                                   height=200)
        self.dataTable.source.selected.on_change('indices', self.__select_row)

        # Closing Price Plotting
        p_closing_price = figure(x_axis_type="datetime",
                                 plot_width=800,
                                 title="Stock Closing Prices")
        p_closing_price.grid.grid_line_alpha = 0.3
        p_closing_price.xaxis.axis_label = "Date"
        p_closing_price.xaxis.axis_label_text_font_style = "bold"
        p_closing_price.yaxis.axis_label = "Price"
        p_closing_price.yaxis.axis_label_text_font_style = "bold"

        p_closing_price.line(x='date', y='cpdata', source=self.source, color='#33A02C')

        # Query Page Layout
        self.layout = layout([
            [
                widgetbox(
                    Paragraph(
                        text="Advanced Search",
                        style={"font-weight": "bold"}
                    ),
                    self.stock_input,
                    self.optiongroup_stock,
                    margin=(20, 0, 10, 0)
                )
            ],

            [
                widgetbox(
                    Paragraph(
                        text="Search by Growth Rate % (It takes a while to find result. Left empty to disable)",
                        style={"font-weight": "bold"},
                        width=self.section_width),
                    self.growth_rate_input,
                    self.btngroup_growth_rate,
                    row([
                        self.start_time_select,
                        self.end_time_select,
                    ]),
                    margin=(10, 0, 0, 0))],

            [widgetbox(self.btn_search)],

            [widgetbox(self.dataTable)],

            [widgetbox(p_closing_price)],
        ],

            width=self.page_width)

    def __changeSearchType(self, attr, old, new):
        self.searchStockCode = [True, False][new]

    def __changeGrowthRate(self, attr, old, new):
        self.searchGrowthRate = False if new == "" else True

    def __search(self):
        if self.stock_input.value != "":
            col = "StockCode" if self.searchStockCode else "StockName"
            query = {col: "LIKE '%{}%'".format(self.stock_input.value),
                     "DataDate": "BETWEEN '{}' AND '{}'".format(self.start_time_select.value,
                                                                self.end_time_select.value)}
            sql_result = self.executor.fetch(True, False, constraint=query)
        else:
            sql_result = self.executor.fetch(True, False)

        if self.searchGrowthRate:
            operator = ["<", "==", ">"][self.btngroup_growth_rate.active]
            code_list = filter_growth_rate(sql_result,
                                           self.start_time_select.value,
                                           self.end_time_select.value,
                                           self.executor,
                                           operator,
                                           self.growth_rate_input.value)
            sql_result = {code: sql_result[code] for code in code_list}

        dataSource = {
            "stock_code": [code for code in sql_result],
            "stock_name": [sql_result[code] for code in sql_result]
        }
        self.dataTable.source.data = dataSource

    def __select_row(self, attr, old, new):
        try:
            selected_index = self.dataTable.source.selected.indices[0]
            selected_stock_code = str(self.dataTable.source.data["stock_code"][selected_index])
            result = self.executor.fetch(constraint={"StockCode": " = '{}' ".format(selected_stock_code),
                                                     "DataDate": "BETWEEN '{}' AND '{}'".format(
                                                         self.start_time_select.value, self.end_time_select.value)})
            data = {
                "date": datetime([r[2][:10] for r in result]),
                "cpdata": [r[4] for r in result],
                "mbdata": [r[3] for r in result]
            }

            self.__draw(data)

        except IndexError:
            pass

    def __draw(self, src):
        print(src)
        self.source.data.update(ColumnDataSource(src).data)


class DataVisualizer:

    def __init__(self, executor):
        self.executor = executor
        self.__query_page = QueryPage(executor)

    def launch(self):
        self.__query_page.initUI()
        curdoc().add_root(self.__query_page.layout)
