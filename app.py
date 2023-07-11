import pandas as pd
import streamlit as st
from streamlit_card import card
import plotly.express as px

st.set_page_config(page_title="Toy Store Dashboard", page_icon=None, layout="wide", menu_items=None)

@st.cache_data
def load_data():
    inventory = pd.read_csv('inventory.csv')
    products = pd.read_csv('products.csv')
    sales = pd.read_csv('sales.csv')
    stores = pd.read_csv('stores.csv')

    df = pd.merge(pd.merge(sales, products, on='Product_ID'), stores, on='Store_ID')
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    df['Date'] = pd.to_datetime(df['Date'])
    df['Product_Price'] = df['Product_Price'].str.replace('$', '').astype(float)
    df['Product_Cost'] = df['Product_Cost'].str.replace('$', '').astype(float)

    product_table = pd.DataFrame()
    product_table = df.groupby(['Product_Name', 'Product_Category']).max('Product_Price')[['Product_Price', 'Product_Cost']].reset_index()
    product_table['Units_Sold'] = df.groupby(['Product_Name','Product_Category']).sum('Units')[['Units']].reset_index(drop=True)
    product_table['Revenue'] = product_table['Units_Sold'] * product_table['Product_Price']
    product_table['Profit'] = (product_table['Product_Price'] - product_table['Product_Cost']) * product_table['Units_Sold']

    category_table = product_table.groupby('Product_Category').sum('Revenue').reset_index()

    return df, product_table, category_table

df, product_table, category_table = load_data()

def format_number(number):
    if abs(number) >= 1e9:
        return f'{round(number/1e9, 2)}B'
    elif abs(number) >= 1e6:
        return f'{round(number/1e6, 2)}M'
    elif abs(number) >= 1e3:
        return f'{round(number/1e3, 2)}K'
    else:
        return str(number)
    
def create_card(title, value):
    st.markdown(
        """
        <div class="card card-border">
            <div class="card-body">
                <h5 class="card-title">{}</h5>
                <h3 class="card-text">{}</h3>
            </div>
        </div>
        """.format(title, value),
        unsafe_allow_html=True
    )

# Add CSS styles for card border and hover animation
st.markdown(
    """
    <style>
        .card-body{
            display: flex;
            flex-direction: column;
        }
        .card-border {
            border: 0;
            border-radius: 2px;
            padding: 10px;
            transition: box-shadow 0.3s ease-in-out;
            box-shadow: 0 0 3px rgba(0, 0, 0, 0.3);
        }
        
        # .card-border:hover {
        #     box-shadow: 0 0 10px 30px rgba(0, 0, 0, 0.3);
        # }
        .card-text{
            text-align: center;
            font-family: montserrat;
            width: max-content;
            transition: scale 200ms,
                        text-shadow 200ms,
                        transform 100ms;

        }
        .card-body:hover .card-text{
            scale: 1.1;
            color: green;
            transform: translateX(1rem);
            text-shadow: 0 0 1px rgba(0, 0, 0, .6);

        }

    </style>
    """,
    unsafe_allow_html=True
)
### KPI
total_product = df['Product_Name'].nunique()
top_sold_product = product_table.sort_values(by = 'Profit', ascending = False)['Product_Name'].head(1).to_string(index=False)
total_Category = df['Product_Category'].nunique()   
top_sold_category = product_table.sort_values(by = 'Profit', ascending = False)['Product_Category'].head(1).to_string(index=False)

### Product Analysis
product = 'Action Figure'
revenue = product_table[product_table['Product_Name'] == product]['Revenue'].astype(str)
revenue = format_number(float(revenue))
profit = product_table[product_table['Product_Name'] == product]['Profit'].astype(str)
profit = format_number(float(profit))

### Title
st.title(':blue[Toy Store] Analysis')
st.divider()

### Card Visual - line - 1 
total_product_card, total_Category_card, revenue_card, profit_card = st.columns(4)

with total_product_card:
    with st.container():
        create_card('Total Products', f'{total_product}')
with total_Category_card:
    with st.container():
        create_card('Total Categories', f'{total_Category}')
with revenue_card:
    with st.container():
        create_card('Revenue', f'{revenue}')
with profit_card:
    with st.container():
        create_card('Profit', f'{profit}')

st.divider()

slicer_col_1, slicer_col_2 = st.columns([1,4])

with slicer_col_1:
    chosen_metric_1 = st.selectbox('Choose a Metric: ', ('Revenue', 'Profit', 'Units_Sold'))

# Sort the product_table by the chosen metric in descending order
sorted_product_table = product_table.sort_values(by=chosen_metric_1, ascending=False)

