import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image
import io
import json
import time

# --- Configuration ---
st.set_page_config(page_title="Menu Extraction SaaS", page_icon="🍽️", layout="wide")

# --- Translations ---
TRANSLATIONS = {
    "English": {
        "title": "🍽️ Menu to Excel Converter",
        "subtitle": "Upload menu images and convert them to an editable Excel file.",
        "login_header": "🔒 Premium Menu Converter",
        "login_prompt": "Enter your Access Code",
        "login_error": "😕 Password incorrect",
        "login_contact": "Don't have a code? Contact [Your Telegram/Link] to buy access.",
        "sidebar_header": "Configuration",
        "language": "Language / ភាសា",
        "col_def": "Column Definitions",
        "col_def_caption": "Define the columns you want to extract, separated by commas.",
        "instructions_header": "### Instructions",
        "instructions": [
            "1. Upload menu images (JPG/PNG).",
            "2. Wait for AI processing.",
            "3. Edit data in the table if needed.",
            "4. Download as Excel."
        ],
        "uploader_label": "Upload Menu Images",
        "processing": "Processing image {} of {}...",
        "processing_complete": "Processing complete!",
        "extracted_data": "Extracted Data",
        "download_btn": "📥 Download Excel",
        "no_data": "No data extracted. Please check the images or try again.",
        "error_parse": "Could not parse JSON from image {}. AI Response: {}...",
        "error_process": "Error processing image {}: {}",
        "prompt_instruction": "Extract all menu items from this image into a JSON list. Keys: {}. If Price is in Riel, divide by 4000 to get USD. Return ONLY JSON. Do not include markdown formatting like ```json ... ```."
    },
    "Khmer": {
        "title": "🍽️ កម្មវិធីបម្លែងម៉ឺនុយទៅជា Excel",
        "subtitle": "បញ្ចូលរូបភាពម៉ឺនុយ ហើយបម្លែងវាទៅជាឯកសារ Excel ដែលអាចកែប្រែបាន។",
        "login_header": "🔒 កម្មវិធីបម្លែងម៉ឺនុយ (Premium)",
        "login_prompt": "បញ្ចូលលេខកូដសម្ងាត់",
        "login_error": "😕 លេខកូដមិនត្រឹមត្រូវ",
        "login_contact": "មិនមានលេខកូដ? ទាក់ទង [Telegram/Link របស់អ្នក] ដើម្បីទិញ។",
        "sidebar_header": "ការកំណត់",
        "language": "Language / ភាសា",
        "col_def": "កំណត់ជួរឈរ (Columns)",
        "col_def_caption": "កំណត់ឈ្មោះជួរឈរដែលអ្នកចង់ស្រង់ចេញ ដោយបំបែកដោយសញ្ញាក្បៀស។",
        "instructions_header": "### ការណែនាំ",
        "instructions": [
            "1. បញ្ចូលរូបភាពម៉ឺនុយ (JPG/PNG)។",
            "2. រង់ចាំ AI ដំណើរការ។",
            "3. កែប្រែទិន្នន័យក្នុងតារាងប្រសិនបើចាំបាច់។",
            "4. ទាញយកជាឯកសារ Excel ។"
        ],
        "uploader_label": "បញ្ចូលរូបភាពម៉ឺនុយ",
        "processing": "កំពុងដំណើរការរូបភាពទី {} នៃ {}...",
        "processing_complete": "ដំណើរការបានជោគជ័យ!",
        "extracted_data": "ទិន្នន័យដែលបានស្រង់ចេញ",
        "download_btn": "📥 ទាញយក Excel",
        "no_data": "មិនមានទិន្នន័យត្រូវបានស្រង់ចេញទេ។ សូមពិនិត្យមើលរូបភាព ឬព្យាយាមម្តងទៀត។",
        "error_parse": "មិនអាចអាន JSON ពីរូបភាព {}។ ការឆ្លើយតបរបស់ AI៖ {}...",
        "error_process": "កំហុសក្នុងការដំណើរការរូបភាព {}៖ {}",
        "prompt_instruction": "Extract all menu items from this image into a JSON list. Keys: {}. If Price is in Riel, divide by 4000 to get USD. Return ONLY JSON. Do not include markdown formatting like ```json ... ```. Translate the extracted 'Item' and 'Description' values into Khmer. Keep 'Price' as is."
    }
}

