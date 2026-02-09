import streamlit as st
import fitz  # PyMuPDF
import gc
import os
import tempfile

def purge():
    gc.collect()

def process_pdf(input_path, dpi_value, quality_value, use_grayscale, is_preview=False):
    doc = fitz.open(input_path)
    out_doc = fitz.open()
    
    zoom = dpi_value / 72
    mat = fitz.Matrix(zoom, zoom)
    c_space = fitz.csGRAY if use_grayscale else fitz.csRGB
    
    # If preview, only process 1 page to save time
    pages_to_process = [doc[len(doc)//2]] if is_preview else doc
    
    for page in pages_to_process:
        pix = page.get_pixmap(matrix=mat, colorspace=c_space, annots=True)
        img_data = pix.tobytes("jpg", jpg_quality=quality_value)
        
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=img_data)
        
    if is_preview:
        size = out_doc.save_to_bytes(garbage=3, deflate=True)
        doc.close()
        out_doc.close()
        return len(size) * len(doc) # Estimated total size
    
    # Final full save logic
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_out:
        out_doc.save(f_out.name, garbage=4, deflate=True)
        out_path = f_out.name
    
    doc.close()
    out_doc.close()
    return out_path

# --- UI ---
st.set_page_config(page_title="PDF Precision Estimator", layout="wide")
st.title("🎯 PDF Optimizer with Live Estimation")

# Sidebar for controls
st.sidebar.header("🔧 Adjustment Panel")
dpi_input = st.sidebar.slider("DPI (Sharpness)", 50, 200, 120, 10)
quality_input = st.sidebar.slider("JPEG Quality", 10, 95, 75, 5)
grayscale_input = st.sidebar.checkbox("Grayscale Mode", value=False)

up_file = st.file_uploader("Upload your large PDF (up to 1GB)", type="pdf")

if up_file:
    # Save to temp disk for previewing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_temp:
        f_temp.write(up_file.getbuffer())
        temp_path = f_temp.name

    # --- LIVE ESTIMATION LOGIC ---
    with st.sidebar:
        st.divider()
        st.subheader("📊 Estimated Final Size")
        try:
            # We run a quick 1-page test
            est_bytes = process_pdf(temp_path, dpi_input, quality_input, grayscale_input, is_preview=True)
            est_mb = est_bytes / (1024 * 1024)
            
            if est_mb > 20:
                st.error(f"~{est_mb:.1f} MB (Too Large)")
                st.caption("Try reducing DPI or turning on Grayscale.")
            else:
                st.success(f"~{est_mb:.1f} MB (Perfect!)")
        except Exception as e:
            st.error("Wait for upload...")

    # --- MAIN ACTION ---
    if st.button("🚀 Start Full Compression"):
        del up_file
        purge()
        with st.spinner("Processing every page surgically..."):
            final_path = process_pdf(temp_path, dpi_input, quality_input, grayscale_input, is_preview=False)
            
            with open(final_path, "rb") as f:
                final_bytes = f.read()
            
            real_mb = len(final_bytes)/(1024*1024)
            st.balloons()
            st.success(f"Compression Complete! Final size: {real_mb:.2f} MB")
            st.download_button("📥 Download PDF", final_bytes, "optimized_final.pdf")
            
            os.remove(final_path)
    
    # Cleanup temp input after the session
    if os.path.exists(temp_path):
        os.remove(temp_path)
