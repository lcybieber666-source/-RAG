# 导入 BGE-M3 嵌入函数，用于生成文档和查询的向量表示
import os.path
import pickle
import torch
# 模型加载器(BGEM3Embedding)
from milvus_model.hybrid import BGEM3EmbeddingFunction
# 导入 Milvus 相关类，用于操作向量数据库
from pymilvus import MilvusClient, DataType, AnnSearchRequest, WeightedRanker
# 导入 Document 类，用于创建文档对象
# 相当于java里面的Pojo(实体类)
from langchain.docstore.document import Document
# 导入 CrossEncoder，用于重排序和 NLI 判断，加载rerank模型()
# TODO sentence_transformers是hugging-face开源的一个基于transformer架构的开源模型库，专门用来处理段落的
# 它是transformers的一部分，交叉学习/对比学习： query和document(context) ，计算关联性
from sentence_transformers import CrossEncoder
# 导入 hashlib 模块，用于生成唯一 ID 的哈希值
import hashlib

import integrated_qa_system.rag_qa.core.document_processor as document_processor
from integrated_qa_system.base.config import single_config as config
from integrated_qa_system.base.logger import single_logger as logger

import sys

# 获取当前文件所在目录的绝对路径
# __file__: 当前文件 + os.path.dirname = 当前文件所在的目录 （/Users/itheima/Documents/黑马/讲课/就业班/EduRAG/学生端/03-代码/0001.项目目录/integrated_qa_system/rag_qa/core）
# os.path.dirname(__file__) -> 当前的文件所在的目录
# local_path: 当前所在的文件夹名 (core)
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# xxx/integrated_qa_system/rag_qa/models/core
# TODO __file__: 当前文件的全路径，就是xxx/integrated_qa_system/rag_qa/core/vector_store.py
# TODO os.path.dirname: xxx/integrated_qa_system/rag_qa/core
local_path = os.path.dirname(__file__)
# 再网上一层

# 重复上述操作，拿到对应的绝对路径
# TODO os.path.dirname: xxx/integrated_qa_system/rag_qa
rag_qa_path = os.path.dirname(local_path)

# TODO 添加到python系统的文件里面(相当于环境变量里面的path)
# 把这个路径放到系统路径的最前面

sys.path.insert(0, rag_qa_path)
# 获取根目录文件所在的绝对位置
project_root = os.path.dirname(rag_qa_path)
sys.path.insert(0, project_root)

"""
实文档向量的存储功能
分为以下3个模块：
初始化与集合管理：创建或加载Milvus向量数据库集合。
    初始化方法：初始化VectorStore类的实例，设置基本参数并调用集合创建或加载方法
    创建或加载集合方法：检查并创建或加载Milvus集合，定义字段结构和索引参数
文档向量化与存储：将分块后的文档转换为向量并存储。
    添加文档方法：将分块后的文档转换为向量并存储到Milvus集合
混合检索与重排序：结合稠密和稀疏向量进行检索，并通过重排序优化结果。
"""

"""
需求：实现初始化方法：初始化VectorStore类的实例，设置基本参数并调用集合创建或加载方法
实现步骤：
1. 初始化milvus向量数据库 
    1.1 用config中的默认值初始化集合名称、主机、端口和数据库名称。
    1.2 把collection索引加载到内存中
2. 初始化模型
    2.1 reranker：加载BGE-Reranker模型，用于后续重排序。
    2.2 embedding_function：初始化BGE-M3嵌入模型，禁用FP16，使用CPU运行。
    2.3 dense_dim：获取稠密向量的维度
"""


