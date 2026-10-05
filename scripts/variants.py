##############################################
# Author: Pavel Kaljunen / pavel@kaljunen.fi #
# Version: 1.0.0                             #
# Last update: 24.2.2024                     #
##############################################

import pandas as pd
import mysql.connector
from datetime import datetime
import os
import re

# Define the path to the current directory where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Combine the path to the current directory with the file name
excel_file = os.path.join(current_dir, 'wtf.xlsx')

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

# Load data from the Excel file with specified starting and ending rows
df = pd.read_excel(excel_file, header=0)

# Replace 'LT' with 'L' in the 'size' column
df['FORMATO'] = df['FORMATO'].str.replace('LT', 'L')

# Replace 'BIANCO' with 'VALKOINEN' in the 'color' column
df['CLA3_senza_spazi'] = df['CLA3_senza_spazi'].str.replace('BIANCO', 'VALKOINEN')
# Replace 'BIANCO' with 'VALKOINEN' in the 'color' column
df['CLA3_senza_spazi'] = df['CLA3_senza_spazi'].str.replace('P/VALKOINEN', 'VALKOINEN')

# Define the mapping between fields in the file and fields in the database
field_mapping = {
    'CodiceArticolo_ItemCode': 'item_code',
    'DescrizioneArticolo_ItemDescription': 'item_description',
    'Barcode': 'barcode',
    'Prezzo_Price': 'price',
    'DIVISIONE': 'cat_name',
    'CLA3_senza_spazi': 'color',
    'FORMATO': 'size',
    'CustomsCode': 'customs_code',
    'Peso_Weight': 'weight',
}

# Define the mapping between words in item_description and the gloss field
gloss_mapping = {
    'LUCID': 'Kiiltävä',
    'SATIN': 'Puolikiiltävä',
    'OPACO': 'Himmeä',
}

# Define the mapping between words in item_description and fields to add to the database
base_mapping = {
    'BASE': 'base',
    'GOLD': 'Kulta',
    'GREY': 'Harmaa',
    'NERO': 'Musta',
    'ORO': 'Kullattu',
    'ROSSO': 'Rose',
    'SILVER': 'Hopea',
}

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
    'TRAVERTINO TONER ROMANO FINITURA': 'TRAVERTINO ROMANO FINITURA',
}

df['PRODOTTO'] = df['PRODOTTO'].replace(name_mapping)

excluded_item_names = [
    'MARMORINO NATURALE',
    'MARMORINO NATURALE FINE',
    'ENCANTO',
    'BIOCOMPACT SILOSSANICO', 
    'FISIKO', 
    'Fundgrap Aggrappante Ecologico', 
    'Rasokol Light',
    'Rasokol Calce', 
    'Rasokol Flex', 
    'Rasokol Top', 
    'RINFRESCA', 
    'TOOLS', 
    'MACCHINE VERNICIANTI DECOPAINT', 
    'MACCHINE VERNICIANTI ECOFACADE',
    'MACCHINE VERNICIANTI NOVALIS',
    'ACCESS.+RICAMBI MACCHINE DECO PAINT',
    'ACCESS.+RICAMBI MACCHINE ECOFACADE',
    'ACCESS.+RICAMBI MACCHINE NOVALIS'
]

total_rows = 0
start_time = datetime.now()

