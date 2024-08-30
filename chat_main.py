import pandas as pd
from sqlalchemy import create_engine

from langchain import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_ollama import ChatOllama
import chainlit as cl
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import PromptTemplate


dialect = "PostgreSQL"
table_info = None
input_question = "What is the maximum min_cpu?"
top_k = 100


@cl.on_chat_start
def on_chat_start():

    engine = create_engine('postgresql+psycopg2://postgres:test@localhost:5432/performance')
    llm = ChatOllama(model="llama3:latest")
    sql_database = SQLDatabase(engine)
    table_info = sql_database.get_table_info()

    template = '''Given an input question, first interpret it and extract the required column. Then, create a syntactically correct 
    {dialect} query to run, execute the query and return the result.

    Given a natural language question, follow these steps:

    1. Generate a syntactically correct SQL query to answer the question.
    2. Ensure that column names and table names are used without unnecessary quotes unless required by SQL syntax for your specific database.
    3. Use single quotes only for string literals and not for column or table names.
    4. Provide the query in the SQLQuery section. Do not include extra or unnecessary quotes.

    Use the following format:

    Question: "Question here"
    SQLQuery: SQL Query to run
    SQLResult: "Result of the SQLQuery"

    Only use the following tables:

    {table_info}.

    Example for SQLQuery: 
    SELECT timestamp, min_cpu
    FROM performance
    ORDER BY min_cpu
    LIMIT 20;

    Question: {input}
    '''

    prompt_temp = PromptTemplate.from_template(template)

    sql_chain = SQLDatabaseChain.from_llm(llm, db=sql_database, verbose=True, return_direct=True, prompt=prompt_temp)

    if sql_chain:
        print(f'L is not ')
    cl.user_session.set("chain",sql_chain)
    cl.user_session.set("db", sql_database)
    cl.user_session.set("llm_chat", llm)

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")

    response = chain.invoke({"query": message.content})

    print(f'Response {response}')
    q = message.content

    querry_result = response["result"]
    
    llm_chat = cl.user_session.get("llm_chat")
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system", 
                "You are helpful assistance that interprets the question and data given and explains it to user. "
                "You understand the context from the question and explain the result in simple words. Don't make up the explanation if you do not understand.",
            ),
            ("human", "Question is {input} and the result of the SQL is {querry_res}"),
        ]
    )
    formatted_prompt = prompt.format_messages(
        querry_res=querry_result,
        input=q
    )
    res = llm_chat(messages=formatted_prompt)

    await cl.Message(content=res.content).send()
