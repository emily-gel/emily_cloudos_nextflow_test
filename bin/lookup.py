#!/usr/bin/env python3
import click
from sqlalchemy import create_engine, event, text
import pandas as pd
import numpy as np

@click.command()
@click.option(
    "--participant_id",
    type=int,
    required=True,
)

def query(participant_id: int):

    version = "source_data_100kv16_covidv4"
    
    def query_to_df(sql_query, version):
        dbname = "gel_clinical_cb_sql_pro"
        host = "clinical-cb-sql-pro.cfe5cdx3wlef.eu-west-2.rds.amazonaws.com"
        port = 5432
        password = 'anXReTz36Q5r'
        user = 'jupyter_notebook'
        engine = create_engine(f'''postgressql://{user}:{password}@{host}:{port}/{database}''')

        @event.listens_for(engine, "connect", insert=True)
        def set_search_path(dbapi_connection, connection_record):
            existing_autocommit = dbapi_connection.autocommit
            dbapi_connection.autocommit = True
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET SESSION search_path={version}")
            cursor.close()
            dbapi_connection.autocommit = existing_autocommit
        
        with engine.connect as connection:
            result = connection.execute(text(sql_query))
            return(pd.DataFrame(result))
    
    hes_sql = (f'''
        SELECT participant_id, arrivaldate, diag_all
        FROM hes_ae
        WHERE participant_id = {participant_id}
        ''')

    hes_query = query_to_df(hes_sql, version)
    hes_query.to_csv("output.tsv", sep="\t", index=False)

    # out = open("output.txt", "w") 
    # out.write(hes_query) 
    # out.close()

if __name__ == "__main__":
    query()
