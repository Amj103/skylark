Hugging Face's logo
Hugging Face
Models
Datasets
Spaces
Community
Docs
Enterprise
Pricing


Spaces:
Amj103
/
skylark-bi


like
0

Logs
App
Files
Community
Settings
skylark-bi
/
app1.py

Amj103's picture
Amj103
Update app1.py
49f511f
verified
5 minutes ago
raw

Copy download link
history
blame
edit
delete

8.52 kB
import streamlit as st
import pandas as pd
import requests
import json
import re
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
try:
    MONDAY_API = st.secrets["MONDAY_API_TOKEN"]
    WORK_ORDERS_BOARD_ID = st.secrets["WORK_ORDERS_BOARD_ID"]
    DEALS_BOARD_ID = st.secrets["DEALS_BOARD_ID"]
except FileNotFoundError:
    st.error("Secrets file not found. Please create .streamlit/secrets.toml with your Monday.com credentials.")
    st.stop()

st.set_page_config(page_title="Skylark BI Agent", layout="wide")
st.title("📊 Founder BI Agent (Offline Llama-3)")

# ==========================================
# 2. LOCAL LLM INITIALIZATION
# ==========================================
@st.cache_resource(show_spinner="Downloading & Loading Phi-3 Mini...")
def load_local_llm():
    model_path = hf_hub_download(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf"
    )

    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=2
    )
    return llm

llm = load_local_llm()

# ==========================================
# 3. MONDAY.COM INTEGRATION & DATA RESILIENCE
# ==========================================
@st.cache_data(ttl=600, show_spinner="Fetching live data from Monday.com...")
def fetch_and_clean_monday_data(board_id):
    headers = {
        "Authorization": MONDAY_API,
        "Content-Type": "application/json"
    }
    
    # Increased limit to 500 to fetch the entire dataset without missing rows
    query = """
    query ($board: [ID!]) {
      boards(ids: $board) {
        items_page(limit: 500) {
          items {
            name
            column_values {
              column { title }
              text
            }
          }
        }
      }
    }
    """
    
    response = requests.post(
        "https://api.monday.com/v2", 
        json={"query": query, "variables": {"board": [board_id]}}, 
        headers=headers
    )
    
    if response.status_code != 200:
        st.error(f"Monday API Error: {response.text}")
        return pd.DataFrame()

    data = response.json()
    items = data.get('data', {}).get('boards', [])[0].get('items_page', {}).get('items', [])
    
    parsed_data = []
    for item in items:
        row = {"Name": item["name"]}
        for col in item["column_values"]:
            row[col["column"]["title"]] = col["text"]
        parsed_data.append(row)
        
    df = pd.DataFrame(parsed_data)
    
    if df.empty:
        return df
    
    # --- DATA RESILIENCE ---
    numeric_cols = [c for c in df.columns if 'amount' in c.lower() or 'value' in c.lower()]
    for col in numeric_cols:
        # Regex [^\d.-] safely removes everything that is NOT a digit, decimal, or minus sign 
        # (e.g., currency symbols, commas, trailing spaces)
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
        
    df.fillna("Unknown", inplace=True)
    return df

# ==========================================
# 4. AGENT LOGIC: SEMANTIC ROUTING
# ==========================================
def extract_intent(user_query):
    system_prompt = """You are a routing agent. Analyze the user query.
    Return ONLY a raw JSON object with keys:
    'intent' (must be either 'deals_pipeline' or 'work_orders')
    'sector' (Extract the industry/sector mentioned, or 'All')
    Do not add markdown or explanation."""
    
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.1,
        max_tokens=50
    )
    
    raw_text = response['choices'][0]['message']['content']
    try:
        json_match = re.search(r'\{.*\}', raw_text.replace('\n', ''))
        return json.loads(json_match.group(0))
    except:
        return {"intent": "deals_pipeline", "sector": "All"}

def generate_leadership_update(context, user_query):
    # ANTI-HALLUCINATION PROMPT ADDED HERE
    system_prompt = """You are a Business Intelligence AI assistant.
        Respond in a concise conversational style — NOT as an email, memo, or letter.
        Do NOT include greetings, signatures, or subject lines.Use ONLY the provided RAW DATA.
        NEVER invent numbers or placeholders.If data is missing, say it is unavailable."""
    
    prompt = f"USER QUERY: {user_query}\nRAW DATA/CALCULATIONS: {context}\n\nDraft the update."
    
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2, # Lowered temperature to reduce hallucination
        max_tokens=250
    )
    return response['choices'][0]['message']['content']

# ==========================================
# 5. CONVERSATIONAL UI
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about pipeline deals or work orders..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing intent and querying Monday.com (Llama 3 CPU inference)..."):
            
            intent_data = extract_intent(prompt)
            intent_str = intent_data.get('intent', '').lower()
            sector_filter = intent_data.get('sector', 'All')
            
            calculated_context = ""
            
            # --- ROUTE 1: WORK ORDERS ---
            if "work" in intent_str or "order" in prompt.lower():
                df = fetch_and_clean_monday_data(WORK_ORDERS_BOARD_ID)
                if not df.empty:
                    # Look for the Execution Status column
                    status_col = [c for c in df.columns if 'status' in c.lower() and 'execution' in c.lower()]
                    if status_col:
                        status_counts = df[status_col[0]].value_counts().to_dict()
                        calculated_context = f"Work Order Statuses: {status_counts}. Total work orders: {len(df)}."
                    else:
                        calculated_context = f"Total work orders found: {len(df)}. Status column is missing or messy."
                else:
                    calculated_context = "Work orders board is empty or could not be reached."

            # --- ROUTE 2: DEALS PIPELINE ---
            else:
                df = fetch_and_clean_monday_data(DEALS_BOARD_ID)
                if not df.empty:
                    # Look for the Sector column dynamically just in case naming is slightly off
                    sector_col = [c for c in df.columns if 'sector' in c.lower() or 'industry' in c.lower()]
                    
                    if sector_filter != "All" and sector_col:
                        filtered_df = df[df[sector_col[0]].astype(str).str.contains(sector_filter, case=False, na=False)]
                    else:
                        filtered_df = df
                    
                    val_col = [c for c in filtered_df.columns if 'deal value' in c.lower()]
                    
                    if val_col:
                        # Robust string to numeric conversion using Regex
                        clean_numbers = pd.to_numeric(filtered_df[val_col[0]].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
                        total_pipeline = clean_numbers.sum()
                        calculated_context = f"Total pipeline value for {sector_filter}: ₹{total_pipeline:,.2f} based on {len(filtered_df)} deals."
                    else:
                        calculated_context = f"Found {len(filtered_df)} deals for {sector_filter}, but the Deal Value column could not be calculated."
                else:
                    calculated_context = "Deals board is empty or could not be reached."

            final_response = generate_leadership_update(calculated_context, prompt)
            
            st.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