# --- Security Layer ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # if st.session_state["password"] == st.secrets["ACCESS_PASSWORD"]:
        if st.session_state["password"] == "helloworld123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Default to English for Login if not set, or persist? Let's keep simple.
    # We can add a mini toggle on login if needed, but for now let's stick to English default or auto.
    # Actually, let's just show English/Khmer toggle on login too if possible, 
    # but `st.sidebar` might not be visible yet. 
    # For simplicity, Login stays English/Universal or we hardcode both.
    
    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.header("🔒 Premium Menu Converter / កម្មវិធីបម្លែងម៉ឺនុយ")
        st.text_input(
            "Enter your Access Code / បញ្ចូលលេខកូដ", type="password", on_change=password_entered, key="password"
        )
        st.info("Don't have a code? Contact [Your Telegram/Link] to buy access.")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.header("🔒 Premium Menu Converter / កម្មវិធីបម្លែងម៉ឺនុយ")
        st.text_input(
            "Enter your Access Code / បញ្ចូលលេខកូដ", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect / លេខកូដមិនត្រឹមត្រូវ")
        st.info("Don't have a code? Contact [Your Telegram/Link] to buy access.")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # --- Main Application ---
    
    # --- API Setup ---
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-flash-latest')
    except Exception as e:
        st.error(f"Error configuring Gemini API: {e}. Please check your secrets.toml.")
        st.stop()

    # --- Sidebar & Language ---
    with st.sidebar:
        st.header("Configuration")
        
        # Language Toggle
        lang_choice = st.radio("Language / ភាសា", ["Khmer", "English"], horizontal=False)
        t = TRANSLATIONS[lang_choice]

        default_cols = "Category, Item, Price, Description"
        columns_input = st.text_area(t["col_def"], value=default_cols, height=100)
        st.caption(t["col_def_caption"])
        
        st.divider()
        st.markdown(t["instructions_header"])
        for line in t["instructions"]:
            st.markdown(line)

    st.title(t["title"])
    st.markdown(t["subtitle"])

    # --- File Uploader ---
    uploaded_files = st.file_uploader(t["uploader_label"], type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        all_items = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(t["processing"].format(i+1, len(uploaded_files)))
            
            try:
                # Load image
                image = Image.open(uploaded_file)
                
                # Prepare prompt
                prompt = t["prompt_instruction"].format(columns_input)
                
                # Call Gemini
                response = model.generate_content([prompt, image])
                
                # Parse JSON
                try:
                    # Clean up response text if it contains markdown code blocks
                    text_response = response.text.strip()
                    if text_response.startswith("```json"):
                        text_response = text_response[7:]
                    if text_response.endswith("```"):
                        text_response = text_response[:-3]
                    
                    items = json.loads(text_response)
                    
                    # Ensure items is a list
                    if isinstance(items, list):
                        all_items.extend(items)
                    elif isinstance(items, dict):
                         all_items.append(items)
                    
                except json.JSONDecodeError:
                    st.warning(t["error_parse"].format(uploaded_file.name, response.text[:100]))
                except Exception as e:
                    st.error(f"Error processing response for {uploaded_file.name}: {e}")

            except Exception as e:
                st.error(t["error_process"].format(uploaded_file.name, e))
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text(t["processing_complete"])
        
        # --- Output & Export ---
        if all_items:
            st.subheader(t["extracted_data"])
            df = pd.DataFrame(all_items)
            
            # Reorder columns if they match input
            desired_cols = [c.strip() for c in columns_input.split(',')]
            existing_cols = [c for c in desired_cols if c in df.columns]
            extra_cols = [c for c in df.columns if c not in existing_cols]
            final_cols = existing_cols + extra_cols
            
            if final_cols:
                df = df[final_cols]

            # Rename columns to Khmer if selected? 
            # The prompt asks for keys in English (Category, Item...), so the DF has English headers.
            # If we want Khmer headers in Excel, we can map them.
            # For now, let's keep it simple or maybe map standard ones.
            if lang_choice == "Khmer":
                # Optional: Map standard columns to Khmer for display
                khmer_headers = {
                    "Category": "ប្រភេទ",
                    "Item": "ឈ្មោះមុខម្ហូប",
                    "Price": "តម្លៃ",
                    "Description": "ការពិពណ៌នា"
                }
                df.rename(columns=khmer_headers, inplace=True)

            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

            # Excel Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Menu Data')
            
            st.download_button(
                label=t["download_btn"],
                data=output.getvalue(),
                file_name="menu_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning(t["no_data"])