class VectorStore:
    def __init__(self
                 , collection_name=config.MILVUS_COLLECTION_NAME
                 , host=config.MILVUS_HOST
                 , port=config.MILVUS_PORT
                 , database=config.MILVUS_DATABASE_NAME
                 ):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.database = database
        self.logger = logger

        rerank_model_path = os.path.join(rag_qa_path, 'models', 'bge-reranker-large')

        # rerank模型加载
        # self.reranker = CrossEncoder(rerank_model_path, device='cuda:0')
        # self.reranker = CrossEncoder(rerank_model_path, device='cpu')
        # TODO 需要注意设备
        # rerank模型： 从milvus查到了context(多个父块)以后，再根据context和query的关联做一个重排序
        # TODO 使用模型名初始化CrossEncoder，会从huggingface官网拉取对应的模型
        # self.reranker = CrossEncoder('bge-reranker-large', device='mps')
        # TODO device代表设备： mps:m1系列的mac/ cpu: cpu / cuda: nvidia的gpu。和操作系统无关
        self.reranker = CrossEncoder(rerank_model_path, device=device)

        # 和rerank_model_path同理
        bge_m3_model_path = os.path.join(rag_qa_path, 'models', 'bge-m3')
        # TODO 需要注意设备
        self.embedding_function = BGEM3EmbeddingFunction(
            model_name_or_path=bge_m3_model_path
            , use_f16=True,
            device=device
        )

        # 拿到embedding模型的维度
        self.dense_dim = self.embedding_function.dim["dense"]

        # 构造一个连接串
        self.client = MilvusClient(uri=f"http://{self.host}:{self.port}", db_name=self.database)

        self._create_or_load_collection()

    """
    需求：实现创建或加载集合方法：检查并创建或加载Milvus集合，定义字段结构和索引参数
    思路步骤：
    1. 判断集合是否存在，若存在则进行加载
    2. 集合不存在，创建新集合
        2.1 定义集合各字段 id、text、dense_vector、sparse_vector、parent_id、 parent_content、source 、timestamp
        2.2 定义索引： 稠密向量索引：dense_vector ， 稀疏向量索引：sparse_vector
    3. 把集合的索引加载到内存中
    """

    def _create_or_load_collection(self):
        # 如果集合不存在，创建一个新的集合
        if not self.client.has_collection(self.collection_name):
            # 创建集合 Schema，禁用自动 ID，启用动态字段
            schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
            # 添加 ID 字段，作为主键，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=100)
            # 添加文本字段，VARCHAR 类型，最大长度 65535
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            # 添加稠密向量字段，FLOAT_VECTOR 类型，维度由嵌入函数指定
            schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=self.dense_dim)
            # 添加稀疏向量字段，SPARSE_FLOAT_VECTOR 类型
            schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
            # 添加父块 ID 字段，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="parent_id", datatype=DataType.VARCHAR, max_length=100)
            # 添加父块内容字段，VARCHAR 类型，最大长度 65535
            schema.add_field(field_name="parent_content", datatype=DataType.VARCHAR, max_length=65535)
            # 添加学科类别字段，VARCHAR 类型，最大长度 50
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=50)
            # 添加时间戳字段，VARCHAR 类型，最大长度 50
            schema.add_field(field_name="timestamp", datatype=DataType.VARCHAR, max_length=50)

            index_params = self.client.prepare_index_params()

            # 为稠密向量（句子向量）字段添加 IVF_FLAT 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_index",
                index_type="IVF_FLAT",
                # COSINE: 余弦相似度， L2:欧氏距离
                metric_type="IP",
                params={"nlist": 128}
            )
            # 为稀疏向量（词向量， 单词：重要程度）字段添加 SPARSE_INVERTED_INDEX 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_index",
                # SPARSE_INVERTED_INDEX: 稀疏向量专用索引
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                # 在构建索引时，按一定比例丢弃向量中绝对值较小的元素
                params={"drop_ratio_build": 0.2}
            )

            self.client.create_collection(self.collection_name, schema=schema, index_params=index_params)
            logger.info(f"已创建集合 {self.collection_name}")
        else:
            # 记录加载集合的日志
            logger.info(f"集合已存在 {self.collection_name}")

        # 将集合加载到内存，确保可立即查询
        # TODO 相当于构建索引，让milvus的这个表可以进行向量匹配查询
        self.client.load_collection(self.collection_name)
        logger.info(f"已加载集合 {self.collection_name}")

    """
         需求：将分块(子块)后的文档转换为向量并存储到Milvus集合
         思路步骤：
         1. 提取文本, 从文档对象中提取文本内容
         2. 生成向量,使用BGE-M3模型生成稠密和稀疏向量。
         3. 构造数据，为每篇文档生成唯一ID（MD5哈希）。将向量和元数据组织成字典
         4. 使用upsert操作插入或更新数据
        """

    def add_documents(self, documents: list[Document]):
        """
        将分块(子块)后的文档转换为向量并存储到Milvus集合
        :param documents: 已经处理成子块的数据, Document是一个子块
        :return:
        """
        # 把每个子块里面的内容（大字符串、纯文本）拿出来
        # 列表，每个元素都是一个子块中的文本，形状是：[n] 。n指的是子块的数量
        texts = [document.page_content for document in documents]

        # 调用embedding的算法，把数据转成向量：一维列表 [文档的纯文本 ] length = 文档数
        # TODO 稠密向量： embeddings['dense'] -> dense_vector : 一个文本用一个1024的向量表示， dense_vector [文档id, 文本向量]
        # TODO 稀疏向量： embeddings['sparse'] -> sparse_vector:   { 单词:单词对应的权重, xxxxxxx}

        # 返回的结果是一个二维的矩阵数据组成的字典，包含稀疏向量和稠密向量。   dict {dense:  [n,dim=1024] , sparse:}
        # TODO 对于常见的模型， 对象名()调用的模型中的forward，也叫做前向传播，做预测(预测是推理的一种)/推理使用
        # TODO y=f(x), x:自变量/输入, y:因变量/输出 ，f: 模型， y=f(x) 其实就是做了推理
        embeddings = self.embedding_function(texts)

        # 要插入的所有的数据
        data = []

        # enumerate是给可迭代对象加一个计数器，从0开始，到len-1
        for index, doc in enumerate(documents):
            # content: 每个文档的纯文本
            content = doc.page_content.encode('utf-8')

            # 对文本进行md5算法（hash操作/加密） 文本 -> 唯一hash字符串(只有内容完全一样的时候，id才会重复)
            # 自己实现了主键的计算
            id = hashlib.md5(content).hexdigest()

            spase_vector = {}

            # TODO 这里如果出错，别忘了打断点调试

            # 稀疏向量
            #   embeddings {dense:  [n,dim=1024] , sparse:[n]}
            # TODO 提取稀疏向量中指定行的数据，[[index], :]表示提取第index行的数据,[index]是因为必须保持稀疏向量的二维结构
            row = embeddings['sparse'][[index], :]
            logger.info(f"获取稀疏向量成功, 得到的row: {row}")

            # TODO 模型返回的结果是 col和data分开存储的，需要转换成 {单词id : 单词权重} 字典结构以满足milvus稀疏向量查询和存储的要求
            # TODO 每个单词
            # row.indices
            indices = row.indices
            # TODO 每个单词的权重
            values = row.data
            # indices: [1,2,3,4]
            # values:  [0.1,0.2,0.3,0.4]
            # zip -> (1,0.1) , (2,0.2) .....
            for token_id, value in zip(indices, values):
                # {单词id : 单词权重}
                spase_vector[token_id] = value

            data.append({
                'id': id,
                'text': doc.page_content,
                # dense_vector [文档id(第几个子块), 文本向量 ] (传入文档id) -> 当前这个文档对应的文本向量
                # dense:  [n,dim=1024]
                'dense_vector': embeddings['dense'][index],
                'sparse_vector': spase_vector,
                'parent_id': doc.metadata['parent_id'],
                'parent_content': doc.metadata['parent_content'],
                'source': doc.metadata.get('source', 'unknown'),
                'timestamp': doc.metadata.get('timestamp', 'unknown')
            })

        if data:
            self.client.upsert(collection_name=self.collection_name, data=data)
            logger.info(f"输入成功写入milvus：{len(data)}条")
        else:
            logger.warning(f"文档数据为空")

    """
    需求：对输入的query进行混合检索
    思路步骤：
    1. 生成查询向量：使用BGE-M3生成稠密和稀疏向量。
    2. 构造检索请求(混合检索)：
        2.1 构造稠密向量的AnnSearchRequest
        2.2 构造稀疏向量的AnnSearchRequest
    3. 混合检索： 使用WeightedRanker融合结果
    4. 重排序，使用CrossEncoder:reranker重新排序父文档
    """

    def hybrid_search_with_rerank(self, query, k=config.RETRIEVAL_K, source_filter=None):

        # 把query进行embedding， [query]
        # TODO 使用BGE-M3生成 ① 稠密和 ②稀疏向量 （文档写入milvus的也执行过同样的操作）,这是为了保证一样的文本转换成向量的数值完全一致
        # 这里必须是列表，因为设计上BGEM3可以传入多个参数，但是我们在这里实现的单条查询，还是必须使用数组包装
        query_embeddings = self.embedding_function([query])

        # 获得稠密向量，由于是单条查询，所以取一个数据
        dense_query_vector = query_embeddings['dense'][0]

        # 获得稀疏向量
        spase_query_vector = {}
        row = query_embeddings['sparse'][[0], :]
        indices = row.indices
        values = row.data

        for token_id, value in zip(indices, values):
            # TODO 稀疏向量的查询和存储要求是 {单词id : 单词权重}
            spase_query_vector[token_id] = value

        # 支持根据学科过滤的场景
        filter_expr = f'source == "{source_filter}"' if source_filter else ''

        # 构建稠密向量的查询对象
        dense_request = AnnSearchRequest(
            data=[dense_query_vector],
            anns_field='dense_vector',
            # IP：内积
            # nprobe：查询最近的几个簇
            param={'metric_type': 'IP', 'params': {'nprobe': 10}},
            limit=k,
            expr=filter_expr
        )

        sparse_request = AnnSearchRequest(
            data=[spase_query_vector],
            anns_field='sparse_vector',
            param={'metric_type': 'IP', 'params': {}},
            limit=k,
            expr=filter_expr
        )

        # 权重混合检索排序
        # 0.7: 稠密向量, 句子向量
        # 1.0: 稀疏向量, 稀疏向量给的大
        # TODO：我们用这种方式是因为我们认为稀疏向量（单词+权重）对检索结果影响更大
        ranker = WeightedRanker(0.7, 1.0)

        # TODO：执行混合检索，这里的results返回的是一个列表
        results = self.client.hybrid_search(
            collection_name=self.collection_name,
            reqs=[dense_request, sparse_request],
            ranker=ranker,
            limit=k,
            output_fields=["text", "parent_id", "parent_content", "source", "timestamp"]
        )[0]

        # 拿到检索到的所有的子块
        # _doc_from_hit: 把milvus返回的结果封装成Document对象
        sub_chunks = [self._doc_from_hit(hit['entity']) for hit in results]

        # TODO：通过子块，拿到所有的父块的内容，并进行去重
        parent_docs = self._get_unique_parent_docs(sub_chunks)

        if parent_docs:
            # 如果父块只有一个，进行返回
            if len(parent_docs) < 2:
                return parent_docs
            # TODO 这里的parent_docs其实就是context
            # TODO 如果父块超过一个，需要进行重排序： 基于query 和context的匹配程度做重排序
            # 构造： (query, context) 对，将“问题”和每一个“候选文档”组成一对 [query, document_text]
            pairs = [[query, doc.page_content] for doc in parent_docs]
            # TODO 通过rerank模型， 计算 query 和 context(一个父块) 的分数
            scores = self.reranker.predict(pairs)

            # 排序，按照分数的大小进行倒排。 分数高的排到前面
            # zip: (0.5, 父块1), (0.3,父块2)
            # TODO 这里直接做了排序(排序方式：倒排)， 可以再增加一个判断score是否大于某个阈值的逻辑
            ranked_parent_docs = [doc for _, doc in sorted(zip(scores, parent_docs), reverse=True)]
        else:
            ranked_parent_docs = []
        # TODO 最后保留CANDIDATE_M个父块作为最终的context
        # TODO 切片操作[:config.CANDIDATE_M] -> 切片 相当于 只保存列表中下标从0到config.CANDIDATE_M的，[0,2)
        # 长度为 10的 list -> 长度不超过CANDIDATE_M
        # 类比 字符串的sub_string(0, CANDIDATE_M)
        # CANDIDATE_M 怎么确定？ 取决于模型能支持的输入的大小 1200 * 2 = 2400 3

        # TODO 注意：这里基于rerank的score排序以后得结果无论和问题的相关性多么小，总是取相对比较大的最大值。
        # TODO 这样会存在一个问题：有可能会查出来和问题完全不相干的。 所以可以在前面增加一个阈值判断
        return ranked_parent_docs[:config.CANDIDATE_M]

       

    @staticmethod
    def _doc_from_hit(hit):
        return Document(
            page_content=hit['text'],
            metadata={
                'source': hit['source'],
                'timestamp': hit['timestamp'],
                'parent_id': hit['parent_id'],
                'parent_content': hit['parent_content']
            }
        )



    @staticmethod
    def _get_unique_parent_docs(sub_chunks):
        """
            parm:
                sub_chunks: 子块
            return:
                unique_parent_docs: 去重后的父块
        """
        # 存储已经出现过的父块内容，用于去重
        parent_docs = set()

        unique_parent_docs = []

        for chunk in sub_chunks:
            # 获取父块的内容，如果没有就用子块的内容兜底
            parent_content = chunk.metadata.get('parent_content', chunk.page_content)
            # 基于父块里面的内容进行去重
            if parent_content and parent_content not in parent_docs:
                unique_parent_docs.append(
                    Document(
                        page_content=parent_content
                        , metadata=chunk.metadata
                    )
                )
                # 添加到集合中，用于去重    
                parent_docs.add(parent_content)

        return unique_parent_docs



if __name__ == '__main__':
    data_path = os.path.join(rag_qa_path, 'data', 'ai_data')
    try:
        documents = document_processor.process_documents(data_path)

        if len(documents) == 0:
            logger.warning("未找到任何文档进行处理")
        else:
            vector_store = VectorStore()
            vector_store.add_documents(documents)
            logger.info(f"成功添加 {len(documents)} 个文档到向量库")
    except Exception as e:
        logger.error(f"处理文档或添加到向量库时发生错误: {e}")
