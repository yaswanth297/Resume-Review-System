from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import streamlit as st
from PIL import Image
import os
import pdf2image
import google.generativeai as genai
import io
import base64
from PyPDF2 import PdfReader
from google.cloud import bigquery, storage
from google.oauth2 import service_account

# Load Google Cloud credentials
gcp_service_account = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(gcp_service_account)

client = bigquery.Client(credentials=credentials)
client2 = storage.Client(credentials=credentials)

dataset_id = 'resumes_data'
table_id = 'data'
bucket_name = 'resume_bucket_297'

def upload_to_gcs(bucket_name, source_file, destination_blob_name):
    bucket = client2.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(source_file)
    return f"File uploaded to {destination_blob_name} in bucket {bucket_name}"

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

input_prompts = {
    "name": "Extract the name of the student from the resume text.",
    "college": "Extract the college of the student from the resume text.",
    "roll_number": "Extract the roll number of the student from the resume text. If not found, give only 'NULL' as output.",
    "branch": "Extract the engineering branch of the student from the resume text.",
    "interest": "Identify the area of interest of the student from the resume text. Possible areas include Frontend, Backend, Data Science, Data Analyst, etc.",
    "rating": "Evaluate the resume based on the following criteria: 1. Quality of projects and experiences 2. Presentation and formatting 3. Position of responsibilities undertaken. Provide a rating out of 10, considering all these aspects. Provide only the number and no other information."
}

def get_gemini_response(pdf_content, prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([pdf_content, prompt])
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "No response received from model."
    except Exception as e:
        return f"An error occurred: {e}"

@st.cache_data
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    else:
        raise FileNotFoundError("No file uploaded")

st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

jd = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")
    # Uncomment to enable uploading to GCS
    # destination_blob_name = uploaded_file.name
    # upload_to_gcs(bucket_name, uploaded_file, destination_blob_name)
    
    url = f"https://storage.googleapis.com/{bucket_name}/{uploaded_file.name}"
    
    pdf_content = input_pdf_setup(uploaded_file)
    
    responses = {
        "Name": get_gemini_response(pdf_content, input_prompts["name"]),
        "College": get_gemini_response(pdf_content, input_prompts["college"]),
        "Roll Number": get_gemini_response(pdf_content, input_prompts["roll_number"]),
        "Branch": get_gemini_response(pdf_content, input_prompts["branch"]),
        "Area of Interest": get_gemini_response(pdf_content, input_prompts["interest"]),
        "Rating": get_gemini_response(pdf_content, input_prompts["rating"])
    }

    st.write(f"Name: {responses['Name'].strip()}")
    st.write(f"College: {responses['College'].strip()}")
    st.write(f"Roll Number: {responses['Roll Number'].strip()}")
    st.write(f"Branch: {responses['Branch'].strip()}")
    st.write(f"Area of Interest: {responses['Area of Interest'].strip()}")
    st.write(f"Rating: {responses['Rating'].strip()}")

    table_ref = client.dataset(dataset_id).table(table_id)
    rows_to_insert = [{
        "Name": responses['Name'].strip(),
        "College": responses['College'].strip(),
        "Roll_Number": responses['Roll Number'].strip(),
        "Branch": responses['Branch'].strip(),
        "Field_of_Interest": responses['Area of Interest'].strip(),
        "Rating": responses['Rating'].strip(),
        "Resume_Link": url
    }]

    try:
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            st.error(f"Encountered errors while inserting rows: {errors}")
        else:
            st.success("Rows have been successfully appended.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

submit1 = st.button("Tell Me About the Resume")
submit2 = st.button("How Can I Improvise my Skills")
submit3 = st.button("Percentage match")
submit4 = st.button("Resources to upskill")

if submit1:
    if uploaded_file is not None:
        response = get_gemini_response(pdf_content, input_prompts["name"] + jd)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.write("Please upload the resume")

elif submit2:
    if uploaded_file is not None:
        response = get_gemini_response(pdf_content, input_prompts["college"] + jd)
        st.subheader("The Response is")
        st.write(response)

elif submit3:
    if uploaded_file is not None:
        response = get_gemini_response(pdf_content, input_prompts["roll_number"] + jd)
        st.subheader("The Response is")
        st.write(response)

elif submit4:
    if uploaded_file is not None:
        response = get_gemini_response(pdf_content, input_prompts["branch"] + jd)
        st.subheader("The Response is")
        st.write(response)
else:
    st.write("Please upload the resume")

