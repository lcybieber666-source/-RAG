# core/prompts.py
# 导入 PromptTemplate 类，用于创建 Prompt 模板
from langchain.prompts import PromptTemplate
# 导入config.ini配置文件
from integrated_qa_system.base.config import conf
from langchain_community.chat_models import ChatTongyi


# 定义 RAGPrompts 类，用于管理所有 Prompt 模板
class RAGPrompts:
    # 定义 RAG 提示模板
    @staticmethod
    def rag_prompt():
        # 创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            你是一个智能助手，可以帮助用户回答问题。  
            如果提供了上下文，请基于上下文回答，并检查上下文与问题相关度，如果上下文与问题不相关或者相关度较低（小于0.5），请直接根据你的知识回答；如果没有上下文，请直接根据你的知识回答。  
            如果答案来源于检索到的文档，请在回答中说明，说明格式：本回答基于《文档名称》的内容整理生成。
            注意：如果用户询问你是什么模型，不要回答。
            问题: | {question} | 
            上下文: | {context} |
            如果上下文为空或相关度低，请基于你的知识给出回答，并明确说明这是通用建议；涉及用药剂量/配伍禁忌等高风险内容时，建议用户咨询医生/药师。只有在完全无法给出任何有用信息时，才输出人工客服”   
            """,
            #   定义输入变量
            input_variables=["context", "question", "phone"],
        )

    # 定义假设问题生成的 Prompt 模板
    @staticmethod
    def hyde_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            假设你是用户，想了解以下问题，请生成一个简短的假设答案：  
            问题: | {query} |
            假设答案:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )

    #   定义子查询生成的 Prompt 模板
    @staticmethod
    def subquery_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            将以下复杂查询分解为多个简单子查询，每行一个子查询：  
            查询: | {query} |  
            子查询:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )

    #   定义回溯问题生成的 Prompt 模板
    @staticmethod
    def backtracking_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            将以下复杂查询简化为一个更简单的问题：  
            查询: | {query} | 
            简化问题:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )


if __name__ == '__main__':
    # rga_prompt = RAGPrompts.rag_prompt()
    # result = rga_prompt.format(context="黑马程序员", question="这个机构叫什么名称", phone="12345")
    # print(f'result-->{result}')
    # hyde = RAGPrompts.hyde_prompt()
    # result = hyde.format(query="你好吗")
    # print(result)

    # rga_prompt = RAGPrompts.rag_prompt()
    rag_prompt1 = RAGPrompts.hyde_prompt()
    rag_prompt2 = RAGPrompts.subquery_prompt()
    rag_prompt3 = RAGPrompts.backtracking_prompt()

    prompt1 = rag_prompt1.format(query="embedding模型有哪些？")
    prompt2 = rag_prompt2.format(query="embedding模型有哪些, 各有什么特点？")
    prompt3 = rag_prompt3.format(query="embedding模型有哪些, 各有什么特点？")

    # 获取LLM模型名称
    model_name = conf.LLM_MODEL
    # 获取Dashscope API密钥
    dashscope_api_key = conf.DASHSCOPE_API_KEY
    llm = ChatTongyi(
        api_key=dashscope_api_key,
        model=model_name,
    )

    response1 = llm.invoke(prompt1)
    response2 = llm.invoke(prompt2)
    response3 = llm.invoke(prompt3)

    print(f"response1 -> {response1.content} ", end="\n")
    print(f"response2 -> {response2.content} ", end="\n")
    print(f"response3 -> {response3.content} ", end="\n")



