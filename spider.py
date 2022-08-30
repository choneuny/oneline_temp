class file :
    # import modules
    import os
    import datetime as dt
    import numpy as np
    from pandas import DataFrame, Series, read_csv 
    from numexpr import evaluate as ne_eval
    from dateutil.parser import parse

    def __init__(self, data_path, dict_path):
        self.dir = data_path
        self.dict = read_csv(dict_path)[['CIK', 'FILING_DATE', 'ACC_NUM', 'FORM_TYPE' ,'CoName']]
        self.depth = 0
        self.subdir = []
        self.file_count = []
        self.columns = {
            "cik": self.dict.CIK.values,
            "date": self.dict.FILING_DATE.values,
            "name": self.dict.CoName.values,
            "acc": self.dict.ACC_NUM.values,
            "form": self.dict.FORM_TYPE.values,
            "symbol": self.dict.TICKER.values,
            "exchange": self.dict.EXCHANGE.values
        }

    def index(self, dir):
        """index tree and file counts in dir
        return pandas set"""
        if not dir or (dir in ["whole", "all", "root", "tree", "node"]):
            ## print all directory tree and return listdir of root
            return os.listdir(self.dir)
        if len(dir) == 1:
            ## search inputted dir in list of subdir and return listdir of that
            if dir in self.subdir: return os.listdir(self.subdir[self.subdir.index(dir)])
        return
    
    def search(self, *keywords):
        if not keywords: return os.listdir(self.dir)
        if len(keywords) > 1: return
        ### search by keyword
        key, modifier = self._search_preprocess(str(keywords[0]))
        assert modifier or key, "input your keyword"
        matrix = []
        ## 조심해야함
        if modifier: 
            matrix.append([self._get_from_modifier(mod, value) for mod, value in modifier.items()])
        if key: 
            matrix.append([self._get_from_key(key, value) for key, value in key.items()])
        idx = np.multiply.reduce(matrix)
        # to boolean array
        idx = np.array([True if i else False for i in idx[0]])
        # result = summaries[idx][['FILING_DATE', 'ACC_NUM']]
        # result.set_index('ACC_NUM', inplace=True)
        return summaries[idx]

    def make_df_from_path(self, paths):
        # make dataframe that has colums of date, type, acc, text
        df = DataFrame(columns=["date", "type", "acc", "text"])
        for path in paths:
            file = os.path.basename(path)
            date = file.split("_")[0]
            type = file.split("_")[1]
            acc = file.split("_")[5].replace(".txt", "")
            text = open(path, "r").read()
            # append to df
            df = df.append(DataFrame([[date, type, acc, text]], columns=["date", "type", "acc", "text"]))
        return df
        ## input: list of path
        # get filename from path
        ## output: 

    def _search_preprocess(self, keyword):
        # params : string for search 
        # return : list of keywords + tags
        key_tags = ['cik', 'date', 'name', 'symbol','acc', 'form']
        modifier_tags = ['after', 'before', 'year', 'qtr']
        keyword_list = keyword.split(' ')
        ## unknown 인식 및 처리 과정 필요
        unknown = list(filter(lambda x: ':' not in x, keyword_list))
        tag = list(filter(lambda x: ':' in x, keyword_list))
        tag = dict(tuple(x.split(':')) for x in tag) if tag else {}
        key = {k:v for k,v in tag.items() if k in key_tags}
        modifier = {k:v for k,v in tag.items() if k in modifier_tags}
        ## 현재 dateparser 적용 안되는 오류
        for k, val in modifier.items(): val = self._date_parser(val)
        modifier = {k:v for k,v in modifier.items() if v}
        return key, modifier

    def _date_parser(self, date):
        if len(date) == 4:
            if date.startswith(('19', '20')):
                ## 연도만 입력된 경우
                return date+'0101'
            if int(date[:2]) < 13:
                ## 월일만 입력된 경우
                year = str(dt.now().year)
                return year + date
        ## try 내에서 return 사용 가능?
        try: result = parse(date).strftime('%Y%m%d')
        except: return None
        return result

    def _get_depth(self, path):
        for root, dir, file in os.walk(path):
            if file and not dir: 
                self.depth = root.count(os.sep)-path.count(os.sep)+1
        return "ERROR"
    
    def _get_subdir(self, path):
        """search for subdir in path
        return list of subdir
        every iteration, check next(os.walk(subdir))[1]
        if empty continue to next iteration"""
        return "ERROR"
    
    def _get_from_key(self, key, value):
        col = self.columns[key]
        idx = ne_eval(f'(col == {value})')
        return idx

    def _get_from_modifier(self, modifier, value):
        date = self.columns["date"]
        value = str(value)
        after = "10000000"
        before = "99999999"
        if modifier == 'after': after = value
        elif modifier == 'before': before = value
        elif modifier == 'year': 
            after = value[:4] + '0101' 
            before = value[:4] + '1231'
        elif modifier == 'qtr':
            after = value 
            before = value[:4] + str(int(value[4:6])+3) + value[6:]
        idx = ne_eval(f'({int(after)} < date) & (date < {int(before)})')
        return idx