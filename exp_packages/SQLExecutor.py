import pymysql


class SQLExecutor:
    db = None
    cursor = None

    def __init__(self, server, username, passwd, database):
        self.server = server
        self.username = username
        self.passwd = passwd
        self.database = database

    def connect(self):
        print("[INFO] Connecting to database...")
        try:
            self.db = pymysql.connect(
                self.server,
                self.username,
                self.passwd,
                self.database)

            self.cursor = self.db.cursor()

        except Exception as e:
            print("SQLExecutor catched an error: {}".format(e))
            exit(1)

        print("[INFO] Database connected!")

    def close(self):
        if self.db:
            self.db.close()
            print("[INFO] Database closed.")

    def create_database_table(self):
        print("[INFO] Initializing Database Table...")
        self.cursor.execute("DROP TABLE IF EXISTS StockData")
        self.cursor.execute("CREATE TABLE StockData ("
                            "StockCode int, "
                            "StockName varchar(100),"
                            "DataDate varchar(100),"
                            "MarginBalance double(100,2),"
                            "ClosingPrice double(100,2));")

    def exec(self, data):
        print("[INFO] Inserting Fetched Data to Local...")

        try:
            self.cursor.executemany(
                "INSERT INTO StockData(StockCode, StockName, DataDate, MarginBalance, ClosingPrice)VALUES(%s,%s,%s,%s,%s);",
                data)

        except Exception as e:
            print("SQLExecutor catched an error: {}".format(e))
