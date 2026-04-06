"""
reader.py

Handles loading documents from source directory.
"""

from pathlib import Path
import pandas as pd

from docling.document_converter import DocumentConverter


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR.parent / "data"   # 🔥 go one level up

#print(f"📂 Using data folder: {SOURCE}")
#print(f"📂 Exists: {SOURCE.exists()}")
converter = DocumentConverter()


# =========================
# PDF
# =========================

def load_pdf_safe(file_path: Path, max_pages: int = 1000):
    docs = []

    for i in range(1, max_pages + 1):
        try:
            res = converter.convert(str(file_path), page_range=(i, i))
            docs.append((i, res.document))
            print(f"✅ {file_path.name} → page {i}")

        except Exception as e:
            print(f"⚠️ Stop at page {i}: {e}")
            break

    return docs


# =========================
# GENERIC DOCS
# =========================

def load_document(file_path: Path):
    try:
        res = converter.convert(str(file_path))
        return res.document

    except Exception as e:
        print(f"❌ Failed {file_path}: {e}")
        return None


# =========================
# CSV
# =========================

def read_csv(file_path: Path):
    try:
        df = pd.read_csv(file_path)

        rows = []

        for _, row in df.iterrows():
            row_dict = row.to_dict()

            # Convert row to readable text
            content = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])

            rows.append({
                "headings": ["CSV Row"],
                "content": content,
                "chunk_text": content,
                "source": str(file_path)
            })

        return rows

    except Exception as e:
        print(f"❌ CSV error {file_path}: {e}")
        return []
# MAIN LOADER

def load_all_files():
    """
    Returns structured raw docs:
    [
        {
            type: "pdf" | "doc" | "csv",
            file: Path,
            content: doc OR text OR [(page, doc)]
        }
    ]
    """
    all_docs = []

    for file in SOURCE.rglob("*"):
        if not file.is_file():
            continue

        ext = file.suffix.lower()
        print(f"\n📄 Processing: {file}")

        if ext == ".pdf":
            pages = load_pdf_safe(file)
            all_docs.append({
                "type": "pdf",
                "file": file,
                "content": pages
            })

        elif ext == ".csv":
            text = read_csv(file)
            if text:
                all_docs.append({
                    "type": "csv",
                    "file": file,
                    "content": text
                })

        elif ext in {".docx", ".md", ".txt", ".html"}:
            doc = load_document(file)
            if doc:
                all_docs.append({
                    "type": "doc",
                    "file": file,
                    "content": doc
                })

        else:
            print(f"⏭️ Skipping unsupported: {file}")

    print(f"\n✅ Loaded {len(all_docs)} files")
    return all_docs