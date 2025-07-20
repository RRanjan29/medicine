from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load basic medicine list (optional improvement)
KNOWN_MEDICINES = ["paracetamol", "ibuprofen", "amoxicillin", "cetirizine", "azithromycin"]

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    text = pytesseract.image_to_string(image)

    # Extract probable medicine names (naive match with known list)
    found_medicines = []
    for med in KNOWN_MEDICINES:
        if med.lower() in text.lower():
            found_medicines.append(med)

    # Search purchase links for each
    search_results = {}
    for med in found_medicines:
        search_results[med] = search_medicine_links(med)

    return JSONResponse({"medicines": found_medicines, "links": search_results})

def search_medicine_links(med_name):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = f"buy {med_name} medicine online"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = []
    for g in soup.find_all('a'):
        href = g.get('href')
        if href and href.startswith("/url?q="):
            link = href.split("/url?q=")[1].split("&")[0]
            if any(domain in link for domain in ["pharmeasy", "netmeds", "1mg", "amazon"]):
                links.append(link)
    return links[:3]  # top 3 links