# Get the top 5 products
top_5_products = sorted_product_table.head(5)

chart_title_1, chart_title_2 = st.columns(2)

with chart_title_1:
    st.subheader(f'Top 5 Products by {chosen_metric_1}')
with chart_title_2:
    st.subheader(f'{chosen_metric_1} by Categories')

chart_columns_1, chart_columns_2 = st.columns(2)

with chart_columns_1:
    product_chart_1 = px.bar(top_5_products,
                             x='Product_Name', y=chosen_metric_1)
    product_chart_1.update_layout(plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
                                  bargap=0.1, xaxis_title='Products', yaxis_title=chosen_metric_1)
    product_chart_1.update_traces(width=0.5, texttemplate='%{text}', textposition='inside',
                                  text=[format_number(num) for num in top_5_products[chosen_metric_1]])
    product_chart_1.update_xaxes(showgrid=False)
    product_chart_1.update_yaxes(showgrid=False)
    st.plotly_chart(product_chart_1, use_container_width=True)

with chart_columns_2:
    total_value = category_table[chosen_metric_1].sum()
    category_chart_1 = px.pie(category_table,
                              values=chosen_metric_1,
                              names='Product_Category')
    category_chart_1.update_traces(textposition='outside', textinfo='label+text',
                                   text=[format_number(num) for num in category_table[chosen_metric_1]])
    category_chart_1.update(layout_showlegend=False)
    category_chart_1.update_traces(hole=.4, hoverinfo="label+percent+name")
    category_chart_1.update_layout(annotations=[dict(text=f'Total<br>{format_number(total_value)}', x=0.5, y=0.5, font_size=20, showarrow=False)])
    st.plotly_chart(category_chart_1, use_container_width=True)

st.divider()

chosen_year_col, chosen_metric_col, dummycolumn = st.columns([1, 1, 2])   

with chosen_year_col:
    chosen_year = st.selectbox('Choose a Year: ', (df['Year'].unique()))
with chosen_metric_col:
    chosen_metric = st.selectbox('Choose a Metric: ', ('Sales', 'Profit', 'Units Sold'))

selected_year = df[df['Year'] == chosen_year]
monthly_sales = selected_year.groupby(selected_year['Date'].dt.to_period('M'))[['Product_Price', 'Product_Cost', 'Units']].sum().reset_index()
monthly_sales['Date'] = monthly_sales['Date'].astype(str)

st.divider()

## ******************************************************Line Charts Sales Section******************************************************
if chosen_metric == 'Sales':
    st.subheader(f'Sales Over Month for {chosen_year}')
    sales_over_year = px.line(monthly_sales, x='Date', y='Product_Price', markers=True, text='Product_Price')
    sales_over_year.update_layout(showlegend=False,
                                  yaxis=dict(showgrid=False),
                                  xaxis=dict(showgrid=False,
                                             dtick='M1',
                                             tickformat='%b'))
    sales_over_year.update_traces(texttemplate='%{text:.2s}', textposition='top center', line_shape='spline')
    sales_over_year.update_yaxes(tickformat=".2s", hoverformat=".2s")
    st.plotly_chart(sales_over_year, use_container_width=True)

elif chosen_metric == 'Profit':
    st.subheader(f'Profit Over Month for {chosen_year}')
    profit_over_year = px.line(monthly_sales, x='Date', y=monthly_sales['Product_Price'] - monthly_sales['Product_Cost'], markers=True, text='Product_Price')
    profit_over_year.update_layout(showlegend=False, 
                                   yaxis=dict(showgrid=False),
                                   xaxis=dict(showgrid=False, 
                                              dtick='M1', 
                                              tickformat='%b'))
    profit_over_year.update_traces(texttemplate='%{text:.2s}', textposition='top center', line_shape='spline')
    profit_over_year.update_yaxes(tickformat=".2s", hoverformat=".2s")
    st.plotly_chart(profit_over_year, use_container_width=True)

elif chosen_metric == 'Units Sold':
    st.subheader(f'Units Sold Over Month for {chosen_year}')
    unit_over_year = px.line(monthly_sales, x='Date', y=monthly_sales['Units'], markers=True, text='Product_Price')
    unit_over_year.update_layout(showlegend=False, 
                                 yaxis=dict(showgrid=False),
                                 xaxis=dict(showgrid=False, 
                                            dtick='M1', 
                                            tickformat='%b'))
    unit_over_year.update_traces(texttemplate='%{text:.2s}', textposition='top center', line_shape='spline')
    unit_over_year.update_yaxes(tickformat=".2s", hoverformat=".2s")
    st.plotly_chart(unit_over_year, use_container_width=True)
st.divider()
