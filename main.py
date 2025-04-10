from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import shutil
import os
import fitz  # PyMuPDF

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/merge")
async def merge_pdfs(files: list[UploadFile]):
    merger = PdfMerger()
    for file in files:
        with open(file.filename, "wb") as f:
            f.write(await file.read())
        merger.append(file.filename)
    output = "merged.pdf"
    merger.write(output)
    merger.close()
    return {"filename": output}

@app.post("/compress")
async def compress_pdf(file: UploadFile = File(...)):
    with open("compressed.pdf", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": "compressed.pdf"}

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    input_path = file.filename
    with open(input_path, "wb") as f:
        f.write(await file.read())
    output_path = input_path.replace(".pdf", ".docx")
    cv = Converter(input_path)
    cv.convert(output_path, start=0, end=None)
    cv.close()
    return {"filename": output_path}

@app.post("/split")
async def split_pdf(file: UploadFile = File(...)):
    with open("input.pdf", "wb") as f:
        f.write(await file.read())
    reader = PdfReader("input.pdf")
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        with open(f"page_{i+1}.pdf", "wb") as out:
            writer.write(out)
    return {"message": "PDF split successfully"}

@app.post("/rotate")
async def rotate_pdf(file: UploadFile = File(...), degrees: int = 90):
    with open("input.pdf", "wb") as f:
        f.write(await file.read())
    reader = PdfReader("input.pdf")
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)
    with open("rotated.pdf", "wb") as f:
        writer.write(f)
    return {"filename": "rotated.pdf"}

@app.post("/pdf-to-images")
async def pdf_to_images(file: UploadFile = File(...)):
    input_path = file.filename
    with open(input_path, "wb") as f:
        f.write(await file.read())
    doc = fitz.open(input_path)
    image_names = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap()
        output_image = f"page_{i+1}.png"
        pix.save(output_image)
        image_names.append(output_image)
    return {"images": image_names}

@app.post("/add-watermark")
async def add_watermark(file: UploadFile = File(...), watermark_text: str = Form(...)):
    with open("input.pdf", "wb") as f:
        f.write(await file.read())
    doc = fitz.open("input.pdf")
    for page in doc:
        page.insert_text((50, 50), watermark_text, fontsize=20, rotate=45, color=(0.5, 0.5, 0.5))
    doc.save("watermarked.pdf")
    return {"filename": "watermarked.pdf"}

@app.post("/add-password")
async def add_password(file: UploadFile = File(...), password: str = Form(...)):
    with open("input.pdf", "wb") as f:
        f.write(await file.read())
    reader = PdfReader("input.pdf")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open("protected.pdf", "wb") as f:
        writer.write(f)
    return {"filename": "protected.pdf"}

@app.post("/remove-password")
async def remove_password(file: UploadFile = File(...), password: str = Form(...)):
    with open("encrypted.pdf", "wb") as f:
        f.write(await file.read())
    reader = PdfReader("encrypted.pdf")
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open("unlocked.pdf", "wb") as f:
        writer.write(f)
    return {"filename": "unlocked.pdf"}
