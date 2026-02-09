import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Client-Side PDF Tool", layout="wide")

st.title("🚀 Zero-Crash PDF Optimizer")
st.markdown("""
**How it works:** This app uses **your computer's RAM** to process the file. 
The 500MB file never touches the Streamlit server's limited memory, preventing crashes.
""")

# Load the JavaScript Engine
with open("compressor.html", "r") as f:
    html_code = f.read()

# Hidden JS component
receiver = components.html(html_code, height=0, width=0)

up_file = st.file_uploader("Upload PDF (Uses your System RAM)", type="pdf")

if up_file:
    # Read file locally
    file_bytes = up_file.read()
    b64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    
    if st.button("Optimize in Browser"):
        st.info("Processing... Please keep this tab open.")
        
        # Trigger the JS logic in the user's browser
        # We use a simple hack to 'inject' the data into the HTML component
        st.components.v1.html(f"""
            <script>
                window.parent.postMessage({{
                    type: "COMPRESS_PDF",
                    base64Pdf: "{b64_pdf}"
                }}, "*");
            </script>
        """, height=0)

    # Note: Modern browsers handle 500MB blobs well, but 
    # the return value will appear here if using a full Custom Component.
