import sqlalchemy as sa

class SqlEngine():

    @staticmethod
    # Возвращает список таблиц с количеством записей в текущей БД
    def GetTablesInfo(db):
        c_engine = db.get_engine()
        t_list = c_engine.table_names()
        t_dict = {}
        for t in t_list:
            sql_query = "select count('id') from {}".format(t)
            rows_count = c_engine.execute(sql_query).scalar()
            t_dict.update({t:rows_count})

        return t_dict
