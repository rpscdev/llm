from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fpdf import FPDF
from google import genai
import os
import uuid

from dotenv import load_dotenv 

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Set up Gemini
genai_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=genai_api_key)

# Home page with form
@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Handle form submission and generate PDF
@app.post("/generate_plan", response_class=HTMLResponse)
async def generate_plan(
    request: Request,
    goal: str = Form(...),
    days: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...)
):
    prompt = (
        f"Give a concise gym workout and diet plan in tabular form for:\n"
        f"- Goal: {goal}\n"
        f"- {days} per week\n"
        f"- Age: {age}, Weight: {weight}kg\n"
        f"Include daily workout routine + protein intake. Use short headings and bullet points."
    )

    response = client.models.generate_content(
    model="gemini-2.0-flash", contents= prompt
    )
    workout_text = response.text

    # Create a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in workout_text.split("\n"):
        pdf.multi_cell(0, 10, line)

    # Save with unique filename
    filename = f"workout_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = f"pdfs/{filename}"
    os.makedirs("pdfs", exist_ok=True)
    pdf.output(pdf_path)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "workout_plan": workout_text,
        "pdf_url": f"/download/{filename}"
    })

# Route to download the PDF
@app.get("/download/{filename}")
async def download_pdf(filename: str):
    file_path = f"pdfs/{filename}"
    return FileResponse(path=file_path, filename="workout_plan.pdf", media_type='application/pdf')
