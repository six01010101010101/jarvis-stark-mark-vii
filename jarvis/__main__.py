"""Permite executar com: python -m jarvis"""

from jarvis.services.zip_extractor import extract_uploaded_zips
from jarvis.app import main

if __name__ == "__main__":
    try:
        extract_uploaded_zips()
    except Exception:
        pass
    main()
