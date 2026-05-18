# 导入标准库
import json
import os
# 导入 PyTorch
# 导入日志
import sys
import torch
# 导入numpy
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
# 导入train_test_split
# TODO sklearn：比较老的机器学习库（没有任何深度学习的方法）
from sklearn.model_selection import train_test_split
# 导入 Transformers 库
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import Trainer, TrainingArguments

from integrated_qa_system.base.logger import single_logger as logger
from integrated_qa_system.base.path_utils import resolve_relative_path

current_dir = os.path.dirname(__file__)
rag_qa_path = os.path.dirname(current_dir)
project_root = os.path.dirname(os.path.dirname(rag_qa_path))
sys.path.insert(0, project_root)

"""
意图识别模块，提供如下功能：
1. 数据加载：读取 5000 条 JSON 数据集，包含查询和标签（“通用知识”或“专业咨询”）
2. 模型训练：使用 bert-base-chinese 模型，微调二分类任务，准确率达 90%+
3. 评估优化：直接处理数字标签（0 或 1），生成分类报告和混淆矩阵
4. 预测接口：支持实时分类，集成到 EduRAG 系统。

为了满足以上功能，需要实现以下需求：
1. 初始化方法：初始化预训练的分词器、 预训练的模型。 如果是在上线阶段，主要是负责加载训练好的模型
2. 数据预处理：将查询文本和预测标签转化为模型的输入数据格式
3. 构建数据集：用于模型的训练，适配模型的训练函数
4. 模型训练：基于处理好的数据集划分出来训练集，对模型进行训练
5. 模型评估：在数据集划分出来的验证集，对模型进行评估
6. 模型预测：加载训练好的模型，完成意图识别任务

"""