# Iterate through the rows of the DataFrame in chunks
try:
    chunk_size = 1000
    for i in range(0, df.shape[0], chunk_size):
        chunk = df.iloc[i:i + chunk_size]

        # Extract all unique 'item_code' values in the current chunk
        unique_item_codes = set(chunk['CodiceArticolo_ItemCode'])

        # Query the shop_variant table to find existing 'item_code' values
        existing_item_codes_query = f"SELECT item_code FROM shop_variant WHERE item_code IN ({', '.join(['%s']*len(unique_item_codes))})"
        cursor.execute(existing_item_codes_query, tuple(unique_item_codes))
        existing_item_codes = set(result[0] for result in cursor.fetchall())

        for _, row in chunk.iterrows():
            item_code_value = row['CodiceArticolo_ItemCode']

            if item_code_value not in existing_item_codes:
                # 'item_code' doesn't exist in shop_variant, proceed with insertion
                
                prodotto_value = row['PRODOTTO']
                query = f"SELECT id FROM shop_product WHERE name = %s"
                cursor.execute(query, (prodotto_value,))
                result = cursor.fetchone()

                if result:
                    product_id = result[0]  # Extracting product_id from the query result

                    # Extract the 'CLA3_senza_spazi' value
                    color_name_value = row['CLA3_senza_spazi']

                    # Formulate the 'image' and 'thumbnail' field values
                    image_value = f"color_images/{color_name_value}.jpg"
                    thumbnail_value = f"color_thumbnails/{color_name_value}_thumbnail.jpg"

                    # Extract the 'DescrizioneArticolo_ItemDescription' value
                    item_description_value = row['DescrizioneArticolo_ItemDescription']

                    # Initialize the gloss value
                    gloss_value = ""
                    # Check for the presence of keywords from the mapping in item_description
                    for word, gloss in gloss_mapping.items():
                        if word in item_description_value:
                            gloss_value = gloss
                            break

                    # Check for the presence of whole words from the base_mapping in item_description
                    base_value = ""
                    for word, base_word in base_mapping.items():
                        # Using \b to match whole words
                        if re.search(r'\b{}\b'.format(re.escape(word)), item_description_value, re.IGNORECASE):
                            base_value = base_word
                            break

                    # Check if the current product name is in the excluded list
                    if prodotto_value in excluded_item_names:
                        grain_value = ''
                    else:
                        # Check if ' 03 ', ' 07 ', ' 10 ', ' 12 ', or ' 15 ' is present in the description
                        match = re.search(r'\s(03|07|10|12|15)\s', item_description_value)
                        if match:
                            grain_value = match.group(1)
                        else:
                            grain_value = ''

                    # Create a list of words to check
                    #words_to_check = ['A', 'B', 'AB', 'BC', 'AD', 'D', 'TB', 'I', 'TRNEW', 'P', 'TR']
                    words_to_check = []

                    # Check each word from the list in the string
                    for word in words_to_check:
                        # Create a regular expression pattern to match a whole word
                        pattern = r'\b{}\b'.format(re.escape(word))
                        # Convert color_name_value to string if it's not already
                        if not isinstance(color_name_value, str):
                            color_name_value = str(color_name_value)
                        # Check if the word is present in the string
                        if re.search(pattern, color_name_value):
                            # If the word is found, set 'active' to False and exit the loop
                            active = False
                            break
                    else:
                        # If none of the words are found, set 'active' to True
                        active = True

                    # Add 'grain' and 'image' fields to variant_data tuple
                    variant_data = tuple(row[file_field] if pd.notna(row[file_field]) else None for file_field, db_field in field_mapping.items())
                    variant_data += (grain_value, image_value, thumbnail_value, product_id, gloss_value, active, base_value)

                    # Add 'grain' and 'image' fields to variant_columns list
                    variant_columns = list(field_mapping.values()) + ['grain', 'image', 'thumbnail', 'product_id', 'gloss', 'active', 'base']

                    variant_query = f"INSERT INTO shop_variant ({', '.join(variant_columns)}) VALUES ({', '.join(['%s'] * len(variant_columns))})"
                    cursor.execute(variant_query, variant_data)

                    connection.commit()

        total_rows += len(chunk)
        print(f"Processed {total_rows} rows. Elapsed time: {datetime.now() - start_time}")

except mysql.connector.Error as err:
    print(f"Error: {err}")
    connection.rollback()

except Exception as e:
    print(f"An error occurred: {e}")

# Close the connection
cursor.close()
connection.close()

print(f"Loading completed. Total time: {datetime.now() - start_time}")
