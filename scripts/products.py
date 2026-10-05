##############################################
# Author: Pavel Kaljunen / pavel@kaljunen.fi #
# Version: 2.2.0                             #
# Last update: 8.9.2025                      #
##############################################

import pandas as pd
import mysql.connector
from datetime import datetime
import os
import pytz
import re

# Define the path to the current directory where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Combine the path to the current directory with the file name
excel_file = os.path.join(current_dir, 'result_with_colors.xlsx')

# Set the connection parameters for the MySQL database
db_params = {
    'host': 'localhost',
    'user': 'decpai_django',
    'password': 'X!%WP25B1=}@',
    'database': 'decpai_django'
}

# Create a connection to the database
connection = mysql.connector.connect(**db_params)
cursor = connection.cursor()

# Load data from the Excel file
df = pd.read_excel(excel_file, header=0)

# Map old product names to unified ones
name_mapping = {
    'BIOCOMPACT 10': 'BIOCOMPACT',
    'BIOCOMPACT 12': 'BIOCOMPACT',
    'BIOCOMPACT 15': 'BIOCOMPACT',
    'BIOCOMPACT ELASTIC 10': 'BIOCOMPACT ELASTIC',
    'BIOCOMPACT ELASTIC 12': 'BIOCOMPACT ELASTIC',
    'BIOCOMPACT ELASTIC 15': 'BIOCOMPACT ELASTIC',
    'BIOCOMPACT SILOSSANICO 12': 'BIOCOMPACT SILOSSANICO',
    'BIOCOMPACT SILOSSANICO 15': 'BIOCOMPACT SILOSSANICO',
    'DUAFLEX 03': 'DUAFLEX',
    'DUAFLEX 07': 'DUAFLEX',
    'Novalis Aggrappante Ecologico': 'Aggrappante Ecologico',
    'STUCCO ROMANO OIKOS': 'Stucco Romano',
    'DRYWALL PAINT BY OIKOS': 'Drywall Paint',
    'ECOSTRIPPER': 'Ekostripper',
    'STUCCO ROMANO OIKOS': 'STUCCO ROMANO',
    'TRAVERTINO TONER ROMANO FINITURA': 'Toner Travertino Romano Finitura',
    'catalogo - listino': 'Efektiharja',
    'spugne': 'Maalaussivellin Pennello Spanga',
    'guanti': 'Sienikäsine',
    'rulli': 'DESIGN ROLLER TP 05',
}

# Apply mapping on PRODUCT column
df['PRODUCT_desc'] = df['PRODUCT_desc'].replace(name_mapping)

# Exclude some products
exclude_products = [
    'cappottini','espositori a terra','espositori da banco','angolari',
    'biocompact silossanico 10','tint. ecs 24 canestri','profili',
    'str. mkt dal vivo altro','mazzette','flyer','depliant','pezzi speciali',
    'brochure','tint. dcs 16 canestri','rete','macchine vernicianti decopaint',
    'minicampionari','access.+ricambi macchine deco paint','bianco salento',
    'apribarattoli','paste col. ecs 24 canestri','paste col. dcs-ecs 16 canestri',
    'compressori aria diretta','book','tasselli','biocompact silossanico 12',
    'biocompact silossanico 15','plus','magliette','campionari',
    'BIOCOMPACT SILOSSANICO','FISIKO','Fundgrap Aggrappante Ecologico',
    'Rasokol Light','Rasokol Calce','Rasokol Flex','Rasokol Top','RINFRESCA',
    'MACCHINE VERNICIANTI DECOPAINT','MACCHINE VERNICIANTI ECOFACADE',
    'MACCHINE VERNICIANTI NOVALIS','ACCESS.+RICAMBI MACCHINE DECO PAINT',
    'ACCESS.+RICAMBI MACCHINE ECOFACADE','ACCESS.+RICAMBI MACCHINE NOVALIS'
]

# Prepare slug, image, thumbnail for PRODUCT
df['slug'] = df['PRODUCT_desc'].apply(lambda x: re.sub(r'\W+', '-', x.lower()) if isinstance(x, str) else x)
df['image_name'] = df['PRODUCT_desc'].apply(lambda x: re.sub(r'\W+', '_', x.lower()) if isinstance(x, str) else x)
df['thumbnail_name'] = df['image_name'] + '_thumbnail'
df['image'] = "products/" + df['image_name'] + '.png'
df['thumbnail'] = "thumbnails/" + df['thumbnail_name'] + '.png'

# Rename columns to database fields
column_mapping = {
    'PRODUCT_desc': 'name',
    'CodiceArticolo_ItemCode': 'sku',
    'slug': 'slug',
    'image': 'image',
    'thumbnail': 'thumbnail',
    'DescrizioneArticolo_ItemDescription': 'description',
    'Prezzo_Price': 'price',
}

