import argparse
import requests
import fitz 
import yaml
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from common import DocumentUtils, MetadataGenerator
from nltk.tokenize import word_tokenize

LOW_VALUE_PHRASES = ["©", "photo by", "image", "figure", "page", "source:"]

# Configure logging to display messages with timestamps and severity levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ExtractAndNormalizePdf")

# Function to load configuration from a YAML file and environment variables
# Raises an error if the .env file is not found
def load_config_and_env(config_path="config/config.yaml"):
    logger.info("Loading configuration from YAML...")
    try:
        # Open and parse the YAML configuration file
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        # Expand user home directory if present in the env_path
        env_path = Path(config.get("env_path")).expanduser()

        # Validate that the .env file exists
        if not env_path or not os.path.isfile(env_path):
            logger.error(f".env file not found at {env_path}")
            raise FileNotFoundError(".env path is invalid or not found in config.yaml")

        logger.info(f"Loading environment variables from: {env_path}")
        
        # Load environment variables from the .env file
        load_dotenv(env_path)

        return config
    except Exception as e:
        logger.exception(f"Error loading config or env: {e}")
        raise

# Function to download a PDF from a URL, read its content, and extract sections based on page content
# Uses the find_best_section_title function to determine section titles

def extract_pdf_sections(url, doc_utils, config):
    logger.info(f"Downloading PDF from URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to download PDF: HTTP {response.status_code}")
        raise ConnectionError("PDF download failed")

    logger.info("Reading and chunking PDF content by page...")
    with open("temp_downloaded.pdf", "wb") as f:
        f.write(response.content)

    try:
        doc = fitz.open("temp_downloaded.pdf")
        metadata_title = doc.metadata.get("title") or "Untitled Document"
        sections = []
        seen_titles = set()
        page_num = 1

        for page in doc:
            try:
                page_dict = page.get_text("dict")
                text = page.get_text("text")

                if not text.strip():
                    logger.info(f"Skipping empty page {page_num}")
                    page_num += 1
                    continue

                cleaned_text = doc_utils.clean_text_block(text)
                word_count = len(word_tokenize(cleaned_text))

                # Filter based on token count and low-value phrase patterns to minimize near empty output pages
                if word_count < 30:
                    lowered = cleaned_text.lower()
                    if all(phrase in lowered for phrase in LOW_VALUE_PHRASES):
                        logger.info(f"Skipping caption-only page {page_num} ({word_count} words)")
                        page_num += 1
                        continue
                    elif word_count < 10:
                        logger.info(f"Skipping nearly empty page {page_num} ({word_count} words)")
                        page_num += 1
                        continue

                section_title = find_best_section_title(page_dict, seen_titles, config)
                section_title = section_title or f"Page {page_num}"
                seen_titles.add(section_title)

                sections.append({
                    "page_number": page_num,
                    "section_title": section_title[:128],
                    "text": cleaned_text
                })

            except Exception as e:
                logger.exception(f"Error processing page {page_num}: {str(e)}")
                raise

            page_num += 1

        doc.close()

        if not sections:
            logger.error("No valid sections extracted from PDF")
            raise ValueError("PDF processing yielded no valid content")

        return metadata_title, sections

    except Exception as e:
        logger.exception(f"Error processing PDF: {str(e)}")
        raise

    finally:
        try:
            os.remove("temp_downloaded.pdf")
        except Exception as e:
            logger.warning(f"Could not remove temporary file: {str(e)}")

# Function to find the best section title from a page's text dictionary
# Considers font size, word count, capitalization, and ignores phrases specified in the config
def find_best_section_title(page_dict, seen_titles, config):
    best_title = None
    largest_font_size = 0
    
    # Get list of phrases to ignore from config (e.g., "table of contents")
    ignore_phrases = [s.lower() for s in config.get("section_title_filter", {}).get("ignore_if_contains", [])]

    # Traverse the hierarchical structure of the PDF page (blocks -> lines -> spans)
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                candidate = span["text"].strip()
                words = candidate.split()

                if not words:
                    continue

                # Calculate ratio of capitalized words for title detection
                capitalized_words = [w for w in words if w[0].isupper()]
                candidate_lc = candidate.lower()

                # Apply multiple heuristics to identify a good section title:
                # 1. Larger font size than previous candidates
                # 2. Reasonable length (not too short or long)
                # 3. Contains at least 3 words
                # 4. At least 40% of words are capitalized
                # 5. Doesn't contain any ignored phrases
                # 6. Not already seen in previous pages
                if (
                    span["size"] > largest_font_size
                    and 12 <= len(candidate) <= 128
                    and len(words) >= 3
                    and len(capitalized_words) / len(words) >= 0.4
                    and not any(bad in candidate_lc for bad in ignore_phrases)
                    and candidate not in seen_titles
                ):
                    largest_font_size = span["size"]
                    best_title = candidate

    return best_title

# Function to build a payload by extracting sections from a PDF and generating metadata
# Saves the metadata and text chunks to the specified output directory
def build_payload(pdf_url, config_path="config/config.yaml"):
    # Load configuration and environment variables
    config = load_config_and_env(config_path)

    llm_document_chunk_size = config.get("llm_document_chunk_size", 2048)
    output_dir = config.get("output_directory", "output")

    # Extract base filename from URL for output files
    doc_utils = DocumentUtils(logger=logger)    
    base_filename = doc_utils.get_base_filename_from_url(pdf_url)

    # Create output directory and clean up any existing files for this document
    doc_utils.prepare_output_directory(base_filename, output_dir)

    # Download PDF and extract its sections
    inferred_title, sections = extract_pdf_sections(pdf_url, doc_utils, config)

    # Combine all text from all sections
    full_text = "\n\n".join([s["text"] for s in sections if s["text"]])

    # Create metadata generator and process the document text
    metadata_gen = MetadataGenerator(config, doc_utils, logger=logger)
    metadata = metadata_gen.generate_metadata(pdf_url, full_text, llm_document_chunk_size)

    # Build the base payload with the generated metadata
    base_payload = doc_utils.build_base_payload(metadata, pdf_url, inferred_title)

    # Save the base payload as JSON and page chunks
    doc_utils.save_base_payload(output_dir, base_filename, base_payload)
    doc_utils.save_text_chunks(output_dir, base_filename, sections, prefix="page")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sustainable agriculture metadata from a PDF URL")
    parser.add_argument("--url", required=True, help="URL to the PDF document")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML")

    args = parser.parse_args()
    try:
        # Process the PDF and generate metadata
        build_payload(args.url, args.config)
    except Exception as e:
        logger.error(f"Failed to generate metadata: {e}")
        exit(1)