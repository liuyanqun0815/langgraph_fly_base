import os
import pandas as pd

from sale_app.config.log import Logger

logger = Logger("fly_base")


# xlsx文件加载
def xlsx_loader(file_path) -> list[dict]:
    # 读取xlsx文件
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    all_data = []
    # 由于列名是自定义的，我们通过列索引来获取数据
    for sheet_name, df in all_sheets.items():
        logger.info(f"Sheet Name: {sheet_name}")
        questions = df.iloc[:, 0].tolist()  # 第一列数据
        answers = df.iloc[:, 1].tolist()  # 第二列数据
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]
        # 将问题和答案组合成一个列表的列表
        qa_list = list(zip(questions, answers))
        for question, answer in qa_list:
            if file_name not in question:
                question = f"{file_name}{question}"
            all_data.append({"question": question, "answer": answer})
    return all_data
