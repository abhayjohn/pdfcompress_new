import streamlit as st
import fitz  # PyMuPDF
import gc
import os
import tempfile
import math

def purge():
    gc.collect()

def robust_shrink(input_path):
    doc = fitz.open(input_path)
    out_doc = fitz.open()
    orig_mb = os.path.getsize(input_path) / (1024 * 1024)
    
    # Calculate DPI to hit ~19MB
    # For a 500MB file, we need a very low DPI (roughly 60-72)
    # This formula balances quality and target size
    target_dpi = max(40, min(150, int(72 * math.sqrt(20 / orig_mb))))
    
    progress = st.progress(0, text="Re-imaging pages (Fixing blank output)...")
    total = len(doc)

    for i, page in enumerate(doc):
        # 1. Render page to a pixmap (Image) at target DPI
        # matrix = zoom factor. 72 DPI is matrix(1,1)
        zoom = target_dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        
        # 2. Compress that image heavily as a JPEG buffer
        img_data = pix.tobytes("jpg", jpg_quality=40)
        
        # 3. Create a new page in the output document
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        
        # 4. Insert the compressed image covering the whole page
        new_page.insert_image(page.rect, stream=img_data)
        
        # Cleanup page-specific RAM
        pix = None
        img_data = None
        progress.progress((i + 1) / total)
        
        if i % 5 == 0:
            purge()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_out:
        # Save with full compression
        out_doc.save(f_out.name, garbage=4, deflate=True)
        out_path = f_out.name
    
    doc.close()
    out_doc.close()
    return out_path

# --- UI CODE ---
st.title("🛡️ Anti-Blank PDF Compressor")
st.markdown("This version renders pages as images to ensure content is **visible** and **small**.")

up_file = st.file_uploader("Upload PDF", type="pdf")

if up_file:
    if st.button("Compress and Fix Output"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_in:
            f_in.write(up_file.getbuffer())
            f_in_path = f_in.name
        
        del up_file
        purge()
        
        try:
            final_path = robust_shrink(f_in_path)
            with open(final_path, "rb") as f:
                final_bytes = f.read()
            
            st.success(f"Final Size: {len(final_bytes)/(1024*1024):.2f} MB")
            st.download_button("📥 Download Fixed PDF", final_bytes, "fixed_compressed.pdf")
            
            os.remove(f_in_path)
            os.remove(final_path)
            purge()
        except Exception as e:
            st.error(f"Error: {e}")
