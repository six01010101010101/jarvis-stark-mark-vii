"""Extrator e analisador de repositórios GitHub descarregados em arquivos .zip."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

USER_UPLOADED_DIR = Path(r"C:\Users\s6x12\.gemini\antigravity\brain\2aabbf87-5e55-4ccd-8932-d1fdcf7361d9\.user_uploaded")
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "github_repos"


def extract_uploaded_zips() -> list[Path]:
    """Localiza todos os zips enviados pelo usuário, extrai e gera inventário completo."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    extracted_paths: list[Path] = []
    inventory_lines: list[str] = ["# Inventário dos Repositórios GitHub Extraídos\n"]

    if not USER_UPLOADED_DIR.exists():
        logger.info("Diretório de uploads não encontrado: %s", USER_UPLOADED_DIR)
        return extracted_paths

    zip_files = sorted(USER_UPLOADED_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime)
    if not zip_files:
        logger.info("Nenhum arquivo zip encontrado em: %s", USER_UPLOADED_DIR)
        return extracted_paths

    for idx, zip_path in enumerate(zip_files, start=1):
        target_subfolder = OUTPUT_DIR / f"repo_{idx}_{zip_path.stem}"
        target_subfolder.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                file_list = zf.namelist()
                already_extracted = any(target_subfolder.iterdir())
                if not already_extracted:
                    print(f"📦 Extraindo Repositório {idx} ({zip_path.name})...")
                    zf.extractall(target_subfolder)
                    print(f"✅ Repositório {idx} extraído com sucesso ({len(file_list)} arquivos).")
                else:
                    print(f"⚡ Repositório {idx} já extraído ({target_subfolder.name}).")

                extracted_paths.append(target_subfolder)
                inventory_lines.append(f"## Repositório {idx}: {zip_path.name}")
                inventory_lines.append(f"- **Destino:** `{target_subfolder}`")
                inventory_lines.append(f"- **Total de arquivos:** {len(file_list)}")
                inventory_lines.append("### Arquivos principais:")
                for item in file_list[:35]:
                    inventory_lines.append(f"  - `{item}`")
                if len(file_list) > 35:
                    inventory_lines.append(f"  - *(e mais {len(file_list) - 35} arquivos...)*")
                inventory_lines.append("\n---\n")
                logger.info("Zip indexado com sucesso: %s -> %s", zip_path.name, target_subfolder)
        except Exception as exc:  # noqa: BLE001
            logger.error("Falha ao extrair %s: %s", zip_path, exc)
            inventory_lines.append(f"## Erro no Repositório {idx}: {zip_path.name} ({exc})\n")

    inventory_file = OUTPUT_DIR / "INVENTORY.md"
    inventory_file.write_text("\n".join(inventory_lines), encoding="utf-8")
    logger.info("Inventário salvo em: %s", inventory_file)
    return extracted_paths
