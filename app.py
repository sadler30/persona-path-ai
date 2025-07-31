# app.py

import streamlit as st
from datetime import datetime
import tempfile
import os
import openai
import fitz  # PyMuPDF
from docx import Document

# ------------------------
# 🔐 API Key Setup
# ------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else st.text_input("Enter your OpenAI API Key", type="password")

# ------------------------
# Resume Extractors
# ------------------------
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text_from_pdf(upload):
    text = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(upload.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    for page in doc:
        text += page.get_text()
    os.unlink(tmp_path)
    return text

# ------------------------
# GPT-4 Resume Rewriter with Sections
# ------------------------
def rewrite_resume_with_sections(resume_text, target_role):
    prompt = f"""
You are a professional resume strategist.

Rewrite the following resume to target a job as a {target_role}. Rephrase the resume to align with the role's responsibilities, modern terminology, and impactful bullet points.

Return the rewritten resume structured using the following headers:

## Professional Summary
## Key Experience
## Core Skills

Only include those three sections in your output.

Original Resume:
{resume_text}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()

# ------------------------
# Section Parser
# ------------------------
def parse_resume_sections(resume_text):
    sections = {"Professional Summary": "", "Key Experience": "", "Core Skills": ""}
    current = None
    for line in resume_text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            title = line[3:].strip()
            current = title
        elif current in sections:
            sections[current] += line + "\n"
    return sections

# ------------------------
# Streamlit App
# ------------------------
st.set_page_config(page_title="PersonaPath AI – GPT-Resume Rewriter", page_icon="📄", layout="wide")
st.title("📄 PersonaPath AI – Resume Rewriter with GPT-4")
st.markdown("_Upload your resume, choose a role, and see a smart, structured rewrite._")

# Upload resume
uploaded = st.file_uploader("Upload your resume (.docx or .pdf)", type=["pdf", "docx"])

if uploaded:
    ext = uploaded.name.split(".")[-1]
    if ext == "pdf":
        resume_text = extract_text_from_pdf(uploaded)
    elif ext == "docx":
        resume_text = extract_text_from_docx(uploaded)
    else:
        st.error("Unsupported file format.")
        resume_text = ""

    if resume_text:
        st.success("Resume extracted successfully.")
        st.markdown("### ✍️ Target Role for Rewrite:")
        target_role = st.text_input("Target job title", value="AI Chatbot QA Tester")

        if target_role and openai.api_key:
            if st.button("🔁 Rewrite with GPT-4"):
                with st.spinner("Rewriting resume using GPT-4..."):
                    try:
                        rewritten = rewrite_resume_with_sections(resume_text, target_role)
                        parsed = parse_resume_sections(rewritten)

                        st.markdown("### 🔍 Side-by-Side Resume Comparison")
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("📝 Original Resume")
                            st.text_area("Raw Resume", resume_text, height=400)

                        with col2:
                            st.subheader("✨ Rewritten Resume")
                            for section, content in parsed.items():
                                st.markdown(f"**{section}**")
                                st.text_area(label="", value=content.strip(), height=150)

                        # Save full output
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as tmp:
                            tmp.write(rewritten)
                            tmp_path = tmp.name
                        with open(tmp_path, "rb") as f:
                            st.download_button("📥 Download Rewritten Resume", f, file_name="rewritten_resume.txt")

                    except Exception as e:
                        st.error(f"GPT-4 Error: {e}")
        elif not openai.api_key:
            st.warning("Please enter your OpenAI API key to continue.")
