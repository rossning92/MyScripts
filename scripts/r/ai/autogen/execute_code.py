import os

import autogen
from autogen.coding import LocalCommandLineCodeExecutor

config_list = [{"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")}]


assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={
        "cache_seed": 41,
        "config_list": config_list,
        "temperature": 0,
    },
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "executor": LocalCommandLineCodeExecutor(work_dir="coding"),
    },
)

user_proxy.initiate_chat(
    assistant,
    message="Plot a chart of META and TESLA stock price change YTD. Save the data to stock_price_ytd.csv, and save the plot to stock_price_ytd.png.",
)
