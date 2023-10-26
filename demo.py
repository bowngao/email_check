import os
import io
import streamlit as st
import PyPDF2
import base64
import requests
from dotenv import load_dotenv
import json
from genai.schemas import GenerateParams
from genai.model import Model
from genai.credentials import Credentials
load_dotenv()
api_key = os.getenv("GENAI_KEY")
api_url = os.getenv("GENAI_API")

st.set_page_config(page_title="Multi-Document Chat Bot", page_icon=":books:")
st.title("Contract Advisor 🤖")
st.subheader("Powered by IBM WatsonX")
preview_tab, result_tab = st.tabs(["Contract Preview", "Result"])



def pdf_preview(pdf_data):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(base64.b64decode(pdf_data)))
    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        page_text = page.extract_text()
        st.text(page_text)


with preview_tab:
    with st.sidebar:
        st.title('🤗💬Please upload your file here.')
        st.write('Advisor Bot based on uploaded documents')
        # methods = ['QA based on uploaded documents']
        # qa_method = st.sidebar.radio('Pick a method', methods)
        # Display file upload fields
        contract_file = st.file_uploader("Upload Contract PDF File", type="pdf")
        email_file = st.file_uploader("Upload Email Text File", type="txt")

        file_path = "./data/Quote Contract.pdf"  # Default value for file_path

        if contract_file:
            temp_file_save = "data/"
            os.makedirs(temp_file_save, exist_ok=True)  # Create the 'data/' directory if it doesn't exist
            uploaded_file_path = os.path.join(temp_file_save, contract_file.name)
            with open(uploaded_file_path, "wb") as f:
                f.write(contract_file.getbuffer())
            file_path = f.name
            st.session_state["pdf"] = ""
        else:
            st.session_state.pdf_processed = False
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            src = base64_pdf
    pdf_preview(src)


    st.sidebar.markdown('''
                ## About
                This app is an LLM-powered chatbot built using:
                - [WatsonX](https://dataplatform.cloud.ibm.com/wx/home?context=wx)
                ''')

with result_tab:
    # Check if files are uploaded
    if contract_file is not None and email_file is not None:
        # Read contract PDF file and extract text
        contract_pdf_path = "temp_contract.pdf"
        with open(contract_pdf_path, "wb") as file:
            file.write(contract_file.read())

        with open(contract_pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            contract_text = ""
            for page in reader.pages:
                contract_text += page.extract_text()

        # Read email content from TXT file
        email_content = email_file.read()

        # Prepare template and generate response
        prompt_template = '''
        Obtain the context of discount percentage requests of products via email.
        Obtain the context of agreed discount of those products on contract. 
        Compare discounts for those products.
        The result of comparison should look like below:
        Product List #1:
        - Product Name: [Product Name]
        - Product Quantity: [Quantity]
        - discount on contract: [discount request from vender] %
        - Product Quantity request in the email: [Quantity]
        - discount via email: [discount request by buyer] %
        - Product Quantity: [Enough or not]
        - discount: [Acceptable or not]
        - Legality: [Based on the contract, determine there is any ambiguity in the email or not] 
        [Repeat the structure for each product mentioned in email]

        Answer the question based on the context below. If the question cannot be answered using the information provided answer with "I don't know".


        Context:
        {content}

        Output: 

        '''

        contract_data = st.text_input("Is there any request? (eg. Please find out if there is any ambiguity.)")
        template = prompt_template.format(content=contract_data)

        bam_input = {
            "model_id": "meta-llama/llama-2-7b-chat",
            "inputs": [template],
            "parameters": {
                "decoding_method": "greedy",
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 3,
                "repetition_penalty": 1,
                "min_new_tokens": 50,
                "max_new_tokens": 1500
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        url = api_url + 'generate'

        responses = requests.post(
            url=url,
            headers=headers,
            json=bam_input
        )

        if responses.status_code == 200:
            response_json = responses.json()
            if 'results' in response_json and len(response_json['results']) > 0:
                generated_text = response_json['results'][0].get('generated_text')
                if generated_text:
                    st.write("This is your answer:", generated_text)
                else:
                    st.write("No generated text found in the response.")
            else:
                st.write("No results found in the response.")
        else:
            st.write(f"Request failed with status code: {responses.status_code}")
            st.write(f"Response content: {responses.content}")