

def format_docs(docs):
    data = ""
    for doc in docs:
        if doc.type == "ai":
            data += f"\n AI助理:{doc.content}"
        else:
            data += f"\n 用户:{doc.content}"
    return data