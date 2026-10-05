##############################################
# Author: Pavel Kaljunen / pavel@kaljunen.fi #
# Version: 1.0.0                             #
# Last update: 30.1.2024                     #
##############################################

import pandas as pd
import mysql.connector
from datetime import datetime
import os
import pytz

# Define the path to the current directory where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Combine the path to the current directory with the file name
excel_file = os.path.join(current_dir, 'wtf.xlsx')

# Set the connection parameters for the MySQL database
db_params = {
    'host': 'localhost',
    'user': 'decopaint',
    'password': 'acidpax9520',
    'database': 'decopaint'
}

# Create a connection to the database
connection = mysql.connector.connect(**db_params)
cursor = connection.cursor()

# Define the starting and ending rows
start_row = 30  # starting row
end_row = 31  # ending row

# Load data from the Excel file with specified starting and ending rows
df = pd.read_excel(excel_file, header=0, skiprows=range(1, start_row-1), nrows=end_row - start_row+1)

# Name of column where to replace spaces
columns_to_strip = ['FORMATO']

# Remove spaces from values in the specified columns
for column in columns_to_strip:
    df[column] = df[column].replace('\\s', '', regex=True)

df['slug'] = df['PRODOTTO']
# List of columns where to replace spaces and convert to lowercase
columns_to_slug = ['slug']

# Replace spaces with hyphens and convert to lowercase for specified columns
for column in columns_to_slug:
    df[column] = df[column].apply(lambda x: x.replace(' ', '-').lower() if isinstance(x, str) else x)

df['image'] = df['slug'].astype(str)
current_date = datetime.now()
df['image'] = "products/{}/{:02d}/{:02d}/".format(current_date.year, current_date.month, current_date.day) + df['slug'] + '.jpg'

# Rename DataFrame columns according to the database
column_mapping = {
    'PRODOTTO': 'name',
    'slug': 'slug',
    'image': 'image',
    'DescrizioneArticolo_ItemDescription': 'description',
    'Prezzo_Price': 'price',
    'available': 'available',
    'created': 'created',
    'updated': 'updated',
    'category_id': 'category_id',
    'DIVISIONE': 'cat_name'
}

# Get the list of columns from the database
db_columns = list(column_mapping.values())

# Rename DataFrame columns according to the order in the database
df.rename(columns=column_mapping, inplace=True)

# Set default values for missing columns
default_values = {
    'name': 'No name',
    'slug': 'No-slug',
    'image': 'products/2024/01/27/ecosmalto-metallizzato-metalloitumaali_2_AkAvoou.png',
    'description': 'No description available',
    'price': 0.0,
    'available': 1,
    'created': datetime.now(pytz.timezone('Europe/Helsinki')).replace(tzinfo=None),
    'updated': datetime.now(pytz.timezone('Europe/Helsinki')).replace(tzinfo=None),
    'category_id': 3,
    'product_id': 'N/A'
}

# Check for missing columns and add them with default values
for col in db_columns:
    if col not in df.columns:
        df[col] = default_values[col]

# Split the DataFrame into chunks
chunk_size = 1000
chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]

total_rows = 0
start_time = datetime.now()

query = f"INSERT INTO shop_product ({', '.join(db_columns)}) VALUES ({', '.join(['%s'] * len(db_columns))})"

try:
    for i, chunk in enumerate(chunks):
        try:
            # Convert data to a list of tuples, using default values for missing columns
            data = [tuple(row[col] if not pd.isna(row[col]) else default_values[col] for col in db_columns) for _, row in chunk.iterrows()]

            if not data:
                continue  # Skip empty data

            # Batch insert into the shop_product table
            cursor.executemany(query, data)
            connection.commit()
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            print(f"Parameters in SQL query: {', '.join(db_columns)}")
            print(f"SQL query: {query}")
            print(f"Parameters in SQL query: {data}")
            connection.rollback()

        total_rows += len(chunk)
        print(f"Processed {total_rows} rows. Elapsed time: {datetime.now() - start_time}")

except Exception as e:
    print(f"An error occurred: {e}")

# Close the connection in the finally block
finally:
    cursor.close()
    connection.close()

print(f"Loading completed. Total time: {datetime.now() - start_time}")