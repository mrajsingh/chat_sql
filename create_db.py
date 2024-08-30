import pandas as pd
from sqlalchemy import create_engine

command = "SELECT version();"
DB_URL = ""
engine = create_engine(DB_URL)
connect_str = engine.raw_connection()
cursor = connect_str.cursor()
ret = cursor.execute(command)
print(f'RET {ret}')
connect_str.commit()
cursor.close()
connect_str.close()
data = pd.read_csv('azure.csv')
data.to_sql('performance', engine, if_exists='append', index=False)
