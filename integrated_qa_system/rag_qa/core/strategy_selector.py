# core/strategy_selector.py 源码
# 导入 LangChain 提示模板
from langchain.prompts import PromptTemplate
# 导入 OpenAI
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)

# 导入日志和配置
from integrated_qa_system.base.config import single_config as config
from integrated_qa_system.base.logger import single_logger as logger


class StrategySelector:
    def __init__(self):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=config.DASHSCOPE_API_KEY,
                             base_url=config.DASHSCOPE_BASE_URL)
        # 获取策略选择提示模板
        self.strategy_prompt_template = self._get_strategy_prompt()

    def call_dashscope(self, prompt):
        # 调用 DashScope API
        try:
            # 正确构建消息列表，使用适当的类型
            messages = [
                ChatCompletionSystemMessageParam(role="system", content="你是一个智能助手，能够根据用户输入的Prompt严格执行并返回可靠的结果"),
                ChatCompletionUserMessageParam(role="user", content=prompt)
            ]
            # 创建聊天完成请求
            completion = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                # 随机性更小
                temperature=0.1
            )
            # 返回完成结果
            # 如果匹配不到，就是直接检索
            return completion.choices[0].message.content if completion.choices else "直接检索"
        except Exception as e:
            # 记录 API 调用失败
            logger.error(f"DashScope API 调用失败: {e}")
            # 默认返回直接检索，调用失败
            return "直接检索"

    @staticmethod
    def _get_strategy_prompt():
        #   定义私有方法，获取策略选择 Prompt 模板
        return PromptTemplate(
            template="""
            你是一个智能助手，负责分析用户查询: "{query}"，并从以下四种检索增强策略中选择一个最适合的策略，直接返回策略名称，不需要解释过程。

            以下是几种检索增强策略及其适用场景：

            1.  **直接检索：**
                * 描述：对用户查询直接进行检索，不进行任何增强处理。
                * 适用场景：适用于查询意图明确，需要从知识库中检索**特定信息**的问题，例如：
                    * 示例：
                        * 查询：阿奇霉素注射液能和生理盐水配伍吗？
                        * 策略：直接检索
                    * 查询：去乙酰毛花苷（西地兰）和钙剂能同时使用吗？
                        * 策略：直接检索
            2.  **假设问题检索（HyDE）：**
                * 描述：使用 LLM 生成一个假设的答案，然后基于假设答案进行检索。
                * 适用场景：适用于查询较为抽象，直接检索效果不佳的问题，例如：
                    * 示例：
                        * 查询：GLP-1 受体激动剂减轻体重的病理生理机制是什么？
                        * 策略：假设问题检索
            3.  **子查询检索：**
                * 描述：将复杂的用户查询拆分为多个简单的子查询，分别检索并合并结果。
                * 适用场景：适用于查询涉及多个实体或方面，需要分别检索不同信息的问题，例如：
                    * 示例：
                        * 查询：比较布洛芬和对乙酰氨基酚在儿童退热中的安全性与疗效。
                        * 策略：子查询检索
            4.  **回溯问题检索：**
                * 描述：将复杂的用户查询转化为更基础、更易于检索的问题，然后进行检索。
                * 适用场景：适用于查询较为复杂，需要简化后才能有效检索的问题，例如：
                    * 示例：
                        * 查询：孕妇怀孕 28 周出现严重偏头痛，可以服用利扎曲普坦吗？
                        * 策略：回溯问题检索

            根据用户查询 {query}，直接返回最适合的策略名称，例如 "直接检索"。不要输出任何分析过程或其他内容。
            """
            ,
            input_variables=["query"],
        )

    #   定义方法，选择检索策略
    def select_strategy(self, query):
        #   调用 LLM 获取检索策略
        # 1. 初始化提示词
        prompt = self.strategy_prompt_template.format(query=query)
        # 2. 调用LLM执行prompt
        strategy = self.call_dashscope(prompt).strip()
        logger.info(f"为查询 '{query}' 选择的检索策略：{strategy}")
        return strategy


if __name__ == '__main__':
    ss = StrategySelector()
    ss.select_strategy('我要处理一个意图识别的场景，选择bert微调作为模型更好，还是直接使用大模型')

