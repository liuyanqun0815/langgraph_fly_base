"""Abstract interface for document loader implementations."""
import logging
from typing import Optional

import pandas as pd
import xlrd
from langchain_core.documents import Document

from sale_app.core.kb.loader.extractor_base import BaseExtractor

logger = logging.getLogger(__name__)


class ExcelExtractor(BaseExtractor):
    """
    用于加载Excel文件的提取器。

    参数:
        file_path (str): 要加载的文件路径。
    """

    def __init__(
            self,
            file_path: str,
    ):
        """
        使用文件路径初始化ExcelExtractor。

        参数:
            file_path (str): 文件路径。
        """
        self._file_path = file_path

    def extract(self) -> list[Document]:
        """
        解析Excel文件并返回文档列表。

        返回:
            list[Document]: 包含解析结果的文档列表。
        """
        if self._file_path.endswith('.xls'):
            return self._extract4xls()
        elif self._file_path.endswith('.xlsx'):
            return self._extract4xlsx()

    def _extract4xls(self) -> list[Document]:
        """
        从.xls文件中提取数据并转换为Document对象。

        返回:
            list[Document]: 包含.xls文件内容的文档列表。
        """
        wb = xlrd.open_workbook(filename=self._file_path)
        logger.info(f'_extract4xls file path:{self._file_path}')
        documents = []

        # 遍历所有工作表
        for sheet in wb.sheets():
            logger.info(f'sheet name:{sheet.name}')
            row_header = None
            for row_index, row in enumerate(sheet.get_rows(), start=1):
                logger.info(f'row_index:{row_index},row:{row}')
                if self.is_blank_row(row):
                    logger.info(f'blank row:{row}')
                    continue
                if row_header is None:
                    row_header = row
                    continue
                item_arr = []
                for index, cell in enumerate(row):
                    txt_value = str(cell.value)
                    logger.info(f'index:{index},key:{row_header[index].value},txt_value:{txt_value}')
                    item_arr.append(f'{row_header[index].value}:{txt_value}')
                item_str = "\n".join(item_arr)
                logger.info(f'item_str:{item_str}')
                document = Document(page_content=item_str, metadata={'source': self._file_path})
                documents.append(document)
        return documents

    def _extract4xlsx(self) -> list[Document]:
        """
        从.xlsx文件中读取数据，并将其转换为Document对象。

        返回:
            list[Document]: 包含.xlsx文件内容的文档列表。
        """
        data = []

        # 使用Pandas读取Excel文件中的每个工作表
        xls = pd.ExcelFile(self._file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # 过滤掉全为空值的行
            df.dropna(how='all', inplace=True)

            # 将每一行转换为Document对象
            for _, row in df.iterrows():
                item = ';'.join(f'{k}:{v}' for k, v in row.items() if pd.notna(v))
                document = Document(page_content=item, metadata={'source': self._file_path})
                data.append(document)
        return data

    @staticmethod
    def is_blank_row(row):
        """
        判断指定行是否为空行。

        参数:
            row: 行对象。

        返回:
            bool: 如果行为空则返回True，否则返回False。
        """
        # 遍历单元格，如果发现非空单元格则返回False
        for cell in row:
            if cell.value is not None and cell.value != '':
                return False
        return True
