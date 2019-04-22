from exp_packages.SQLExecutor import SQLExecutor
from exp_packages.utils import *


def main():
    print("************INITIALIZING DATABASE*****************")
    server, username, password, database = get_database_info_from_config('./exp.conf')
    executor = SQLExecutor(server, username, password, database)
    executor.connect()
    executor.create_database_table()

    print("************FETCHING DATA TO LOCAL****************")
    stock_dict = get_stock_dict('./stocklist.xls', 'StockList')
    request_url = get_request_url_from_config('./exp.conf')
    result = get_fetched_data(stock_dict, request_url)
    for stock in result:
        executor.exec(stock)

    print("**************DATA VISUALIZATION*****************")


if __name__ == '__main__':
    main()
