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

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_gemini_response(input,pdf_content,prompt):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([input,pdf_content,prompt])
    return response.text

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

st.set_page_config(page_title="ATS Resume EXpert")
st.header("Resume Review System")
jd=st.text_area("Job Description: ",key="input")
uploaded_file=st.file_uploader("Upload your resume(PDF)...",type=["pdf"])


if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")


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
