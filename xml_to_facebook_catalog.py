import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from io import BytesIO

st.title("XML/Excel/Google Sheets Product Feed to Meta/Facebook Catalog CSV")

# --- Input: XML Feed URL
xml_url = st.text_input("Paste XML Feed URL (e.g., Shopify Facebook Feed):", "")

# --- Input: Excel File Upload
excel_file = st.file_uploader("Or upload an Excel file", type=["xlsx", "xls"])

# --- Input: Google Sheets URL
gsheet_url = st.text_input("Or paste a Google Sheets URL (must be public or shared with 'Anyone with the link'):", "")

def gsheet_to_csv_url(url):
    # Handles both /edit and /view links
    if '/edit' in url:
        url = url.split('/edit')[0]
    elif '/view' in url:
        url = url.split('/view')[0]
    return url + '/export?format=csv'

# Define your required columns
csv_columns = [
    'id', 'title', 'description', 'availability', 'condition', 'price', 'link', 'image_link', 'brand',
    'google_product_category', 'fb_product_category', 'quantity_to_sell_on_facebook', 'sale_price',
    'sale_price_effective_date', 'item_group_id', 'gender', 'color', 'size', 'age_group', 'material',
    'pattern', 'shipping', 'shipping_weight', 'gtin', 'video[0].url', 'video[0].tag[0]',
    'product_tags[0]', 'product_tags[1]', 'style[0]'
]

# --- Excel file processing
if excel_file is not None:
    try:
        df_excel = pd.read_excel(excel_file)
        st.write("Excel file uploaded. Preview:", df_excel.head())
        # Attempt to reindex to match the required columns (missing columns will be empty)
        df_out = df_excel.reindex(columns=csv_columns)
        st.write("Preview (mapped to Facebook Catalog format):", df_out.head())
        csv_bytes = df_out.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name="facebook_catalog.csv",
            mime='text/csv'
        )
    except Exception as e:
        st.error(f"Error processing Excel file: {e}")

# --- Google Sheets processing
elif gsheet_url:
    try:
        st.write("Downloading Google Sheet as CSV...")
        csv_url = gsheet_to_csv_url(gsheet_url)
        df_gsheet = pd.read_csv(csv_url)
        st.write("Google Sheet loaded. Preview:", df_gsheet.head())
        df_out = df_gsheet.reindex(columns=csv_columns)
        st.write("Preview (mapped to Facebook Catalog format):", df_out.head())
        csv_bytes = df_out.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name="facebook_catalog.csv",
            mime='text/csv'
        )
    except Exception as e:
        st.error(f"Error processing Google Sheet: {e}")

# --- XML file processing
elif xml_url:
    try:
        # Download XML
        st.write("Downloading XML feed...")
        resp = requests.get(xml_url)
        resp.raise_for_status()
        xml_content = resp.content
        
        # Debug: Show XML content length
        st.write(f"XML content length: {len(xml_content)} bytes")
        
        # Parse XML
        try:
            root = ET.fromstring(xml_content)
            st.write("Successfully parsed XML structure")
            st.write(f"Root tag: {root.tag}")
            channel = root.find('channel')
            if channel is None:
                st.error("No 'channel' element found in XML. Please check if this is a valid product feed.")
                st.write("Available root elements:", [child.tag for child in root])
                raise ValueError("Missing 'channel' element")
            items = channel.findall('item')
            st.write(f"Found {len(items)} items in the feed")
            if len(items) == 0:
                st.error("No items found in the XML feed. Please check if the feed is empty or has a different structure.")
                st.write("Available elements in channel:", [child.tag for child in channel])
                raise ValueError("No items found in feed")

            # Namespace for Google fields
            ns = {'g': 'http://base.google.com/ns/1.0'}

            # Updated get_text function
            def get_text(item, tag):
                # Try with namespace
                if tag.startswith('g:'):
                    el = item.find(tag, ns)
                else:
                    el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ''

            rows = []
            for item in items:
                row = {
                    'id': get_text(item, 'g:id') or get_text(item, 'id'),
                    'title': get_text(item, 'g:title') or get_text(item, 'title'),
                    'description': get_text(item, 'g:description') or get_text(item, 'description'),
                    'availability': get_text(item, 'g:availability') or get_text(item, 'availability'),
                    'condition': get_text(item, 'g:condition') or get_text(item, 'condition'),
                    'price': get_text(item, 'g:price') or get_text(item, 'price'),
                    'link': get_text(item, 'g:link') or get_text(item, 'link'),
                    'image_link': get_text(item, 'g:image_link') or get_text(item, 'image_link'),
                    'brand': get_text(item, 'g:brand') or get_text(item, 'brand'),
                    'google_product_category': get_text(item, 'g:google_product_category') or get_text(item, 'google_product_category'),
                    'fb_product_category': '',
                    'quantity_to_sell_on_facebook': get_text(item, 'quantity_to_sell_on_facebook'),
                    'sale_price': get_text(item, 'g:sale_price') or get_text(item, 'sale_price'),
                    'sale_price_effective_date': get_text(item, 'g:sale_price_effective_date') or get_text(item, 'sale_price_effective_date'),
                    'item_group_id': get_text(item, 'g:item_group_id') or get_text(item, 'item_group_id'),
                    'gender': get_text(item, 'g:gender') or get_text(item, 'gender'),
                    'color': get_text(item, 'g:color') or get_text(item, 'color'),
                    'size': get_text(item, 'g:size') or get_text(item, 'size'),
                    'age_group': get_text(item, 'g:age_group') or get_text(item, 'age_group'),
                    'material': get_text(item, 'g:material') or get_text(item, 'material'),
                    'pattern': get_text(item, 'g:pattern') or get_text(item, 'pattern'),
                    'shipping': get_text(item, 'g:shipping') or get_text(item, 'shipping'),
                    'shipping_weight': get_text(item, 'g:shipping_weight') or get_text(item, 'shipping_weight'),
                    'gtin': get_text(item, 'g:gtin') or get_text(item, 'gtin'),
                    'video[0].url': '',
                    'video[0].tag[0]': '',
                    'product_tags[0]': get_text(item, 'g:product_type') or get_text(item, 'product_type'),
                    'product_tags[1]': '',
                    'style[0]': '',
                }
                rows.append(row)

            # DataFrame and CSV Download
            df_out = pd.DataFrame(rows, columns=csv_columns)
            st.write("Preview:", df_out.head())

            csv_bytes = df_out.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name="facebook_catalog.csv",
                mime='text/csv'
            )

        except Exception as e:
            st.error(f"Error parsing XML: {e}")

    except Exception as e:
        st.error(f"Error downloading XML: {e}")

st.markdown("""
---
**Instructions:**
1. Paste your XML Feed URL (Shopify Facebook/Google format), upload an Excel file, or paste a Google Sheets URL (must be public/shared).
2. Wait for processing.
3. Preview the result and download as CSV (Meta Catalog ready).
""")
