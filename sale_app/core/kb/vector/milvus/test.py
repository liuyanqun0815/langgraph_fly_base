from pymilvus import model

splade_ef = model.sparse.SpladeEmbeddingFunction(
    model_name="naver/splade-cocondenser-selfdistil",
    device="cpu"
)

docs = [
    "没办法按时还款，有什么后果",
    "贷款未结清是否可以再次申请借款？",
    "如何发现不合规的使用，行方将采取什么样的限制措施？",
]

# docs_embeddings = splade_ef.encode_documents(docs)

# 打印嵌入
# print("Embeddings:", docs_embeddings)

data = splade_ef.encode_queries(["没有还款怎么办？"])
print("Data:", data)

# 由于输出的嵌入是二维 csr_array 格式，我们将其转换为列表以便更容易操作。
# print("Sparse dim:", splade_ef.dim, list(docs_embeddings)[0].shape)