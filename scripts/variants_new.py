##############################################
# Author: Pavel Kaljunen / pavel@kaljunen.fi #
# Version: 3.0.5                             #
# Last update: 17.10.2025                    #
##############################################

import pandas as pd
import mysql.connector
from datetime import datetime
import os
import re

# Define the path to the current directory where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Combine the path to the current directory with the file name
excel_file = os.path.join(current_dir, 'imperium.xlsx')

# Set the connection parameters for the MySQL database
db_params = {
    'host': 'localhost',
    'user': 'decpai_django',
    'password': 'X!%WP25B1=}@',
    'database': 'decpai_django'
}

# FILTER SETTINGS - Set these to True/False to enable/disable filters
APPLY_BIANCA_FILTER = False      # Apply white color detection
APPLY_GRAIN_FILTER = False       # Apply grain detection  
APPLY_GLOSS_FILTER = False       # Apply gloss detection
APPLY_BASE_FILTER = False        # Apply base detection

# PRODUCT FILTER - Enter product name to load only its variants, leave empty for all products
TARGET_PRODUCT_NAME = ""        # Example: "BIOCOMPACT" or "" for all products

# Create a connection to the database
connection = mysql.connector.connect(**db_params)
cursor = connection.cursor()

# Load data from the Excel file
df = pd.read_excel(excel_file, header=0)

# Print column names to debug
print("Excel-tiedoston sarakkeet:", df.columns.tolist())

# Define the mapping between fields in the file and fields in the database
field_mapping = {
    'CodiceArticolo_ItemCode': 'item_code',
    'DescrizioneArticolo_ItemDescription': 'item_description',
    'Barcode': 'barcode',
    'Prezzo_Price': 'price',
    'CATEGORY_desc': 'cat_name',
    'Size': 'size',
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
    'TRAVERTINO TONER ROMANO FINITURA': 'Toner Travertino Romano Finitura',
    'catalogo - listino': 'Efektiharja',
    'spugne': 'Maalaussivellin Pennello Spanga',
    'guanti': 'Sienikäsine',
    'rulli': 'DESIGN ROLLER TP 05',
}

# Determine the correct column name for product
product_column = 'PRODUCT_desc'

if product_column in df.columns:
    df[product_column] = df[product_column].replace(name_mapping)
    print(f"Käytetään tuotesaraketta: {product_column}")
else:
    print("Varoitus: Tuotesaraketta ei löytynyt. Saatavilla olevat sarakkeet:", df.columns.tolist())

excluded_item_names = [
    'cappottini',
    'espositori a terra',
    'espositori da banco',
    'angolari',
    'biocompact silossanico 10',
    'tint. ecs 24 canestri',
    'profili',
    'str. mkt dal vivo altro',
    'mazzette',
    'flyer',
    'depliant',
    'pezzi speciali',
    'brochure',
    'tint. dcs 16 canestri',
    'rete',
    'macchine vernicianti decopaint',
    'minicampionari',
    'access.+ricambi macchine deco paint',
    'bianco salento',
    'apribarattoli',
    'paste col. ecs 24 canestri',
    'paste col. dcs-ecs 16 canestri',
    'compressori aria diretta',
    'book',
    'tasselli',
    'biocompact silossanico 12',
    'biocompact silossanico 15',
    'plus',
    'magliette',
    'campionari',
    'BIOCOMPACT SILOSSANICO',
    'FISIKO',
    'Fundgrap Aggrappante Ecologique',
    'Rasokol Light',
    'Rasokol Calce',
    'Rasokol Flex',
    'Rasokol Top',
    'RINFRESCA',
    'MACCHINE VERNICIANTI DECOPAINT',
    'MACCHINE VERNICIANTI ECOFACADE',
    'MACCHINE VERNICIANTI NOVALIS',
    'ACCESS.+RICAMBI MACCHINE DECO PAINT',
    'ACCESS.+RICAMBI MACCHINE ECOFACADE',
    'ACCESS.+RICAMBI MACCHINE NOVALIS'
]

total_rows = 0
start_time = datetime.now()

def safe_int(val):
    """Convert value to integer safely, return None if conversion fails"""
    try:
        return int(val) if pd.notna(val) else None
    except (ValueError, TypeError):
        return None

def safe_float(val):
    """Convert value to float safely, return None if conversion fails"""
    try:
        return float(val) if pd.notna(val) else None
    except (ValueError, TypeError):
        return None

def safe_str(val):
    """Convert value to string safely, return empty string if value is NaN"""
    return str(val).strip() if pd.notna(val) else ''

def format_color_filename(color_name):
    """Remove spaces from color name and format for filename"""
    if not color_name:
        return ""
    # Remove all spaces and special characters that might cause issues in filenames
    cleaned_name = re.sub(r'\s+', '', color_name)
    # Remove any other potentially problematic characters
    cleaned_name = re.sub(r'[^\w\-_]', '', cleaned_name)
    return cleaned_name

