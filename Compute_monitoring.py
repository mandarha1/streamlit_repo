import json
from snowflake.snowpark import Session
from snowflake.snowpark.functions import *
import pandas as pd
import streamlit as st
from datetime import datetime
from snowflake.snowpark.types import DecimalType
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


st.set_page_config(layout="wide")
st.header("Snowflake Monitoring Framework")


def create_session_object():
    connection_parameters = st.secrets["snowflake"]
    session = Session.builder.configs(connection_parameters).create()
    return session


def aggrid_interactive_table(df: pd.DataFrame):
    """Creates an st-aggrid interactive table based on a dataframe.
    Args:
        df (pd.DataFrame]): Source dataframe
    Returns:
        dict: The selected row
    """
    options = GridOptionsBuilder.from_dataframe(
        df, enableRowGroup=True, enableValue=True, enablePivot=True
    )
    options.configure_side_bar()
    options.configure_selection("single")
    selection = AgGrid(
        df,
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        theme="balham",
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
    )
    return selection

# Create Snowpark DataFrames that loads data from Knoema: Environmental Data Atlas
def wh_data(session):
    # CO2 Emissions by Country
    raw_wh_df =   session.table("WAREHOUSE_METERING_HISTORY")\
                    .select(concat(year(col("START_TIME")),month(col("START_TIME"))).as_("Year-Month"),col("WAREHOUSE_NAME"),lit(col("CREDITS_USED")).cast(DecimalType(10,0)).alias("CREDITS_USED"))
                   #.select(date_trunc("MONTH",col("START_TIME")).as_("QUERY_MONTH"),col("WAREHOUSE_NAME"),lit(col("CREDITS_USED")).cast(DecimalType(10,0)).alias("CREDITS_USED"))
                    #.select(col("WAREHOUSE_NAME"),to_decimal(col("CREDITS_USED"),10,0).as_("CREDITS_USED"))
    raw_wh_df = raw_wh_df.filter(col("WAREHOUSE_NAME").isNotNull())
    raw_wh_df = raw_wh_df.filter(col("CREDITS_USED") > 0)

    
    snow_df_co2 = raw_wh_df.group_by(col("WAREHOUSE_NAME")).agg(sum('CREDITS_USED').as_("Total Credit Consumption"))
    snow_df_co2 = snow_df_co2.select(col("WAREHOUSE_NAME").as_("Warehouse Name"),col("Total Credit Consumption"))
    snow_df_co2 = snow_df_co2.sort(col("Total Credit Consumption").desc())
    snow_df_co2 = snow_df_co2.limit(10)
    #snow_df_co2 = snow_df_co2.to_pandas()

    monthly_df = raw_wh_df.group_by(col("Year-Month")).agg(sum('CREDITS_USED').as_("Total Credit Consumption"))
    monthly_df = monthly_df.filter(col("Total Credit Consumption") > 0)
    monthly_df = monthly_df.sort(col("Year-Month").desc())


    # Convert Snowpark DataFrames to Pandas DataFrames for Streamlit
    #snow_df_co2 = snow_df_co2.to_pandas()

    col1, col2 = st.columns(2)
    with st.container():
        with col1:
            st.markdown("**:blue[Monthly Credit Consumtpion - Table]**")
            #st.dataframe(monthly_df,use_container_width=True)
            pd_monthly_df = pd.DataFrame(monthly_df.collect())
            selection = aggrid_interactive_table(df = pd_monthly_df)
            #st.write(selection)
            
            st.write("---------------------------")
            
            if selection:
                st.write("You selected:")
                #data = st.json(selection["selected_rows"][0])
                #for value in data['Year-Month']:
                 #   print(value, ":", data['Year-Month'][value])
                data = selection["selected_rows"][0]['Year-Month']
                #st.write(data)
                
                
                
            st.markdown("**:blue[Warehouse  Credit Consumtpion - Table]**")
            st.dataframe(snow_df_co2,use_container_width=True)
            
                       
            
        with col2:
            st.markdown("**:red[Monthly Credit Consumtpion - Graph]**")
            df_wh_month = raw_wh_df.filter(col("Year-Month") == data).collect()
            df_wh_month = df_wh_month.group_by(col("WAREHOUSE_NAME")).agg(sum("CREDITS_USED").as_("Total Credit Consumption")).collect()
            st.table(df_wh_month)
            #st.bar_chart(df_wh_month,x="WAREHOUSE_NAME",y="Total Credit Consumption")
            #st.markdown("**:red[Warehouse Credit Consumtpion - Graph]**")
            #st.bar_chart(snow_df_co2,x="Warehouse Name",y="Total Credit Consumption")
            #edited_df = st.experimental_data_editor(snow_df_co2)      
            
            
            
if __name__ == "__main__":
    session = create_session_object()
    wh_data(session)
