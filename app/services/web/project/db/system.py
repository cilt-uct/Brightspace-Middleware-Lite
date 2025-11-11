from datetime import datetime
from mysql.connector import connection, Error

import MySQLdb.cursors

class System(object):
    def __init__(self, client) -> None:
        self._client = client

    def get_users(self, start:int = 0,
                        length:int = 20,
                        draw:int = 1,
                        order_column:str = '',
                        order_dir:str = 'asc',
                        search_st:str = '',
                        search_regex:bool = False):

        result = {'draw' : int(draw), "recordsTotal": 0, "recordsFiltered": 0, "data":[] }
        try:
            with self._client.mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                search_sql = ''

                if search_st:
                    search_sql = """where ( LOCATE(%(search_st)s, name) or LOCATE(%(search_st)s, username)) """

                cursor.execute('SELECT count(*) as c FROM system_user')
                result['recordsTotal'] = cursor.fetchone()['c']

                cursor.execute(f'SELECT count(*) as c FROM system_user {search_sql}', {'search_st': search_st})
                result['recordsFiltered'] = cursor.fetchone()['c']

                final_sql = f"""SELECT `id` as "DT_RowId", `id`, `name`, `username` as `username`,
                                        DATE_FORMAT(`created_on`, %(dt)s) as `created_on`,
                                        DATE_FORMAT(`last_login`, %(dt)s) as `last_login`,
                                        `login_count`, `is_active`
                                    FROM system_user
                                    {search_sql}
                                    order by `{order_column}` {order_dir}
                                    limit %(start)s, %(length)s """
                cursor.execute(final_sql, {'start': start, 'length': length, 'search_st': search_st, 'dt': '%Y-%m-%d %H:%i:%S'})
                result['data'] = cursor.fetchall()

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)

        return result
