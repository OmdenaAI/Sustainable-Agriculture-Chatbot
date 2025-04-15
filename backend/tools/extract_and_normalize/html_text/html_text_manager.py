from common.document_utils import DocumentUtils
from .generic_scraper import GenericScraper
from common.metadata_generator import MetadataGenerator
from urllib.parse import urlparse
import re
import hashlib

class HtmlTextManager:
    def __init__(self, url, config, logger):
        self.url = url
        self.config = config
        self.logger = logger
        self.doc_utils = DocumentUtils(self.logger)
        parsed_url = urlparse(self.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.scraper = GenericScraper(base_url, self.config, self.logger)

    def build_payload(self):
        # Load configuration and environment variables
        llm_document_chunk_size = self.config.get("llm_document_chunk_size", 2048)
        output_dir = self.config.get("output_directory", "output")

        # Extract base filename from URL for output files 
        base_filename = self.doc_utils.get_base_filename_from_url(self.url)

        # Create output directory and clean up any existing files for this document
        self.doc_utils.prepare_output_directory(base_filename, output_dir)

        # Combine all text from all sections
        scraper_full_text = self.scraper.scrape_topic_page(self.url)
        inferred_title = scraper_full_text.get("title")
        full_text = scraper_full_text.get("content")
        cleaned_text = self.doc_utils.clean_text_block(full_text)

        sections = []

        # For html put all text into one section
        sections.append({
                        "page_number": 1,
                        "section_title": inferred_title,
                        "text": cleaned_text
                    })

        # Create metadata generator and process the document text
        metadata_gen = MetadataGenerator(self.config, self.doc_utils, logger=self.logger)
        metadata = metadata_gen.generate_metadata(self.url, full_text, llm_document_chunk_size)

        # Build the base payload with the generated metadata
        base_payload = self.doc_utils.build_base_payload(metadata, self.url, inferred_title)

        # Save the base payload as JSON and page chunks
        self.doc_utils.save_base_payload(output_dir, base_filename, base_payload)
        self.doc_utils.save_text_chunks(output_dir, base_filename, sections, prefix="page")
