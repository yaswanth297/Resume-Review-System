from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

import streamlit as st
from PIL import Image
import os
import pdf2image
import google.generativeai as genai
import io
import base64
from PyPDF2 import PdfReader
from google.cloud import bigquery
import os
from google.cloud import storage
import toml
from google.oauth2 import service_account

# Load the TOML file
config = toml.load(".streamlit/secrets.toml")

# Get the path from the TOML file
# Load Google Cloud credentials
gcp_service_account = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(gcp_service_account)

client = bigquery.Client(credentials=credentials)
client2 = storage.Client(credentials=credentials)

dataset_id = 'resumes_data'  
table_id = 'data'          
bucket_name = 'resume_bucket_297'

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

input_prompt_name = """
Extract the name of the student from the resume text.
"""

input_prompt_college = """
Extract the college of the student from the resume text.
"""

input_prompt_roll_number = """
Extract the roll number of the student from the resume text."""

input_prompt_branch = """
Extract the engineering branch of the student from the resume text."""

input_prompt_cgpa= """
Extract the CGPA or percentage of the student mentioned in the resume text. Just give the number as output."""

input_prompt_interest = """
Identify the area of interest of the student from the resume text based on the projects mentioned or experiences . Possible areas include Frontend, Backend, Data Science, Data Analyst, or core branches roles like process engineeringetc.
"""
input_prompt_rating = """
Evaluate the resume based on the following criteria:
1. Quality of projects and experiences
2. Presentation and formatting
3. Position of responsibilities under taken
Provide a rating out of 10, considering all these aspects.
Provide only the number and no other information.
"""

def get_gemini_response(input,pdf_content,prompt):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([input,pdf_content,prompt]) # Debugging line
    return response.candidates[0].content.parts[0].text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        reader=PdfReader(uploaded_file)

        text=""

        for page in range(len(reader.pages)):
            page=reader.pages[page]
            text=text+str(page.extract_text())

        return text
    else:
        raise FileNotFoundError("No file uploaded")
    
def upload_to_gcs(file):
    bucket = client2.bucket(bucket_name)
    blob = bucket.blob(file.name)
    
    blob.upload_from_file(file)

    return f"File uploaded to {blob} in bucket {bucket_name}"


st.set_page_config(page_title="ATS Resume EXpert")
st.header("ATS Tracking System")
jd=st.text_area("Job Description: ",key="input")
uploaded_file=st.file_uploader("Upload your resume(PDF)...",type=["pdf"])


if uploaded_file is not None:
    
    st.write("PDF Uploaded Successfully")
    url=f"https://storage.googleapis.com/{bucket_name}/{uploaded_file.name}"
    pdf_content=input_pdf_setup(uploaded_file)
    name_response = get_gemini_response(pdf_content, input_prompt_name,input_prompt_name)
    college_response = get_gemini_response(pdf_content, input_prompt_college,input_prompt_college)
    roll_number_response = get_gemini_response(pdf_content, input_prompt_roll_number,input_prompt_roll_number)
    branch_response = get_gemini_response(pdf_content, input_prompt_branch,input_prompt_branch)
    interest_response = get_gemini_response(pdf_content, input_prompt_interest,input_prompt_interest)
    rating_response = get_gemini_response(pdf_content, input_prompt_rating,input_prompt_rating)
    cgpa_response = get_gemini_response(pdf_content, input_prompt_cgpa,input_prompt_cgpa)
    
    if(len(roll_number_response)>15):
        roll_number_response="NULL"
    if(len(cgpa_response)>15):
        cgpa_response="NULL"

    st.write(f"Name: {name_response.strip()}")
    st.write(f"College: {college_response.strip()}")
    st.write(f"Roll Number: {roll_number_response.strip()}")
    st.write(f"Branch: {branch_response.strip()}")
    st.write(f"Area of Interest: {interest_response.strip()}")
    st.write(f"Rating: {rating_response.strip()}")
    st.write(f"CGPA: {cgpa_response.strip()}")
    table_ref = client.dataset(dataset_id).table(table_id)

    rows_to_insert = [
        {
            "Name ": name_response.strip(),
            "College": college_response.strip(),
            "Roll_Number": roll_number_response.strip(),
            "Branch": branch_response.strip(),
            "CGPA":cgpa_response.strip(),
            "Field_of_Interest": interest_response.strip(),
            "Rating": rating_response.strip(),
            "Resume_Link": url
        }
    ]

    errors = client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        st.write("Encountered errors while inserting rows: {}".format(errors))
    else:
        st.write("Rows have been successfully appended.")



submit1 = st.button("Tell Me About the Resume")

submit2 = st.button("How Can I Improvise my Skills")

submit3 = st.button("Percentage match")

submit4 = st.button("Resources to upskill")

input_prompt1 = """

You are an experienced Technical Human Resource Manager. Your task is to review the provided resume.Give a breif introduction 
about the candidate including his name, education, experiences and skills in one paragraph.Please share your professional evaluation on whether the candidate's profile is technically strong or not. 
Highlight the strengths and weaknesses of the applicant based on the skills and experiences mentioned in the resume. 
Provide an overall assessment of the candidate's technical proficiency with respect to the job description provided finally.
"""

input_prompt2 = """You are an experienced Career Development Coach. Your task is to review the provided resume against
 the job description. Please share your professional evaluation on how the candidate can further develop their skills
   to better align with the role. Highlight the areas where the candidate shows potential and provide specific 
   recommendations for improvement in relation to the specified job requirements."""

input_prompt3 = """
You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS 
functionality, your task is to evaluate the resume against the provided job description. give me the percentage of 
match if the resume matchesthe job description. First the output should come as percentage and then keywords missing
and last final thoughts.
"""

input_prompt4="""
I have a job description and a resume. The job description lists certain skills and qualifications required for the position. 
The resume, however, is missing some of these skills. Please generate a list of the best online resources 
(such as courses, tutorials, books, or articles) that can help someone acquire the missing skills mentioned in the 
job description. Here are the details:

Job Description:

Required Skill 1
Required Skill 2
Required Skill 3
Required Skill 4
Resume:

Existing Skill A
Existing Skill B
Existing Skill C
Missing Skills:

Required Skill 1
Required Skill 3
Please provide links to the best resources for learning these missing skills.
"""



if submit1:
    if uploaded_file is not None:
        pdf_content=input_pdf_setup(uploaded_file)
        response=get_gemini_response(input_prompt1,pdf_content,jd)
        st.subheader("The Repsonse is")
        st.write(response)
    else:
        st.write("Please uplaod the resume")

elif submit2:
    if uploaded_file is not None:
        pdf_content=input_pdf_setup(uploaded_file)
        response=get_gemini_response(input_prompt2,pdf_content,jd)
        st.subheader("The Repsonse is")
        st.write(response)

elif submit3:
    if uploaded_file is not None:
        pdf_content=input_pdf_setup(uploaded_file)
        response=get_gemini_response(input_prompt3,pdf_content,jd)
        st.subheader("The Repsonse is")
        st.write(response)

elif submit4:
    if uploaded_file is not None:
        pdf_content=input_pdf_setup(uploaded_file)
        response=get_gemini_response(input_prompt4,pdf_content,jd)
        st.subheader("The Repsonse is")
    
        st.write(response)
else:
    st.write("Please uplaod the resume")
