# https://python.langchain.com/docs/integrations/tools/search_tools/
# https://python.langchain.com/docs/integrations/tools/google_serper/

from langchain.agents import AgentType, initialize_agent, load_tools
from langchain_openai import OpenAI

llm = OpenAI(temperature=0)
tools = load_tools(["google-serper"], llm=llm)
agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)
agent.run("how to become a reviewer for conference?")
