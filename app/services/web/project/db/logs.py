import MySQLdb.cursors


class Logs:

    def __init__(self, client) -> None:
        self._client = client

    def get_logs(self, active_status:list = [],
                        start:int = 0,
                        length:int = 20,
                        draw:int = 1,
                        order_column:str = '',
                        order_dir:str = 'asc',
                        search_st:str = '',
                        search_regex:bool = False):

        result = {'draw' : int(draw), 'recordsTotal': 0, 'recordsFiltered': 0, 'data':[] }
        try:
            with self._client.mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                filter_where, search_where = [], []
                filter_ar, search_ar = {}, {}

                # setup filters:
                if 'All' in active_status or 'all' in active_status:
                    pass # let's just show all of it
                else:
                    filter_ar['status'] = tuple(active_status)
                    filter_where.append('concat(left(`status`,1),"xx") in %(status)s')

                # setup search
                if search_st:
                    search_ar['search_st'] = search_st
                    search_where.append("""( LOCATE(%(search_st)s, request) or
                                            LOCATE(%(search_st)s, result) or
                                            LOCATE(%(search_st)s, status))""")


                # get full count with search filters used
                search_sql = 'where {}'.format(' and '.join(filter_where)) if filter_where else ''
                cursor.execute(f'SELECT count(*) as c FROM call_log {search_sql}', filter_ar)
                result['recordsTotal'] = cursor.fetchone()['c']

                # get filtered count with search filters used
                search_sql = ''
                if (filter_where + search_where):
                    search_sql = 'where {}'.format(' and '.join(filter_where + search_where))

                cursor.execute(f'SELECT count(*) as c FROM call_log {search_sql}', filter_ar | search_ar)
                result['recordsFiltered'] = cursor.fetchone()['c']

                cursor.execute("""SELECT concat(left(`status`,1),'xx') as status_group, count(*) as c
                                    FROM call_log
                                    group by concat(left(`status`,1),'xx') order by status_group""")
                result['count_status'] = cursor.fetchall()

                final_sql = f"""SELECT `id` as "DT_RowId", `id`, `request`, `result`,
                                        DATE_FORMAT(`created_at`, %(dt)s) as `created_at`,
                                        `status`
                                    FROM call_log
                                    {search_sql}
                                    order by `{order_column}` {order_dir}
                                    limit %(start)s, %(length)s """
                cursor.execute(final_sql, {'start': start,
                                            'length': length,
                                            'dt': '%Y-%m-%d %H:%i:%S'} | filter_ar | search_ar)
                result['data'] = cursor.fetchall()

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)

        return result
