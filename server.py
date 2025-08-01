# General
from dotenv import load_dotenv
import os
from pypdf import PdfReader
# AI Agents
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
# Web-Server
from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge


UPLOAD_FOLDER = "./static/files"
MAX_FILE_SIZE = 16 # In MB
ALLOWED_EXTENSIONS = [ "txt", "pdf" ]


def summarizeFile(filePath):
    reader = PdfReader(filePath)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    # AI Agent
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    promptTemplate = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a PDF summarizing agent meant to summarize uploaded PDFs to the user as concisely as possible. Keep summaries no more than 3 sentences long
            """
        ),
        ("user", "{textContent}")
    ])
    prompt = promptTemplate.invoke({ "textContent": text})
    prompt.to_messages()
    return llm.invoke(prompt).content


def allowedExtension(fileName: str) -> bool:
    return "." in fileName and fileName.split(".")[1] in ALLOWED_EXTENSIONS


load_dotenv()

summary = ""

app = Flask(__name__)
app.secret_key = "Super Secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = ALLOWED_EXTENSIONS
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE * 1024 * 1024

@app.route("/")
def home():
    return render_template("index.html", summary=summary)


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        if file.filename == "":
            flash("No file provided")
            return redirect("/")
        if not allowedExtension(file.filename):
            flash(f"File extension not supported (supported: {", ".join(ALLOWED_EXTENSIONS)})")
        elif file:
            filePath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
            file.save(filePath)
            global summary
            summary = summarizeFile(filePath)
            os.remove(filePath)
            return redirect("/")
    except RequestEntityTooLarge:
        flash(f"File size limit of {MAX_FILE_SIZE} MB exceeded")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)