class QueryClassifier(object):
    """
    需求：初始化预训练的分词器、 预训练的模型。 如果是在上线阶段，主要是负责加载训练好的模型
    思路步骤：
    1. 获取bert预训练模型所在的目录
    2. 加载预训练分词器
    3. 设置训练设备
    4. 定义标签映射
    5. 尝试加载模型
    """

    def __init__(self, model_path='models/bert_query_classifier'):
        # 加载bert
        self.pre_trained_model_path = os.path.join(rag_qa_path, 'models', 'bert-base-chinese')
        # 模型训练以后保存的位置
        self.model_path = resolve_relative_path(rag_qa_path, model_path)
        # 加载tokenizer(词表)
        # TODO 因为我们项目的微调，没有改变词表，所以对于微调过的模型和没有微调的模型，我们使用的tokenizer没有任何变化
        self.tokenizer = BertTokenizer.from_pretrained(self.pre_trained_model_path)
        # 模型对象
        self.model = None
        # 训练和预测的设备
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # # mac m系列用它，因为GPU是苹果开发自己的
        # self.device = 'mps'

        logger.info(f"使用设备: {self.device}")
        # 定义标签映射 (相当于label的词表)
        self.label_map = {"通用知识": 0, "专业咨询": 1}
        # 加载模型
        self.load_model()

    # TODO 加载模型transformers库高度封装的API
    def load_model(self):
        # 1. 对于训练好的模型
        if os.path.exists(self.model_path):
            self.model = BertForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            logger.info(f"模型加载成功：{self.model_path}")
        else:
            # 2.对于第一次训练模型
            self.model = BertForSequenceClassification.from_pretrained(self.pre_trained_model_path, num_labels=2)
            self.model.to(self.device)
            logger.info("初始化新 BERT 模型")

    # TODO 这里的保存用的是transformers库高度封装的API
    # 如果使用torch框架保存，只支持模型本体的保存，词表的需要用户自己写代码保存
    def save_model(self):
        # 1. 保存模型本体
        self.model.save_pretrained(self.model_path)
        # 2. 保存的模型的词表。 单词->id映射关系
        self.tokenizer.save_pretrained(self.model_path)
        logger.info(f"保存模型成功：{self.model_path}")

    """
    需求：实现数据预处理，将查询文本和预测标签转化为模型的输入数据格式
    思路步骤：
    1. 接收传入的query数据和分类标签数据
    2. 将查询文本数值化，使用预训练的tokenizer对query进行编码和长度补齐，得到input_ids和attention_mask
    3. 将标签数据数值化
    """

    # TODO 这里我们使用3行处理了数据，但是在实际工作中，这里要复杂得多。一般来讲很少有数据直接可以拿来用
    def preprocess_data(self, texts, labels):
        # texts： [问题1,问题2,...问题n] -> ["解释一下什么是RESTful API。"]
        # labels：[标签1,标签2,...标签n] -> ["通用知识"]
        # ["你是谁","解释一下什么是RESTful API。"]
        # pt: pytorch的缩写。 tf: tensorflow
        # tensor: 张量， 1个数字-常量，1维数组-向量，2维数组-矩阵，3维？ 张量：1~n维数据的统称。
        encodings = self.tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors="pt")
        # labels: [标签1,标签2,...标签n] -> [0,1,...0]
        return encodings, [self.label_map[label] for label in labels]

    """
    需求：实现数据集的构建，用于模型的训练，适配模型的训练函数
    思路步骤：
    1. 预处理的数据化query和label数据
    2. 继承实现Dataset类
        2.1 实现初始化方法
        2.2 实现__getitem__，根据索引拿到对应的数据
        2.3 实现__len__，获取数据集长度
    3. 构建Dataset类并返回
    """

    def create_dataset(self, encodings, labels):
        class Dataset(torch.utils.data.Dataset):
            def __init__(self, encodings1, labels1):
                self.encodings = encodings1
                self.labels = labels1

            def __getitem__(self, idx):
                # encodings: { 'input_ids': input_ids, 'attention_mask':attention_mask  }

                # input_ids: tensor[batch_size(有几句话，几条数据)=485, seq_len(一句话多长)=<128]"
                # val[idx]： 第idx条数据的编码以后的id

                item = {key: val[idx] for key, val in self.encodings.items()}

                # 将标签加进去, 转换成 PyTorch 的张量格式（Tensor），因为神经网络只能处理 Tensor
                item["labels"] = torch.tensor(self.labels[idx])
                # TODO item {"labels":labels, "attention_mask":attention_mask, "input_ids":input_ids,"token_type_ids": token_type_ids}
                return item

            def __len__(self):
                return len(self.labels)

        return Dataset(encodings, labels)

    """
    需求：实现模型的训练方法，基于处理好的数据集划分出来训练集，对模型进行训练
    思路步骤：
    1. 数据预处理
        1.1 加载数据集
        1.2 把数据集划分成8:2的训练集和验证集
        1.3 把数据进行数值化
        1.4 构建Dataset
    2. 设置训练参数
    3. 初始化Trainer，传入参数、数据集、模型对象等
    4. 开启训练
    5. 保存模型
    6. 评估模型
    """

    def train_model(self, data_file='model_generic_1000.json'):
        if not os.path.exists(data_file):
            logger.error(f"数据集文件 {data_file} 不存在")
            raise FileNotFoundError(f"数据集文件 {data_file} 不存在")

        with open(data_file, "r", encoding="utf-8") as f:
            # 只能读取jsonl文件
            data = [json.loads(value) for value in f.readlines()]
            logger.info(f"数据集加载成功：{data}")

        texts = [item["query"] for item in data]
        labels = [item["label"] for item in data]

        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )

        train_encodings, train_labels = self.preprocess_data(train_texts, train_labels)
        val_encodings, val_labels = self.preprocess_data(val_texts, val_labels)

        train_dataset = self.create_dataset(train_encodings, train_labels)
        val_dataset = self.create_dataset(val_encodings, val_labels)

        training_args = TrainingArguments(
            output_dir="./bert_results",
            num_train_epochs=3,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir="./bert_logs",
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            save_total_limit=1,  # 只保存一个检查点，即最优的模型
            metric_for_best_model="eval_loss",
            fp16=False,  # 禁用混合精度
        )

        # 初始化 Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics
        )

        # 训练模型
        logger.info("开始训练 BERT 模型...")
        trainer.train()
        self.save_model()

        # 评估模型
        self.evaluate_model(val_texts, val_labels)

    @staticmethod
    def compute_metrics(eval_pred):
        """计算评估指标"""
        # logits：预测权重值 [-1.5, 2.0]
        # labels: 真实值 [0]
        logits, labels = eval_pred
        # TODO: 正常的做法 logits: [-1.5, 2.0] -> softmax归一化 -> [0.2, 0.8] -> argmax
        # TODO: 我们这里省略了softmax，直接取logits: [-1.5, 2.0] 最大值。
        # softmax不会影响数据前后的单调性（logits里面最大值，转成softmax归一化以后得结果，还是最大值）
        # argmax需要的是索引， argmax得到的结果就是：1
        # prediction = 1 , label = 0
        # predictions: [batch_size] -> labels:[batch_size]
        predictions = np.argmax(logits, axis=-1)
        accuracy = (predictions == labels).mean()
        return {"accuracy": accuracy}

    """
       需求：评估模型性能，输出分类报告和混淆矩阵
       思路步骤：
       1. 数据预处理
           1.1 对输入文本进行分词编码（截断/填充至128长度）
           1.2 创建包含编码和标签的Torch数据集
       2. 初始化预测工具
           2.1 创建Trainer实例加载当前模型
       3. 执行预测
           3.1 使用predict方法获取原始预测结果
           3.2 通过argmax解析预测标签，得到概率最大的预测值的标签id(0 ~ 1)
       4. 生成评估报告
           4.1 输出分类报告（含精确率/召回率/F1值）
           4.2 输出混淆矩阵
    """

    def evaluate_model(self, texts, labels):
        """评估模型性能"""
        # 仅对 texts 进行分词，labels 已为数字
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt"
        )
        dataset = self.create_dataset(encodings, labels)

        trainer = Trainer(model=self.model)
        predictions = trainer.predict(dataset)
        # predictions : [batch_size=97, 2]
        # np.softmax(predictions.predictions) ->  [-3.1, 2.7 ] /[ 0.3, 0.7 ]
        # argmax操作1维向量，所以我需要给它一个维度，它在哪个维度上去计算最大值 , array[-1]
        pred_labels = np.argmax(predictions.predictions, axis=-1)
        true_labels = labels  # 直接使用数字标签

        logger.info("分类报告:")
        logger.info(classification_report(
            true_labels,
            pred_labels,
            target_names=["通用知识", "专业咨询"]
        ))
        logger.info("混淆矩阵:")
        logger.info(confusion_matrix(true_labels, pred_labels))

    """
      需求：根据输入的查询语句预测其类别（通用知识或专业咨询）
          端到端： "Java学费一年多少钱"  -> "专业咨询"
      思路步骤：
      1. 加载模型, 并检查模型的状态
          1.1 验证模型是否已加载，未加载则记录错误并返回默认类别: 0->通用知识，让大模型处理query
      2. 输入数据处理
          2.1 对查询语句进行分词和编码（截断/填充至128长度）
          2.2 将编码数据移动到模型所在的设备
      3. 执行预测
          3.1 在无梯度模式下进行推理
          3.2 获取模型输出并解析预测结果（取logits最大值对应的类别）
      4. 结果映射
          4.1 将数字标签转换为对应的类别名称（0->通用知识，1->专业咨询）
      """

    def predict_category(self, query1):
        # 检查模型是否加载
        if self.model is None:
            # 模型未加载，记录错误
            logger.error("模型未训练或加载")
            # 默认返回通用知识
            return "通用知识"
        # 对查询进行编码
        encoding = self.tokenizer(query1, truncation=True, padding=True, max_length=128, return_tensors="pt")
        # 将编码移到指定设备
        #
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        # 不计算梯度，进行预测
        with torch.no_grad():
            # 获取模型输出
            # {"attention_mask":attention_mask, "input_ids":input_ids,"token_type_ids": token_type_ids}
            outputs = self.model(**encoding)
            # 获取预测结果
            prediction = torch.argmax(outputs.logits, dim=1).item()
        # 根据预测结果返回类别
        return "专业咨询" if prediction == 1 else "通用知识"


