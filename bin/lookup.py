#!/usr/bin/env python3
import os
import click
# import psycopg2
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

dbname = os.getenv("DB_NAME")
options = os.getenv("DB_OPTIONS")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

# Ensure that the environment variables are set
if not all([dbname, options, user, password, host, port]):
    raise ValueError("One or more environment variables are not set. Please check your .env file.")

# Define the function to query the database and return a DataFrame  
def query_to_df(sql_query, database, user, password, host, port, options):
    """
    function to execute a SQL query and return the result as a pandas DataFrame.
    
    input:
    sql_query: str; The SQL query to execute.
    database: str; The name of the database to connect to.

    output:
    returns a pandas DataFrame containing the result of the SQL query.
    """
    # connection = psycopg2.connect(
    #     dbname = "gel_clinical_cb_sql_pro",
    #     options = f"-c search_path=source_data_100kv16_covidv4",
    #     host = "clinical-cb-sql-pro.cfe5cdx3wlef.eu-west-2.rds.amazonaws.com",
    #     port = 5432,
    #     password = 'anXReTz36Q5r',
    #     user = 'jupyter_notebook'
    # )
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}",
        connect_args={"{options}": f"-c search_path={database}"})

    return(pd.read_sql_query(sql_query, connection))

def query(participant_id: int):
    """
    function to query HES data for a given participant_id.

    input:
    participant_id: int; The ID of the participant to query.

    output: 
    writes the query result to a file named "output.tsv".
    """
    version = "source_data_100kv16_covidv4"
    
    hes_sql = (f'''
        SELECT participant_id, arrivaldate, diag_all
        FROM hes_ae
        WHERE participant_id = {participant_id}
        ''')

    hes_query = query_to_df(hes_sql, version)
    hes_query.to_csv("output.tsv", sep="\t", index=False)


@click.command()
@click.option(
    "--participant_id",
    type=int,
    required=True,
)
def main(participant_id: int):
    """
    main function to query HES data for a given participant_id.
    """
    query(participant_id)

if __name__ == "__main__":
    query()
