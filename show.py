from exp_packages.DataVisualizer import DataVisualizer
from exp_packages.SQLExecutor import SQLExecutor
from exp_packages.utils import *

print("[MESSAGE] Connecting to Local Database")
server, username, password, database = get_database_info_from_config('./exp.conf')
executor = SQLExecutor(server, username, password, database)
executor.connect()

print("[MESSAGE] Emitting Data Visualization")
query_page = DataVisualizer(executor)
query_page.launch()
