from utils.api import (
    single_conversation,  # 单次对话请求
    multi_conservation,  # 多并行对话请求
    single_embedding,  # 单次文本嵌入请求
    multi_embedding,  # 多文本嵌入请求
    multiroundConversation,  # 多轮对话
)

import multiprocessing as mp

if __name__ == "__main__":
    mp.freeze_support()
    # 单一请求测试
    system_prompt = "You are a helpful assistant.You are good at telling jokes."
    user_input = "Tell me a joke."
    response = single_conversation(
        system_prompt, user_input, need_json=False, show_progress=True
    )
    print("Response:", response)

    # 多并行请求测试
    system_prompt = ["You are a helpful assistant.You are good at telling jokes."] * 4
    user_input = ["Tell me a joke."] * 4
    response = multi_conservation(
        system_prompt, user_input, need_json=[False] * 4, show_progress=True
    )
    print("Response:", response)

    # 多轮对话测试

    conversation = multiroundConversation("你是一个有趣的助手，你擅长讲笑话。")
    conversation.add_user_input("记住这个数字：123456")
    response = conversation.get_response(need_json=False)
    print("Response:", response)
    conversation.add_user_input("现在请重复这个数字")
    print(conversation.conversation)
    response = conversation.get_response(need_json=False)
    print("Response:", response)

    # 单一文本嵌入尝试
    text = "This is a test sentence for embedding."
    embedding = single_embedding(text)
    print("Embedding:", embedding)

    # 多文本嵌入尝试

    texts = [
        "This is the first test sentence.",
    ] * 2
    # 警告：此处发现并发数>=3会报错 code=11202
    embeddings = multi_embedding(texts)
    print("Embeddings:", embeddings)