if __name__ == '__main__':
    # 检查PyTorch版本和CUDA可用性
    print("PyTorch Version:", torch.__version__)
    print("CUDA Available:", torch.cuda.is_available())
    print(project_root)
    # 实例化查询分类器
    # model_path是模型训练后保存的路径
    classifier = QueryClassifier(model_path='models/bert_query_classifier')

    # 步骤1：训练模型
    # 注意：训练过程需要几分钟到几十分钟，具体取决于您的硬件。
    # 如果您已经有训练好的模型，可以注释掉下面 classifier.train_model 一行。
    # 确保数据集文件路径正确, 默认是在项目根目录的dataset文件夹下
    # print("开始训练模型...")
    # try:
    #     data_file = os.path.join(project_root, "others", "classify_data", "model_generic_1000.json")
    #     classifier.train_model(data_file=data_file)
    #     print("模型训练完成。")
    # except FileNotFoundError as e:
    #     print(f"错误: {e}")

    # 步骤2：使用训练好的模型进行预测
    # 重新实例化分类器会加载刚才训练并保存好的模型
    print("\n加载模型并进行预测...")
    predictor = QueryClassifier(model_path='models/bert_query_classifier')

    # 检查模型是否成功加载
    if predictor.model is not None:
        # 定义一些测试查询
        test_queries = [
            "你好，请问什么是人工智能？",  # 预期：通用知识
            "你们学校的计算机科学硕士项目申请要求是什么？",  # 预期：专业咨询
            "给我讲个笑话",  # 预期：通用知识
            "我想了解一下关于深度学习课程的详细信息和学费。",  # 预期：专业咨询
            "今天天气怎么样？",  # 预期：通用知识
            "丙泊酚乳状注射液能和其他药物混合吗？",  # 预期：专业咨询
        ]
        # 遍历查询并打印预测结果
        for query in test_queries:
            predicted_category = predictor.predict_category(query)
            print(f"查询: '{query}'\n  -> 预测类别: {predicted_category}\n")
    else:
        print("模型加载失败，无法进行预测。请先完成模型训练。")
