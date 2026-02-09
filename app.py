import streamlit as st
import fitz  # PyMuPDF
import gc
import os
import tempfile
import math
from PIL import Image
from io import BytesIO

# --- 1. RAM PROVISION ---
def purge():
    """Immediately evicts data from RAM to prevent the 1GB crash."""
    gc.collect()
    st.cache_data.clear()

def surgical_shrink(input_path, target_mb):
    """Processes images on disk so RAM stays empty."""
    doc = fitz.open(input_path)
    orig_mb = os.path.getsize(input_path) / (1024 * 1024)
    
    # Calculate geometric scale to hit 19.5MB
    # If 500MB -> 20MB, we need scale factor ~0.2 (20% dimensions)
    scale = math.sqrt(19.5 / orig_mb) * 0.9
    scale = min(1.0, max(0.05, scale)) 

    # Iterate pages
    for page in doc:
        img_list = page.get_images(full=True)
        for img in img_list:
            xref = img[0]
            try:
                # 1. Extract image WITHOUT loading the page into RAM
                base = doc.extract_image(xref)
                if not base: continue
                
                # 2. Shrink in a tiny memory window
                with Image.open(BytesIO(base["image"])) as pil_img:
                    if pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                    
                    new_size = (int(pil_img.width * scale), int(pil_img.height * scale))
                    # LANCZOS is high quality but uses more RAM, using BILINEAR for safety
                    pil_img = pil_img.resize(new_size, Image.Resampling.BILINEAR)
                    
                    buf = BytesIO()
                    # Low quality (30-40) is required to reach 20MB from 500MB
                    pil_img.save(buf, format="JPEG", quality=35, optimize=True)
                    
                    # 3. Push back to disk immediately
                    doc.update_stream(xref, buf.getvalue())
                    buf.close()
                
                # 4. Immediate Purge
                purge()
            except:
                continue

    # Create the output file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_out:
        # garbage=4 is THE MOST IMPORTANT line. 
        # It deletes the old 500MB data from the file structure.
        doc.save(f_out.name, garbage=4, deflate=True, clean=True)
        out_path = f_out.name
    
    doc.close()
    return out_path

# --- UI ---
st.title("🛡️ 500MB to 20MB Precision Shrinker")
st.markdown("This version uses **Disk-Buffering** to prevent Streamlit crashes.")

up_file = st.file_uploader("Upload PDF", type="pdf")

if up_file:
    if st.button("Surgically Shrink to <20MB"):
        # STEP 1: Move upload to disk immediately
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_in:
            f_in.write(up_file.getbuffer())
            f_in_path = f_in.name
        
        # STEP 2: Wipe the upload from RAM provision
        del up_file
        purge()
        
        with st.spinner("Processing surgically..."):
            try:
                final_path = surgical_shrink(f_in_path, 19.5)
                
                with open(final_path, "rb") as f:
                    final_bytes = f.read()
                
                size = len(final_bytes)/(1024*1024)
                st.success(f"Final Size: {size:.2f} MB")
                st.download_button("📥 Download PDF", final_bytes, "shrunk_20mb.pdf")
                
                # STEP 3: Final Cleanup
                os.remove(f_in_path)
                os.remove(final_path)
                purge()
                
            except Exception as e:
                st.error(f"Error: {e}. The file might be too complex.")