def has_bianco_in_description(description):
    """
    Check if description contains 'bianco' in any form (case insensitive)
    """
    if not description:
        return False
    return bool(re.search(r'bianco', description, re.IGNORECASE))

def is_bianco_with_3xx_number(description):
    """
    Check if description contains 'bianco' followed by 3-digit number starting with 3
    """
    if not description:
        return False
    
    # Pattern to find 'bianco' followed by space and 3-digit number starting with 3
    pattern = r'bianco\s*3\d{2}\b'
    
    return bool(re.search(pattern, description, re.IGNORECASE))

def has_color_defined(color1_value, color2_value):
    """
    Check if item already has color defined (either Color1 or Color2)
    """
    return bool(color1_value or color2_value)

def process_color_for_bianco(color1_value, color2_value, r_value, g_value, b_value, hue_value):
    """
    Process colors for items with 'bianco' in description
    Returns modified color values for white color
    """
    # If there's Color1 (image-based color), use white image
    if color1_value:
        image_value = "color_images/VALKOINEN.jpg"
        thumbnail_value = "color_thumbnails/VALKOINEN_thumbnail.jpg"
        color1_value = "Valkoinen"
        color2_value = ""  # Clear color2 for image-based colors
        r_value = None
        g_value = None
        b_value = None
        hue_value = None
    # If there's Color2 (RGB color), use white RGB values
    elif color2_value:
        image_value = None
        thumbnail_value = None
        color1_value = ""  # Clear color1 for RGB colors
        color2_value = "Valkoinen"
        r_value = 255  # White RGB values
        g_value = 255
        b_value = 255
        hue_value = 0.0  # Hue for white
    # If no color specified, set as white RGB
    else:
        image_value = None
        thumbnail_value = None
        color1_value = ""
        color2_value = "Valkoinen"
        r_value = 255
        g_value = 255
        b_value = 255
        hue_value = 0.0
    
    return color1_value, color2_value, image_value, thumbnail_value, r_value, g_value, b_value, hue_value

# Display filter settings
print("\n--- SUODATINASETUKSET ---")
print(f"Valkoinen väritunnistus: {'PÄÄLLÄ' if APPLY_BIANCA_FILTER else 'POIS PÄÄLTÄ'}")
print(f"Grain-tunnistus: {'PÄÄLLÄ' if APPLY_GRAIN_FILTER else 'POIS PÄÄLTÄ'}")
print(f"Gloss-tunnistus: {'PÄÄLLÄ' if APPLY_GLOSS_FILTER else 'POIS PÄÄLTÄ'}")
print(f"Base-tunnistus: {'PÄÄLLÄ' if APPLY_BASE_FILTER else 'POIS PÄÄLTÄ'}")
if TARGET_PRODUCT_NAME:
    print(f"Tuotesuodatin: {TARGET_PRODUCT_NAME}")
else:
    print("Tuotesuodatin: KAIKKI TUOTTEET")
