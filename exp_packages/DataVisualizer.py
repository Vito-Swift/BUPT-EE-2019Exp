from bokeh.io import output_file, show
from bokeh.core.properties import value
from bokeh.layouts import layout
from bokeh.plotting import figure, curdoc
from bokeh.layouts import widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Button, RadioButtonGroup, Select, TextInput, RadioGroup
from bokeh.models.widgets import DataTable, TableColumn, Panel, Tabs, Paragraph
from bokeh.transform import dodge
from functools import partial


class QueryPage:
    page_width = 800
    layout = None
    searchGrowthRate = False
    searchStockCode = True
    executor = None
    title = "Stock Statistic System - Query Page"

    def __init__(self, executor):
        self.executor = executor
        self.btngroup_growth_rate = None
        self.growth_rate_input = None
        self.start_time_select = None
        self.end_time_select = None
        self.optiongroup_stock = None
        self.stock_input = None
        self.btn_search = None
        self.dataTable = None

    def initUI(self, date):
        """
        Initialization of widgets, layouts and events in the Query Page
        :param date: list of available dates
        :return: None
        """
        # Growth Constraint Section
        self.btngroup_growth_rate = RadioButtonGroup(name="growth_rate",
                                                     active=1,
                                                     labels=["less than", "equal to", "more than"])
        self.growth_rate_input = TextInput(value="", title="Growth Rate % (left empty to disable):")
        self.growth_rate_input.on_change('active', partial(self.__changeSearchType, "GrowthRate", TextInput.value))
        self.start_time_select = Select(title="Start at",
                                        options=date,
                                        value=date[0])
        self.end_time_select = Select(title="End at",
                                      options=date,
                                      value=date[-1])

        # Stock Search Section
        self.optiongroup_stock = RadioGroup(lables=["Stock Code", "Stock Name"],
                                            active=0,
                                            width=100,
                                            inline=True)
        self.optiongroup_stock.on_change('active', partial(self.__changeSearchType, "Stock"))
        self.stock_input = TextInput(value="")

        # Search Button
        self.btn_search = Button(label="Search")
        self.btn_search.on_click(self.__search)

        # Data Table
        column = [
            TableColumn(field="stock_code", title="Stock Code"),
            TableColumn(field="stock_name", title="Stock Name")
        ]
        self.dataTable = DataTable(source=ColumnDataSource(),
                                   solumns=column,
                                   width=self.page_width,
                                   height=200)

        # Page Layout
        self.layout = layout([
            [widgetbox(
                self.growth_rate_input,
                self.start_time_select,
                self.end_time_select,
                self.btngroup_growth_rate
            )],
            [widgetbox(
                self.optiongroup_stock,
                self.stock_input
            )],
            [widgetbox(
                self.dataTable
            )],
            [widgetbox(
                self.btn_search
            )]
        ])

    def __changeSearchType(self, option_type, option_arg=""):
        if option_type == "Stock":
            self.searchStockCode = not self.searchStockCode
        elif option_type == "GrowthRate":
            self.searchGrowthRate = False if option_arg == "" else True

    def __search(self):
        criteria = dict()
        sql_result = list()

        if self.stock_input.value != "":
            col = "StockCode" if self.searchStockCode else "StockName"
            query = {col: self.stock_input.value}
            sql_result = self.executor.fetch(query)


class TabularPage:
    layout = None
    title = "Stock Statistic System - Tabular"

    def initUI(self):
        pass
