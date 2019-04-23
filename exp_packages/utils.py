import json
import requests
import xlrd
import re
import configparser
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
import gevent
from gevent import monkey


def print_time_stamp(prefix="", end='\n', noise=True):
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y-%H:%M:%S")
    if noise:
        print(prefix + date_time, end=end)
    else:
        return prefix + date_time


def get_fist_positive_closing_value(l):
    for x in l:
        if x[-1] > 0:
            return x[-1]
    return 1


def get_fist_positive_marginal_balance(l):
    for x in l:
        if x[-2] > 0:
            return x[-2]
    return 1


def get_database_info_from_config(path):
    print("[INFO] Collecting Database Info from Config:{}".format(path))
    config = configparser.ConfigParser()

    try:
        configfile = open(path, 'r')
        config.read_file(configfile)
    except Exception as e:
        print("[ERROR] Fail to Open Config File: {}".format(e))

    return (config['DATABASE']['Server'],
            config['DATABASE']['Username'],
            config['DATABASE']['Password'],
            config['DATABASE']['Database'])


def get_request_url_from_config(path):
    print("[INFO] Collecting Request URL from Config:{}".format(path))
    config = configparser.RawConfigParser()

    try:
        configfile = open(path, 'r')
        config.read_file(configfile)
    except Exception as e:
        print("[ERROR] Fail to Open Config File: {}".format(e))

    return config['DEFAULT']['URL']


def get_stock_dict(filename, sheetname):
    print("[INFO] Collecting StockList from Excel:{}".format(sheetname))

    workbook = xlrd.open_workbook(filename)
    worksheet = workbook.sheet_by_name(sheetname)

    ret = zip(
        [worksheet.cell(r, 0).value for r in range(worksheet.nrows)],
        [worksheet.cell(r, 1).value for r in range(worksheet.nrows)])

    return dict(ret)


def get_fetched_data(stock_list, url, process_num=100):
    pool = ThreadPool(process_num)
    stock_num = len(stock_list)
    count = 1

    def get_result(stock_code, stock_name, api, count):
        print("[INFO] {}\tFetching Stock Data from Website\tTaskID: {}/{}\t{}".format(
            print_time_stamp(noise=False),
            count,
            stock_num,
            stock_name))

        is_fetched = False
        while not is_fetched:
            try:
                r = requests.get(api)
                json_str = json.dumps(r.text)
                is_fetched = True
            except Exception as e:
                print("[Warning] Cannot Fetch One Stock: {}\t{}".format(stock_name, e))
                print("Retry Fetching...")

        try:
            ret = list()
            stock_data = eval(json.loads(json_str))

            for snapshot in stock_data:
                ret.append([
                    stock_code,
                    stock_name,
                    re.sub(r"(T)", r" ", snapshot["tdate"]),
                    snapshot["rzrqye"],
                    snapshot["close"] if snapshot["close"] != "-" else 0
                ])

            return ret

        except Exception as e:
            print("[Warning] Cannot Fetch One Stock: {}\t{}".format(stock_name, e))

    argv_list = []
    for stock_code, stock_name in stock_list.items():
        api = re.sub(r'(%27%27)', r'%27{}%27'.format(stock_code), url)
        argv_list.append([stock_code, stock_name, api, count])
        count += 1

    ret = pool.starmap(get_result, argv_list)
    pool.close()
    pool.join()

    return ret


def filter_growth_rate(stock_list, ldate, rdate, executor, operator, bound):
    monkey.patch_socket()

    ratio = lambda stock_data_list: (get_fist_positive_closing_value(stock_data_list) - stock_data_list[-1][
        -1]) / \
                                    get_fist_positive_closing_value(stock_data_list)

    def is_valid_result(stock_code, ldate, rdate, executor, operator, bound):
        return stock_code if eval(
            str(100 * ratio(executor.fetch(constraint={"StockCode": " = '{}' ".format(stock_code),
                                                       "DataDate": "BETWEEN '{}' AND '{}'".format(
                                                           ldate, rdate)}))) +
            operator +
            bound
        ) else None

    jobs_list = []
    for stock_code in stock_list:
        jobs_list.append(gevent.spawn(
            is_valid_result,
            stock_code, ldate, rdate, executor, operator, bound
        ))
    gevent.joinall(jobs_list, timeout=10)

    return [r.value for r in jobs_list if r.value]
