import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import base64
import openai

# Set the page config first
st.set_page_config(page_title="Finance App", page_icon="/Users/dexter/workdi/python-finance/emoji.png", layout="wide")

# Then add the custom styling
page_element = """
<style>
[data-testid="stAppViewContainer"]{
  background-image: url("https://cdn.wallpapersafari.com/88/75/cLUQqJ.jpg");
  background-size: cover;
}
</style>
"""

st.markdown(page_element, unsafe_allow_html=True)



def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]

        # Optional: Convert date columns to datetime
        df["Booked date"] = pd.to_datetime(df["Booked date"]).dt.date
        df["Amount"] = df["Amount"].astype(float)

        # Display relevant columns only
        st.subheader("Transaction History")
        st.dataframe(df[["Booked date", "Description", "Amount", "Booked balance"]])
        return df
    except Exception as e:
        st.error(f"Error processing the csv file: {str(e)}")
        return None


def main():
    st.title("Finance Dashboard")

    upload_file = st.file_uploader("Upload your bank transaction CSV file", type=["csv"])

    if upload_file is not None:
        df = load_transactions(upload_file)


main()