print("-------------------------\n")

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
                # Get product name from the correct column
                prodotto_value = safe_str(row[product_column])
                
                if not prodotto_value:
                    print(f"Varoitus: Tuotteen nimeä ei löytynyt tuotteelle {item_code_value}")
                    continue

                # Apply product filter if specified
                if TARGET_PRODUCT_NAME and prodotto_value != TARGET_PRODUCT_NAME:
                    continue

                query = f"SELECT id FROM shop_product WHERE name = %s"
                cursor.execute(query, (prodotto_value,))
                result = cursor.fetchone()

                if result:
                    product_id = result[0]

                    item_description_value = safe_str(row['DescrizioneArticolo_ItemDescription'])
                    
                    # Apply gloss detection filter
                    gloss_value = ""
                    if APPLY_GLOSS_FILTER:
                        for word, gloss in gloss_mapping.items():
                            if word in item_description_value:
                                gloss_value = gloss
                                break

                    # Apply base detection filter
                    base_value = ""
                    if APPLY_BASE_FILTER:
                        for word, base_word in base_mapping.items():
                            if re.search(r'\b{}\b'.format(re.escape(word)), item_description_value, re.IGNORECASE):
                                base_value = base_word
                                break

                    # Apply grain detection filter
                    grain_value = ""
                    if APPLY_GRAIN_FILTER:
                        if prodotto_value in excluded_item_names:
                            grain_value = ''
                        else:
                            # Check for "A" followed by 03, 07, 10, 12, 15 with or without space
                            if re.search(r'\bA\s*(03|07|10|12|15)\b', item_description_value, re.IGNORECASE):
                                grain_value = ''
                            else:
                                match = re.search(r'\s(03|07|10|12|15)\s', item_description_value)
                                grain_value = match.group(1) if match else ''

                    active = True
                    
                    # Get original color values
                    color1_value = safe_str(row.get('Color1', ''))
                    color2_value = safe_str(row.get('Color2', ''))
                    
                    # Initialize color variables
                    image_value = None
                    thumbnail_value = None
                    r_value = None
                    g_value = None
                    b_value = None
                    hue_value = None
                    
                    # Apply bianca (white color) detection filter
                    if APPLY_BIANCA_FILTER and has_bianco_in_description(item_description_value):
                        # Check if it's Bianco with 3XX number AND already has color defined
                        if is_bianco_with_3xx_number(item_description_value) and has_color_defined(color1_value, color2_value):
                            # Skip setting Valkoinen for Bianco 3XX that already has color
                            print(f"Ohitettu: Bianco 3XX väri jo määritelty tuotteelle {item_code_value}: {item_description_value}")
                            # Process normal colors for this item
                            if color1_value:
                                color_filename = format_color_filename(color1_value)
                                if color_filename:
                                    image_value = f"color_images/{color_filename}.jpg"
                                    thumbnail_value = f"color_thumbnails/{color_filename}_thumbnail.jpg"
                            if color2_value:
                                r_value = safe_int(row.get('R'))
                                g_value = safe_int(row.get('G'))
                                b_value = safe_int(row.get('B'))
                                hue_value = safe_float(row.get('Hue'))
                        else:
                            # Process colors for white variant (either not Bianco 3XX or Bianco 3XX without color)
                            color1_value, color2_value, image_value, thumbnail_value, r_value, g_value, b_value, hue_value = process_color_for_bianco(
                                color1_value, color2_value, r_value, g_value, b_value, hue_value
                            )
                            if is_bianco_with_3xx_number(item_description_value):
                                print(f"Valkoinen väri asetettu (ei väriä): Bianco 3XX tuotteelle {item_code_value}: {item_description_value}")
                            else:
                                print(f"Valkoinen väri asetettu tuotteelle {item_code_value}: {item_description_value}")
                    else:
                        # Handle normal Color1 (image-based colors)
                        if color1_value:
                            # Format color name for filename - remove spaces and add .jpg extension
                            color_filename = format_color_filename(color1_value)
                            if color_filename:
                                image_value = f"color_images/{color_filename}.jpg"
                                thumbnail_value = f"color_thumbnails/{color_filename}_thumbnail.jpg"
                            else:
                                print(f"Varoitus: Virheellinen värienimi '{color1_value}' tuotteelle {item_code_value}")
                        
                        # Handle normal Color2 (RGB colors)
                        if color2_value:
                            r_value = safe_int(row.get('R'))
                            g_value = safe_int(row.get('G'))
                            b_value = safe_int(row.get('B'))
                            hue_value = safe_float(row.get('Hue'))
                    
                    # Collect values from Excel according to mapping
                    variant_data = tuple(
                        row[file_field] if pd.notna(row[file_field]) else None
                        for file_field, db_field in field_mapping.items()
                        if file_field in ['CodiceArticolo_ItemCode', 'Barcode', 'Prezzo_Price', 'CATEGORY_desc', 'Size', 'CustomsCode', 'Peso_Weight']
                    )
                    
                    # Insert item_description at the correct position (after item_code)
                    variant_data_list = list(variant_data)
                    variant_data_list.insert(1, item_description_value)  # Insert description after item_code
                    variant_data = tuple(variant_data_list)
                    
                    # Add color1 and color2 fields, then remaining fields
                    variant_data += (
                        color1_value,          # color1 from Excel (original value with spaces)
                        color2_value,          # color2 from Excel
                        grain_value,
                        image_value,           # Will be None for Color2 items
                        thumbnail_value,       # Will be None for Color2 items
                        product_id,
                        gloss_value,
                        active,
                        base_value,
                        False,                 # order_item
                        r_value,               # Will be None for Color1 items
                        g_value,               # Will be None for Color1 items
                        b_value,               # Will be None for Color1 items
                        hue_value              # Will be None for Color1 items
                    )

                    # Updated variant columns including color1 and color2
                    variant_columns = [
                        'item_code', 'item_description', 'barcode', 'price', 'cat_name', 'size', 'customs_code', 'weight',
                        'color1', 'color2', 'grain', 'image', 'thumbnail', 'product_id', 'gloss', 'active', 'base', 'order_item',
                        'r', 'g', 'b', 'hue'
                    ]

                    variant_query = f"INSERT INTO shop_variant ({', '.join(variant_columns)}) VALUES ({', '.join(['%s'] * len(variant_columns))})"
                    cursor.execute(variant_query, variant_data)
                    connection.commit()

        total_rows += len(chunk)
        print(f"Käsitelty {total_rows} riviä. Kulunut aika: {datetime.now() - start_time}")

except mysql.connector.Error as err:
    print(f"Virhe: {err}")
    connection.rollback()

except Exception as e:
    print(f"Tapahtui virhe: {e}")

# Close the connection
cursor.close()
connection.close()

print(f"Lataus valmis. Kokonaisaika: {datetime.now() - start_time}")