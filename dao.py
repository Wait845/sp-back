import pymysql
import configuration


# 读取配置
config = configuration.config
IP = config.get('database', 'ip')
PORT = config.get('database', 'port')
USER = config.get('database', 'user')
PASSWORD = config.get('database', 'password')
DATABASE = config.get('database', 'database')

class DataAccess():
    def __init__(self) -> None:
        self.conn = pymysql.connect(
            host=IP,
            user=USER,
            passwd=PASSWORD,
            database=DATABASE
        )
    def execute(self, sql):
        if self.conn.open:
            self.cursor = self.conn.cursor()
        else:
            return None

        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            return None
        finally:
            if self.cursor:
                self.cursor.close()

    def __del__(self):
        if self.conn.open:
            self.conn.close()

# dao = DataAccess()
# print(dao.execute("select timestamp from detect_stream where id = 653;"))