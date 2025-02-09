from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import langid
import re
from pdfminer.high_level import extract_text
import os
import tempfile

app = FastAPI()

def detect_language(text):
    lang, _ = langid.classify(text)
    return lang if lang in ["fr", "en"] else "en"

def clean_text(text):
    text = re.sub(r"<extra_id_\d+>", "", text)
    text = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.lower().startswith("ce document parle de") or text.lower().startswith("this document discusses"):
        return text
    else:
        prefix = "Ce document parle de " if detect_language(text) == "fr" else "This document discusses "
        return prefix + text

def process_document(file_path, task):
    """
    Processes a document by extracting its text, detecting its language, and performing a specified task 
    (either summarizing or describing the document) using a pre-trained language model.

    Args:
        file_path (str): The path to the document file to be processed.
        task (str): The task to perform on the document. Can be either "summarize" or "describe".

    Returns:
        str: The processed text (summary or description) of the document.

    Raises:
        ValueError: If the task is not "summarize" or "describe".
    """
    model_name = "google/flan-t5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    texte = extract_text(file_path)
    langue = detect_language(texte)

    if task == "summarize":
        if langue == "en":
            prompt = (
                "You are an expert in document analysis. Please provide a concise and clear summary of the following text, "
                "highlighting the key points and essential information. "
                "Ensure that the summary is well-structured and accurately reflects the content of the original text. "
                "Here is the text to summarize:\n\n" + texte
            )
        else:
            prompt = (
                "Vous êtes un expert en analyse de documents. Veuillez reformuler le texte suivant en utilisant vos propres mots, "
                "tout en conservant le sens original. Assurez-vous que la reformulation soit claire, concise et bien structurée. "
                "N'hésitez pas à utiliser des alinéas et des retours à la ligne pour bien séparer les paragraphes. Faites bien attention à la cohérence du texte. "
                "Voici le texte à reformuler :\n\n" + texte
            )
    elif task == "describe":
        if langue == "en":
            prompt = (
                "Analyze and describe the main content and key points of the following text. "
                "Start your response with exactly 'This document discusses' and then continue with "
                "a natural description of what the document contains and explains. "
                "Focus on the main topics and important information. Here's the text:\n\n" + texte
            )
        else:
            prompt = (
                "Vous êtes un expert en analyse de documents. À partir du texte extrait, veuillez fournir une description détaillée et structurée du document lui-même, "
                "sans résumer simplement son contenu. Commencez impérativement votre description par la phrase exacte : 'Ce document parle de ...'. "
                "Ensuite, décrivez le contexte (objectif, public visé, format de publication), la structure, le ton et le style du document, "
                "ainsi que toutes les caractéristiques remarquables qui le définissent. Votre description doit être claire, concise, bien organisée et professionnelle. "
                "Voici le texte extrait :\n\n" + texte
            )

    inputs = tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True)
    output = model.generate(
        **inputs,
        max_length=700,
        min_length=300,
        num_beams=5,
        do_sample=True,
        temperature=0.7,
        no_repeat_ngram_size=3,
        early_stopping=True,
    )

    description = tokenizer.decode(output[0], skip_special_tokens=True)
    return clean_text(description)

@app.post("/summarize/")
async def summarize_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are accepted.")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        summary = process_document(tmp_path, task="summarize")
        os.remove(tmp_path)
        return JSONResponse(content={"Summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/describe/")
async def describe_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are accepted.")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        description = process_document(tmp_path, task="describe")
        os.remove(tmp_path)
        return JSONResponse(content={"Description": description})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
