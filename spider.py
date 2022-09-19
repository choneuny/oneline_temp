# module dependencies
import os
from typing import Union
from re import match, compile, findall
from pathlib import Path
from time import strftime, strptime

import numpy as np
import pandas as pd
from numexpr import evaluate
from datefinder import find_dates

# 파티셔닝된 DB 기반으로 수정 필요


class spider:
    class phrase:
        # collections 상속하여 재작성하는 편이 나을 듯
        def __init__(self, keyword: str):
            self.phrase = self._preprocessor(keyword)
            # assert self.key or self.modifier, "There's something wrong with your input"
            return

        def _preprocessor(self, keyword: str):
            # params : string for search
            # return : list of keywords + tags
            keys = ['cik', 'date', 'type', 'name',
                    'ticker', 'exchange', 'path']
            modifiers = ['after', 'before', 'year', 'qtr']
            keywords = keyword.split(' ')
            tagged = [x for x in keywords if ':' in x]
            untagged = (x for x in keywords if ':' not in x)
            untagged = [self._auto_tagging(x) for x in untagged]
            untagged = [x for x in untagged if x]
            tagged.extend(untagged)
            key = {k: v for k, v in map(
                lambda x: x.split(':'), tagged) if k in keys}
            if 'cik' in key:
                key['cik'] = int(key['cik'])
            modifier = {k: v for k, v in map(
                lambda x: x.split(':'), tagged) if k in modifiers}
            modifier = {k: self._date_parser(v) for k, v in modifier.items()}
            return key, modifier

        def _date_parser(self, input: str):
            """확실히 깔끔하게 다듬을 필요가 있음"""
            month = tuple(map(lambda x: str(x).rjust(2, '0'), range(1, 13)))
            # check input format
            assert isinstance(input, str), 'input must be a string'
            # check divier in input
            special_chars = set(findall(r'[^a-zA-Z0-9]', input))
            if not special_chars:
                if len(input) == 8:
                    return input
                elif len(input) == 6:
                    format = '%y%m%d'
                elif len(input) == 4:
                    if input.startswith(('19', '20')):
                        format = '%Y'
                    elif input.startswith(month):
                        # in current this method is not working, base year is 1900
                        format = '%m%d'
                    else:
                        raise ValueError('Invalid date format')
                else:
                    raise ValueError('Invalid date format')
                date = strptime(input, format)
                return strftime('%Y%m%d', date)
            # check there is only one type of divider
            divier, *_ = special_chars
            assert not _, 'More than one special character found'
            date = find_dates(input, first='year')
            parsed = input.split(divier)
            if len(parsed) == 2:
                if len(parsed[0]) == 4:
                    date = find_dates(input, first='year')
                    date = next(date).strftime('%Y%m01')
                else:
                    date = find_dates(input, first='month')
                    date = next(date).strftime('%Y%m%d')
            elif len(parsed) == 3:
                date = find_dates(input, first='year')
                date = next(date).strftime('%Y%m%d')
            else:
                raise ValueError('Invalid date format')
            return date

        def _auto_tagging(self, input: str) -> str:
            key = None
            acc = compile(r'\d{10}\-\d{2}\-\d{6}')
            form_type = compile(r'\d{2}\-\w+')
            if input.isdigit():
                key = 'cik'
            elif input.isalpha():
                if input.isupper():
                    key = 'ticker'
                elif input == ('Nasdaq' or 'NYSE'):
                    key = 'exchange'
            elif match(acc, input):
                key = 'acc'
            elif match(form_type, input):
                key = 'type'
            if key:
                return f'{key}:{input}'
            return

    def __init__(self, data_path: Union[str, Path], index_path: Union[str, Path] = 'index.pkl'):
        # self.index.cols = ['acc', 'cik', 'date', 'type', 'name', 'ticker', 'exchange', 'path']
        self.dir: Path = Path(data_path)
        self.index_path: Path = self.dir / index_path
        self.index: pd.DataFrame = pd.read_pickle(self.index_path) if (
            self.index_path).exists() else None
        self.index_dict: dict = {col: self.index.groupby(
            col).groups for col in self.index.columns}
        self.columns: list = self.index.columns
        # There must be a much more elegant way
        self.tree = None
        self._buildtree()
        return

    def search(self, keyword: Union[str, phrase] = '', output: str = 'cik') -> pd.Series:
        """
        get string of search query and return result of query as pd.Series[val = output]
        """
        if isinstance(keyword, str):
            key, modifier = self.phrase(keyword).phrase
        elif isinstance(keyword, spider.phrase):
            key, modifier = keyword.phrase
        else:
            raise ValueError("keyword must be str or phrase")
        assert output in self.columns, f"output must be one of {self.columns}"
        # get spider.syntax object from keywords
        # matrix of search results
        # maybe there's a better way to do this
        matrix: list = []
        for idx, (k, v) in enumerate(key.items()):
            matrix.append(self.index_dict[k][v])
        for idx, (k, v) in enumerate(modifier.items()):
            matrix.append(self._getfrom_modifier(k, v))
        # get intersection of all lists
        # if there is no intersection, return empty list
        if not matrix:
            return []
        result: set = set(matrix[0])
        for idx, m in enumerate(matrix):
            result = result.intersection(m)
        # get output of searching files
        return self.index.loc[result, output]

    def company(self, after=0, before=99999999, min_freq: int = 0, get_period=True):
        """        
        search unique cik from given period and return that (cik, *period) to spider.pharse object
        options: min_freq = minimum baseline of annual reports
        this method is just a smart wrapper for access spider.search()
        """
        phrase = spider.phrase(f'after:{after} before:{before}')
        corps = self.search(phrase, output='cik').unique()
        print(corps)
        # 조건에 맞는 기업이 없는 경우 에러
        assert corps is not None, "There's no company matching in query"
        # min_freq 이상의 기업만 추출
        if min_freq > 0:
            corps = [corp for corp in corps if len(
                self.index_dict['cik'][corp]) >= min_freq]
        # get period
        if get_period:
            return [spider.phrase(f'cik:{cik} after:{after} before:{before}') for cik in corps]
        # not get period
        return [spider.phrase(f'cik:{cik}') for cik in corps]

    def get(self, key: phrase):
        """
        get spider.syntax object, return pd.Series of (idx, text)
        대상이 너무 클 경우 OOM 대처하기 위한 코드 필요.
        """
        assert isinstance(
            key, spider.phrase), "keyword must be spider.syntax object"
        path = self.search(key, output='path')
        text = path.apply(lambda x: open(x, 'r').read())
        return text

    def _getfrom_modifier(self, mod, value):
        """ 재작성 필요 """
        date = self.index["date"]
        value = str(value)
        after = "10000000"
        before = "99999999"
        if mod == 'after':
            after = value
        elif mod == 'before':
            before = value
        elif mod == 'year':
            after = value[:4] + '0101'
            before = value[:4] + '1231'
        elif mod == 'qtr':
            after = value
            before = value[:4] + str(int(value[4:6])+3) + value[6:]
        idx = evaluate(f'({int(after)} < date) & (date < {int(before)})')
        # True to index
        return np.where(idx)[0]

    def _buildtree(self):
        """
        사용자의 디렉토리 구성이 평탄하다는 가정 하에 빠르게 트리 노드를 작성함
        spider.tree object에 딕셔너리 트리의 시각화된 표현을 할당함
        """
        if self.tree:
            return self.tree
        level = self._getlevel() - 1
        whitespace = '│  '
        childnode = '├──'
        childnoed_last = '└──'
        result = ''
        for root, dirs, _ in self._walklevel(level):
            this = root.replace(str(self.dir), '')
            num_sep = this.count(os.sep)
            result += f'{childnode * num_sep}{this}\n'
            if num_sep == level:
                for dir in dirs:
                    result += f'{childnode * (num_sep + 1)}{dir}\n'
        self.tree = result
        return

    def _walklevel(self, level=1):
        dir = str(self.dir)
        dir = dir.rstrip(os.sep)
        assert os.path.isdir(dir)
        num_sep = dir.count(os.sep)
        for root, dirs, files in os.walk(dir):
            yield root, dirs, files
            num_sep_this = root.count(os.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]

    def _getlevel(self) -> int:
        dir = str(self.dir).rstrip(os.sep)
        dir_level = dir.count(os.sep)
        for root, dirs, files in os.walk(dir):
            root_level = root.count(os.sep)
            if not dirs:
                return root_level - dir_level
