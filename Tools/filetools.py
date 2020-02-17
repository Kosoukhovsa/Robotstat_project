import pandas as pd
import os
from config import basedir

class FileEngine():

    @staticmethod
    # Возвращает содержимое листа Excel в виде словаря строк
    def GetListData(listname):
        path_name = os.path.join(basedir, 'Tools/Dictionaries.xlsx')

        #try:
        f = pd.read_excel(path_name, listname)

        #except:
        #    return {}
        #else:
        d = f.to_dict(orient='records')
        return d

    @staticmethod
    # Возвращает список справочников
    def GetDictList():
        path_name = os.path.join(basedir, 'Tools\Dictionaries.xlsx')

        try:
            f = pd.read_excel(path_name, 'Dict_list')
            print(f)
        except:
            return {}
        else:
            d = f.to_dict(orient='records')
            #d = sorted(d.items(), key=lambda x:x[1])
            dict_list = []
            for i in d:
                dict_list.append(i['Dictionary'])

            return dict_list
