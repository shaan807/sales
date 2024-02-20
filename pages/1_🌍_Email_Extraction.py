import streamlit as st
import leafmap.foliumap as leafmap
import os
import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image
import re
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
load_dotenv()

api = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api)  

model = genai.GenerativeModel('gemini-pro')

markdown = """
Web App URL: <https://geotemplate.streamlit.app>
GitHub Repository: This Product is Under Development
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)


#st.title("Email Extraction")

#col1, col2 = st.columns([4, 1])
#options = list(leafmap.basemaps.keys())
#index = options.index("OpenTopoMap")

#with col2:

#    basemap = st.selectbox("Select a basemap:", options, index)


#with col1:

#    m = leafmap.Map(locate_control=True, latlon_control=True, draw_export=True, minimap_control=True)
#    m.add_basemap(basemap)
#    m.to_streamlit(height=700)

output_path = "images"

def pdf_to_images(pdf_file, output_path):
    images = convert_from_bytes(pdf_file.read())
    for i, image in enumerate(images):
        image_path = os.path.join(output_path, f'page_{i+1}.jpg')
        image.save(image_path, 'JPEG')

def delete_images(output_path):
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith('.jpg'):
            os.remove(file_path)

def get_gemini_response(input, image):
    vmodel = genai.GenerativeModel('gemini-pro-vision')
    response = vmodel.generate_content([input, image])
    return response.text

def extract_company_details(response):
    # Use regular expression to extract company details
    pattern = r".+?,.+?,.+?,.+"  
    matches = re.findall(pattern, response)
    # Split each match into a list of four elements
    matches = [match.split(",") for match in matches]
    # Filter out rows with null values
    matches = [match for match in matches if not any(field.strip().lower() == 'na' for field in match)]
    return matches

custom_inst = '''Extract company details including company names, email addresses, phone numbers, and website links in comma-separated format. Ensure accuracy and refrain from including any additional information beyond the CSV format.

Desired Output Format:
Company name, Email address, Phone Number, Website

For Example:
Apple Inc., info@apple.com, +1-(800)-555-9876, www.apple.com
Google, info@google.com, +929168551364, www.google.com

Please provide only the necessary details as mentioned above. Do not include any additional information such as page numbers or any other extraneous content.
'''

st.title("Company Details Extractor")

pdf_files = st.file_uploader("Choose multiple pdf files...", type="pdf", accept_multiple_files=True)

responses = []

if pdf_files:
    for pdf_file in pdf_files:
        pdf_to_images(pdf_file, output_path)
        # Process images in the 'images' folder
        image_folder = "images"

        if os.path.exists(image_folder):
            st.write(f"Processing images from PDF: {pdf_file.name}")
            for filename in os.listdir(image_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    st.write(f"Processing image: {filename}")
                    image_path = os.path.join(image_folder, filename)
                    image = Image.open(image_path)
                    input_text = custom_inst  # Set your input text here
                    img_response = get_gemini_response(input_text, image)
                    responses.extend(extract_company_details(img_response))

    # Write all responses to a CSV file
    if responses:
        df = pd.DataFrame(responses, columns=["Company name", "Email address", "Phone Number", "Website"])
        st.write(df)

        # Save dataframe to CSV file
        csv_file_path = "gemini_responses.csv"
        df.to_csv(csv_file_path, index=False)
        st.write(f"Responses saved to CSV file: {csv_file_path}")
    else:
        st.write("No responses found to save.")

    delete_images(output_path)
