from sale_app.core.moudel.zhipuai import ZhipuAI


def pre_handle(question: str) -> dict | None:
    llm = ZhipuAI().openai_chat()

    return None




# if __name__ == '__main__':
#     data = PreSafety()
#     d = pre_handle("xx", "xx")
#     print(d)
