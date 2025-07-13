# Document-QA

A Retrieval-Augmented Generation (RAG) Question Answering System for Documents  
Supports PDF, Word (.docx), PowerPoint (.pptx), and image files (PNG, JPG, JPEG) with OCR and reference link crawling.

---

## Features

- **Multi-format Support:** Upload PDF, DOCX, PPTX, PNG, JPG, or JPEG files.
- **Image OCR:** Extracts text from standalone images and images embedded in documents using Tesseract OCR.
- **Reference Link Crawling:** Detects and fetches content from URLs and hyperlinks found in documents, making referenced web content searchable.
- **Semantic Search:** Uses Cohere embeddings and Chroma vector database for semantic retrieval, not just keyword matching.
- **RAG Chatbot:** Ask questions about your uploaded documents and get context-aware answers.
- **Web Interface:** Simple Flask-based web UI for uploading files and chatting.

---

## How It Works

1. **Upload** a document or image via the web interface.
2. **Text Extraction:** The system extracts text from the file, including OCR for images and embedded images.
3. **Reference Crawling:** Any URLs or hyperlinks in the document are fetched and their content is added to the searchable corpus.
4. **Chunking & Embedding:** The combined text is split into chunks and embedded using Cohere.
5. **Semantic Retrieval:** When you ask a question, the system retrieves the most relevant chunks using vector similarity.
6. **Answer Generation:** The chatbot uses an LLM to generate an answer based on the retrieved context.

---

### Prerequisites

- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and added to your PATH
- Cohere API key (set as `COHERE_API_KEY` in your environment)