df.rename(columns=column_mapping, inplace=True)

# Define database columns including all required fields
db_columns = [
    'name', 'slug', 'image', 'thumbnail', 'description', 
    'price', 'sku', 'properties', 'tech_info'
]

# Default values for missing fields
default_values = {
    'name': 'N/A',
    'slug': 'no-slug',
    'image': 'products/no_image.jpg',
    'thumbnail': 'thumbnails/no_image_thumbnail.jpg',
    'description': '',
    'price': 0.0,
    'sku': '',
    'properties': '',
    'tech_info': '',
    'available': 1,
    'created': datetime.now(pytz.timezone('Europe/Helsinki')).replace(tzinfo=None),
    'updated': datetime.now(pytz.timezone('Europe/Helsinki')).replace(tzinfo=None),
    'discount_percentage': 0,
    'use_color1_palette': 0,  # False
    'use_color2_palette': 1,  # True
    'palette_priority': 'color2',  # Default value from your model
}

# Add missing columns with default values
for col in db_columns + ['available', 'created', 'updated', 'discount_percentage', 'use_color1_palette', 'use_color2_palette', 'palette_priority']:
    if col not in df.columns:
        df[col] = default_values[col]

# Calculate minimum price per product (excluding BASE items)
min_prices = df[df['description'].str.contains('BASE', case=False, na=False) == False] \
    .groupby('name')['price'].min().reset_index()
df = pd.merge(df, min_prices, on='name', how='left', suffixes=('', '_min'))
df.rename(columns={'price_min': 'min_price'}, inplace=True)

# SQL queries
query_select = "SELECT id, name FROM shop_product WHERE name = %s"
query_insert = f"""
    INSERT INTO shop_product (
        {', '.join(db_columns + ['available', 'created', 'updated', 'discount_percentage', 
                                'use_color1_palette', 'use_color2_palette', 'palette_priority', 'multiplier'])}
    ) VALUES ({', '.join(['%s'] * (len(db_columns) + 8))})
"""
query_update = f"""
    UPDATE shop_product
    SET price = %s, updated = %s
    WHERE name = %s
"""
query_min_price = """
    SELECT MIN(v.price) FROM shop_variant v
    JOIN shop_product p ON v.product_id = p.id
    WHERE p.name = %s
"""
query_add_category = """
    INSERT INTO shop_product_category (product_id, category_id)
    VALUES (%s, %s)
"""

# Process in chunks
chunk_size = 1000
chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]

total_rows = 0
start_time = datetime.now()

try:
    for chunk in chunks:
        for _, row in chunk.iterrows():
            if row['name'] in exclude_products:
                print(f"Product '{row['name']}' excluded from loading.")
                continue

            cursor.execute(query_select, (row['name'],))
            existing_product = cursor.fetchone()

            # Get minimal price from variants
            cursor.execute(query_min_price, (row['name'],))
            min_price_result = cursor.fetchone()
            min_price = min_price_result[0] if min_price_result and min_price_result[0] is not None else row['min_price']

            if existing_product:
                # Update only price if product exists
                update_data = (min_price, datetime.now(), row['name'])
                cursor.execute(query_update, update_data)
            else:
                # Insert new product
                insert_data = tuple(
                    row[col] if not pd.isna(row[col]) else default_values[col]
                    for col in db_columns
                ) + (
                    row['available'] if not pd.isna(row['available']) else default_values['available'],
                    row['created'] if not pd.isna(row['created']) else default_values['created'],
                    row['updated'] if not pd.isna(row['updated']) else default_values['updated'],
                    row['discount_percentage'] if not pd.isna(row['discount_percentage']) else default_values['discount_percentage'],
                    row['use_color1_palette'] if not pd.isna(row['use_color1_palette']) else default_values['use_color1_palette'],
                    row['use_color2_palette'] if not pd.isna(row['use_color2_palette']) else default_values['use_color2_palette'],
                    row['palette_priority'] if not pd.isna(row['palette_priority']) else default_values['palette_priority'],
                    1  # multiplier=1
                )
                
                insert_data = list(insert_data)
                price_index = db_columns.index('price')
                insert_data[price_index] = min_price
                insert_data = tuple(insert_data)
                
                cursor.execute(query_insert, insert_data)
                
                # Get the ID of the newly inserted product
                product_id = cursor.lastrowid
                
                # Add relationship to category 95
                cursor.execute(query_add_category, (product_id, 95))

        connection.commit()
        total_rows += len(chunk)
        print(f"Processed {total_rows} rows. Elapsed time: {datetime.now() - start_time}")

except Exception as e:
    print(f"Error: {e}")
    connection.rollback()

finally:
    cursor.close()
    connection.close()

print(f"Loading completed. Total time: {datetime.now() - start_time}")