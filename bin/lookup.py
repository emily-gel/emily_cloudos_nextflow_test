#!/usr/bin/env python3
import click
import psycopg2
import pandas as pd
import numpy as np

@click.command()
@click.option(
    "--participant_id",
    type=int,
    required=True,
)

def query_to_df(sql_query, database):
    connection = psycopg2.connect(
        dbname = "gel_clinical_cb_sql_pro",
        options = f"-c search_path=source_data_100kv16_covidv4",
        host = "clinical-cb-sql-pro.cfe5cdx3wlef.eu-west-2.rds.amazonaws.com",
        port = 5432,
        password = 'anXReTz36Q5r',
        user = 'jupyter_notebook'
    )
    return(pd.read_sql_query(sql_query, connection))

def query(participant_id: int):

    version = "source_data_100kv16_covidv4"
    
    hes_sql = (f'''
        SELECT participant_id, arrivaldate, diag_all
        FROM hes_ae
        WHERE participant_id = {participant_id}
        ''')

    hes_query = query_to_df(hes_sql, version)
    hes_query

    out = open("output.txt", "w") 
    out.write(hes_query) 
    out.close()

if __name__ == "__main__":
    query()
