from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from dotenv import load_dotenv
import sqlite3
import requests
import os
from datetime import datetime
import pytz
load_dotenv()

STOCK_PRICE_API = os.getenv('STOCK_PRICE_API')
WEATHER_API = os.getenv('WEATHER_API_KEY')
# llm=HuggingFaceEndpoint(
#     repo_id='HuggingFaceH4/zephyr-7b-beta',
#     task='text-generation',
#     # provider="hf-inference",
# )

# model = ChatHuggingFace(llm=llm)

model = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash')

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
import operator
from typing import TypedDict, Annotated

from langgraph.graph.message import add_messages

# TOOLS
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def get_stock_price(symbol : str)-> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """

    response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={STOCK_PRICE_API}')
    return response.json()

@tool
def get_weather(city_name: str):
    """
    FETCH WEATHER OF THE CITY USING WEATHER API
    :param city_name: Camel case city name
    :type city_name: str
    """
    json = {
    'key': WEATHER_API,
    'q': city_name
    }
    weather = requests.post('http://api.weatherapi.com/v1/current.json', data=json)
    return weather.json()
@tool
def calculator(first_num: float, second_num: float, operation: str):
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num

        elif operation == "sub":
            result = first_num - second_num

        elif operation == "mul":
            result = first_num * second_num

        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num

        else:
            return {"error": f"Unsupported operation '{operation}'"}

        return {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result
        }

    except Exception as e:
        return {"error": str(e)}

from datetime import datetime
import pytz

@tool
def get_current_datetime(timezone: str = "UTC") -> dict:
    """
    Get current date and time for a given timezone.
    Default timezone is UTC.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return {
            "timezone": timezone,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "iso_datetime": now.isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

tools = [get_stock_price,search_tool, get_weather, calculator, get_current_datetime]

model_with_tools = model.bind_tools(tools)



class chatstate(TypedDict):
    # messages : Annotated[list[BaseMessage], operator.add] this works but we have separerate operater for convesational messages


    messages : Annotated[list[BaseMessage], add_messages]

def chat(state : chatstate):

    messages = state['messages']
    response = model_with_tools.invoke(messages)

    return {
        "messages": [response]
    }

# from langgraph.checkpoint.memory import MemorySaver
# checkpointer  = MemorySaver()

from langgraph.checkpoint.sqlite import SqliteSaver



DBNAME = 'chatbot.db'
conn = sqlite3.connect(
    database=DBNAME,
    check_same_thread=False
)
checkpointer = SqliteSaver(conn=conn)

tool_node = ToolNode(tools)

graph = StateGraph(chatstate)
graph.add_node('chat_node', chat)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools','chat_node')
graph.add_edge('chat_node',END)

chatbot = graph.compile(checkpointer=checkpointer)

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage



# for checkpoint in checkpointer.list(None):
#         thread_id = checkpoint.config['configurable']['thread_id']

#         # ⬇️ correct access
#         channel_values = checkpoint.checkpoint.get("channel_values", {})
#         messages = channel_values.get("messages", [])
#         print(messages)
from langchain_core.messages import HumanMessage

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        thread_id = checkpoint.config['configurable']['thread_id']
        all_threads.add(thread_id)
    return list(all_threads)
