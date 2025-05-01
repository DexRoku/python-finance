import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import base64


# Set the page config
st.set_page_config(page_title="Finance App", page_icon="/Users/dexter/workdi/python-finance/emoji.png", layout="wide")

category_file = "categories.json"

# Load categories from session or file
if "categories" not in st.session_state:
    st.session_state.categories = {"uncategorized": []}

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

# Save categories to file
def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

# Categorize transactions based on user-defined categories
def categorize_transactions(df):
    df["Category"] = "Uncategorized"
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():
            details = row["Description"].lower().strip()
            if any(keyword in details for keyword in lowered_keywords):
                df.at[idx, "Category"] = category
    return df

# Custom styling for the page
page_element = """
<style>
[data-testid="stAppViewContainer"]{
  background-image: url("https://cdn.wallpapersafari.com/88/75/cLUQqJ.jpg");
  background-size: cover;
}
</style>
"""
st.markdown(page_element, unsafe_allow_html=True)

# Load transactions from CSV
def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]

        # Convert date columns to datetime
        df["Booked date"] = pd.to_datetime(df["Booked date"]).dt.date
        df["Amount"] = df["Amount"].astype(float)

        # Display relevant columns only
        st.subheader("Transaction History")
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error processing the csv file: {str(e)}")
        return None

# Add new keyword to category
def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False

# Main app function
def main():
    st.title("Finance Dashboard")

    # Upload file section
    upload_file = st.file_uploader("Upload your bank transaction CSV file", type=["csv"])

    if upload_file is not None:
        df = load_transactions(upload_file)

        if df is not None:
            debits = df[df["Amount"] < 0].copy()
            credits = df[df["Amount"] >= 0].copy()

            st.session_state.debits = debits.copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])

            # Expenses Tab
            with tab1:
                st.subheader("Expenses Summary")
                total_expenses = debits["Amount"].sum()
                st.metric("Total Payments", f"{total_expenses:,.2f} SEK")
                # Add Category
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                # Edit Categories in Expenses
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits[["Booked date", "Description", "Amount", "Category"]],
                    column_config={
                        "Booked date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f SEK"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category", options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if row["Category"] == st.session_state.debits.at[idx, "Category"]:
                            continue
                        description = row["Description"]
                        st.session_state.debits.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, description)

                # Expense Summary and Chart
                st.subheader('Expense Summary')
                category_totals = st.session_state.debits.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(category_totals, use_container_width=True, hide_index=True)

                fig = px.bar(
                    category_totals.sort_values("Amount"),
                    x="Amount",
                    y="Category",
                    orientation='h',
                    text="Category",
                    title="Expenses by Category",
                    labels={"Amount": "Total Expense", "Category": "Category"},
                    color_discrete_sequence=["indianred"]
                )
                fig.update_layout(yaxis_title="", xaxis_title="Amount (SEK)", margin=dict(t=40, b=40))
                fig.update_traces(textposition="outside", hovertemplate='%{y}: %{x:,.2f} SEK<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)

            # Trend Analysis - Line chart
            category_trend = debits.groupby(["Booked date", "Category"])["Amount"].sum().reset_index()
            fig_trend = px.line(
                category_trend,
                x="Booked date",
                y="Amount",
                color="Category",
                title="Expense Trend by Category Over Time",
                line_shape='spline',
                template='plotly_dark',
                markers=True
            )

            fig_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Amount (SEK)",
                xaxis=dict(tickformat="%d/%m/%Y"),
                yaxis=dict(tickprefix="SEK ", autorange="reversed"),
                margin=dict(t=40, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                showlegend=True
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # Payments Tab
            with tab2:
                st.subheader("Payments Summary")
                total_payments = credits["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} SEK")
                st.write(credits)

# Run the main function
if __name__ == "__main__":
    main()
