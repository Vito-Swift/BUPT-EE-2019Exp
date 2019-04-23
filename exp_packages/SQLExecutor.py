import pymysql


class SQLExecutor:
    db = None
    cursor = None
    isConnected = False

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
                self.database,
                charset="utf8")

            self.isConnected = True
            self.cursor = self.db.cursor()
            self.cursor.execute("ALTER DATABASE {} CHARACTER SET utf8".format(self.database))

        except Exception as e:
            print("SQLExecutor caught an error: {}".format(e))
            exit(1)

        print("[INFO] Database connected!")

    def close(self):
        if self.isConnected:
            self.db.close()
            self.isConnected = False
            print("[INFO] Database closed.")

    def create_database_table(self):
        if self.isConnected:
            print("[INFO] Initializing Database Table...")
            self.cursor.execute("DROP TABLE IF EXISTS StockData")
            self.cursor.execute("CREATE TABLE StockData ("
                                "StockCode int, "
                                "StockName varchar(100),"
                                "DataDate varchar(100),"
                                "MarginBalance double(100,2),"
                                "ClosingPrice double(100,2));")
            self.cursor.execute("ALTER TABLE StockData CONVERT TO CHARACTER SET utf8")
        else:
            print("SQLExecutor caught an error: did not connect to database server")

    def exec(self, data):
        try:
            self.cursor.executemany(
                "INSERT INTO StockData(StockCode, StockName, DataDate, MarginBalance, ClosingPrice)VALUES(%s,%s,%s,%s,%s);",
                data)

        except Exception as e:
            print("SQLExecutor catched an error: {}".format(e))

        self.db.commit()

    def fetch(self, stockNameOnly=False, timeIntervalOnly=False, **kargs):
        if self.isConnected:
            query = "SELECT * FROM StockData WHERE 1"

            if "constraint" in kargs:
                for col, con in kargs["constraint"].items():
                    query += " AND ({} {})".format(col, con)

            self.cursor.execute(query + " ORDER BY DataDate;")
            result = self.cursor.fetchall()

            if stockNameOnly:
                ret = {}
                return {result[i][0]: result[i][1]
                        for i in range(len(result))
                        if result[i][0] not in ret
                        }

            if timeIntervalOnly:
                ret = []
                for r in result:
                    if r[2] not in ret:
                        ret.append(r[2])

                return ret

            else:
                return result

        else:
            print("SQLExecutor caught an error: did not connect to database server")
