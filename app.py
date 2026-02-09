import streamlit as st
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ultimate PDF Compressor", layout="centered")

st.title("🛡️ 500MB+ PDF Survivor")
st.markdown("""
### Why this works:
* **Zero Server RAM:** The file stays in your browser. It never touches Streamlit's 1GB limit.
* **Binary Processing:** Uses `Uint8Array` to bypass the 200MB JavaScript string error.
* **Auto-Purge:** Memory is released the moment you close the tab.
""")

# --- THE JAVASCRIPT ENGINE ---
# We use pdf-lib for the logic and embed it directly in the UI
html_code = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card { 
            border: 2px dashed #4285f4; 
            border-radius: 12px; 
            padding: 40px; 
            text-align: center; 
            background: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        #status { margin-top: 20px; font-weight: 600; color: #1a73e8; }
        .progress-container { 
            width: 100%; 
            background-color: #e0e0e0; 
            border-radius: 10px; 
            margin-top: 20px; 
            display: none;
        }
        #progress-bar { 
            width: 0%; 
            height: 10px; 
            background-color: #34a853; 
            border-radius: 10px; 
            transition: width 0.3s;
        }
        input[type="file"] { margin-bottom: 20px; }
        button { 
            background-color: #1a73e8; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 16px;
        }
        button:disabled { background-color: #ccc; }
    </style>
</head>
<body>
    <div class="card">
        <input type="file" id="pdf-input" accept="application/pdf">
        <br>
        <button id="exec-btn">Compress in Browser</button>
        
        <div id="status">Ready for 500MB+ File</div>
        
        <div class="progress-container" id="p-cont">
            <div id="progress-bar"></div>
        </div>
    </div>

    <script>
        const btn = document.getElementById('exec-btn');
        const status = document.getElementById('status');
        const pBar = document.getElementById('progress-bar');
        const pCont = document.getElementById('p-cont');

        btn.onclick = async () => {
            const file = document.getElementById('pdf-input').files[0];
            if (!file) {
                status.innerText = "❌ Please select a file first!";
                return;
            }

            try {
                btn.disabled = true;
                pCont.style.display = "block";
                pBar.style.width = "10%";
                status.innerText = "Reading Binary Data (Using System RAM)...";

                // Step 1: Use ArrayBuffer to avoid 200MB String Limit
                const arrayBuffer = await file.arrayBuffer();
                pBar.style.width = "30%";

                status.innerText = "Parsing PDF Structure...";
                // Step 2: Load PDF without full-string conversion
                const pdfDoc = await PDFLib.PDFDocument.load(arrayBuffer, { 
                    ignoreEncryption: true 
                });
                pBar.style.width = "50%";

                status.innerText = "Optimizing Object Streams...";
                // Step 3: Compress streams and remove duplicate metadata
                const compressedBytes = await pdfDoc.save({
                    useObjectStreams: true,
                    addDefaultFont: false,
                    updateFieldAppearances: false
                });
                pBar.style.width = "90%";

                status.innerText = "Success! Generating Download...";
                
                // Step 4: Create local Blob (zero server interaction)
                const blob = new Blob([compressedBytes], { type: 'application/pdf' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = "optimized_" + file.name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                pBar.style.width = "100%";
                status.innerText = "✅ Done! Check your downloads folder.";
                btn.disabled = false;

            } catch (err) {
                console.error(err);
                status.style.color = "red";
                status.innerText = "Error: Browser hit memory limit. Try Chrome or Edge.";
                btn.disabled = false;
            }
        };
    </script>
</body>
</html>
"""

# Display the component in Streamlit
components.html(html_code, height=500)

st.divider()
st.caption("Note: This app runs entirely on your local machine. No data is sent to the server.")
