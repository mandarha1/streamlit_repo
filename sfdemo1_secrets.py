import json
from snowflake.snowpark import Session
from snowflake.snowpark.functions import *
import pandas as pd
import streamlit as st


st.set_page_config(layout="wide")
st.header("Snowflake Monitoring Framework")


def create_session_object():
    connection_parameters = st.secrets["snowflake"]
    session = Session.builder.configs(connection_parameters).create()
    return session


# Create Snowpark DataFrames that loads data from Knoema: Environmental Data Atlas
def load_data(session):
    # CO2 Emissions by Country
    snow_df_co2 = session.table("WAREHOUSE_METERING_HISTORY").select(col("WAREHOUSE_NAME"),to_decimal(col("CREDITS_USED"),10,0).as_("CREDITS_USED"))
    snow_df_co2 = snow_df_co2.filter(col("WAREHOUSE_NAME").isNotNull())
    snow_df_co2 = snow_df_co2.group_by(col("WAREHOUSE_NAME")).agg(sum('CREDITS_USED').as_("Total Credit Consumption"))
    snow_df_co2 = snow_df_co2.sort(col("Total Credit Consumption").desc())
    snow_df_co2 = snow_df_co2.limit(10)

    # Convert Snowpark DataFrames to Pandas DataFrames for Streamlit
    #snow_df_co2 = snow_df_co2.to_pandas()

    col1, col2 = st.columns(2)
    with st.container():
        with col1:
            st.write('Top 10 Credit Consuming Warehouses - Table')
            st.dataframe(snow_df_co2)
                       
            
        with col2:
            st.write('Top 10 Credit Consuming Warehouses - Graph')
            st.bar_chart(snow_df_co2,x="WAREHOUSE_NAME")
            #edited_df = st.experimental_data_editor(snow_df_co2)                  
            
            
if __name__ == "__main__":
    session = create_session_object()
    load_data(session)
