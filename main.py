from dotenv import load_dotenv
import os
load_dotenv()

import os
from fastapi import FastAPI, UploadFile, File, Form
from litellm import completion, completion_cost
import traceback
from pypdf import PdfReader
import io
from docx import Document
from openpyxl import load_workbook
import sqlite3

app = FastAPI()

conn = sqlite3.connect("budgets.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS team_usage (
    team TEXT PRIMARY KEY,
    spent REAL
)
""")

conn.commit()

def get_spent(team: str) -> float:
    cursor.execute("SELECT spent FROM team_usage WHERE team=?", (team,))
    row = cursor.fetchone()
    return row[0] if row else 0.0


def update_spent(team: str, new_spent: float):
    cursor.execute("""
        INSERT INTO team_usage (team, spent)
        VALUES (?, ?)
        ON CONFLICT(team) DO UPDATE SET spent=excluded.spent
    """, (team, new_spent))
    conn.commit()


team_budgets = {
    "team 1": 20.0,
    "team 2": 20.0,
    "team 3": 20.0,
    "team 4": 20.0
}

async def extract_text(file: UploadFile):

    if file is None:
        return ""

    contents = await file.read()

    filename = file.filename.lower()

    # txt
    if filename.endswith(".txt"):
        return contents.decode("utf-8")

    # pdf
    elif filename.endswith(".pdf"):

        pdf = PdfReader(io.BytesIO(contents))

        text = ""

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    # word
    elif filename.endswith(".docx"):

        doc = Document(io.BytesIO(contents))

        text = ""

        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return text

    # excel
    elif filename.endswith(".xlsx"):

        workbook = load_workbook(io.BytesIO(contents))

        text = ""

        for sheet in workbook.worksheets:

            text += f"Worksheet: {sheet.title}\n"

            for row in sheet.iter_rows(values_only=True):

                row_text = " | ".join(
                    str(cell) if cell is not None else ""
                    for cell in row
                )

                text += row_text + "\n"

        return text

    else:
        raise ValueError("Unsupported file type.")
    
    await file.close()


@app.post("/chat")
async def chat(
    team: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(None)
):

    if team not in team_budgets:
        return {"error": "Unknown team"}

    spent = get_spent(team)
    remaining = team_budgets[team] - spent

    if remaining <= 0:
        return {
            "status": "blocked",
            "error": "budget reached",
            "remaining_budget": 0
        }

    try:
        file_text = await extract_text(file)
    except Exception as e:
        return {
            "error": str(e)
        }
    
    full_prompt = f"""
    Student Prompt:
    {message}

    Uploaded File:
    {file_text}
    """

    try:
        response = completion(
            model=f"{provider}/{model}",
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        cost = completion_cost(completion_response=response)

        new_spent = spent + cost
        update_spent(team, new_spent)

        return {
            "status": "allowed",
            "response": response.choices[0].message.content,
            "team": team,
            "provider": provider,
            "model": model,
            "cost": cost,
            "spent": get_spent(team),
            "remaining": team_budgets[team] - spent
        }

    except Exception as e:
        return {"error": str(e)}