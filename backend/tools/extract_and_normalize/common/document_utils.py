import json
import os
import uuid
from urllib.parse import urlparse
from os.path import basename, splitext, join
import logging
import re
import unicodedata

class DocumentUtils:
    """Utility class for document processing operations."""
    
    def __init__(self, logger=None):
        """Initialize with optional custom logger."""
        self.logger = logger or logging.getLogger("ExtractAndNormalizePdf")
    
    def get_base_filename_from_url(self, url):
        """Extract filename without extension from URL path."""
        try:
            return splitext(basename(urlparse(url).path))[0]
        except Exception as e:
            self.logger.exception("Failed to extract base filename from URL")
            raise

    def prepare_output_directory(self, base_filename, output_dir):
        """Create output directory and clean previous files for same document."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            # Remove existing files for this document
            for filename in os.listdir(output_dir):
                if filename.startswith(base_filename + "_"):
                    os.remove(join(output_dir, filename))
        except Exception as e:
            self.logger.exception("Failed to prepare output directory")
            raise

    def build_base_payload(self, metadata, pdf_url, inferred_title):
        """Construct standardized metadata payload from extracted data."""
        try:
            return {
                "title": metadata.get("title") or inferred_title,
                "source_url": pdf_url,
                "date_published": metadata.get("date_published"),
                "language": metadata.get("language"),
                "region_or_country": metadata.get("region_or_country"),
                "document_type": metadata.get("document_type"),
                "sustainability_dimensions": metadata.get("sustainability_dimensions"),
                "key_topics": metadata.get("key_topics"),
                "contains_harmful_practices": metadata.get("contains_harmful_practices"),
                "intended_audience": [a.lower() for a in metadata.get("intended_audience", [])],
                "source_name": self.infer_source_name_from_url(pdf_url),
                "doc_id": str(uuid.uuid5(uuid.NAMESPACE_URL, pdf_url))
            }
        except Exception as e:
            self.logger.exception("Failed to build base payload")
            raise

    def infer_source_name_from_url(self, url):
        """Determine document source organization from URL domain."""
        result = "Unknown"
        try:
            netloc = urlparse(url).netloc.lower()
            # Known organization mappings
            if "fao" in netloc:
                result = "FAO"
            elif "worldbank" in netloc:
                result = "World Bank"
            elif "cimmyt" in netloc:
                result = "CIMMYT"
            elif "undp" in netloc:
                result = "UNDP"
            result = netloc.replace("www.", "")
        except Exception as e:
            self.logger.warning("Failed to infer source name from URL")
        
        return result

    def save_base_payload(self, output_dir, base_filename, base_payload):
        """Save metadata payload as formatted JSON file."""
        try:
            with open(join(output_dir, f"{base_filename}_base_payload.json"), "w", encoding="utf-8") as f:
                json.dump(base_payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception("Failed to save base payload JSON")
            raise

    def save_text_chunks(self, output_dir, base_filename, sections, prefix="page"):
        """Save each document section as separate text file."""
        try:
            for i, section in enumerate(sections):
                if not section["text"]:
                    continue
                
                # Use the page_number from section, or fallback to (i+1) for 1-based indexing
                identifier = section.get("page_number", i + 1)
                section_title = section.get("section_title", f"Page {identifier}")
                
                # Include section title as header in the content
                formatted_content = f"--- {section_title} ---\n\n{section['text']}"
                
                # Save with page number in filename for consistent referencing
                with open(join(output_dir, f"{base_filename}_{prefix}{identifier}.txt"), "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                                    
                    
        except Exception as e:
            self.logger.exception("Failed to save one or more text chunks")
            raise

    # Strip control characters but keep punctuation and line breaks
    def _strip_control_chars(self, s):
            return ''.join(
                c for c in s
                if unicodedata.category(c)[0] != "C" or c == "\n"
            )
    
    def clean_text_block(self, text, max_newlines=2):
        """
        Normalize and clean extracted PDF text for semantic processing,
        while preserving paragraph-level structure via double line breaks.
        
        Args:
            text (str): Raw text extracted from PDF
            max_newlines (int): Maximum number of consecutive newlines to preserve
                                (default: 2 for paragraph separation)
        
        Returns:
            str: Cleaned text with normalized whitespace and preserved paragraph structure
        """
        result = ""

        if text:
            # Remove form feeds and null bytes
            text = re.sub(r"[\f\x00]", "", text)
            
            # Strip control characters
            text = self._strip_control_chars(text)
            
            # Convert all whitespace-only lines to newlines
            text = re.sub(r"^\s+$", "\n", text, flags=re.MULTILINE)
            
            # Normalize spaces (collapse multiple spaces into one)
            text = re.sub(r" +", " ", text)
            
            # Remove spaces at the beginning or end of lines
            text = re.sub(r"^ +| +$", "", text, flags=re.MULTILINE)
            
            # Convert runs of 3+ newlines into exactly max_newlines (default: 2 for paragraphs)
            text = re.sub(r"\n{%d,}" % (max_newlines + 1), "\n" * max_newlines, text)
            
            # Split into paragraphs (defined by double newlines)
            paragraphs = text.split("\n\n")
            
            # Clean each paragraph: join lines that were artificially split by PDF extraction
            # but preserve intentional line breaks for lists, addresses, etc.
            cleaned_paragraphs = []
            for paragraph in paragraphs:
                # Join lines that are likely continuing the same paragraph
                # (no period/colon/etc. at end of line and next line doesn't start with capital)
                lines = paragraph.split("\n")
                i = 0
                while i < len(lines) - 1:
                    current_line = lines[i].strip()
                    next_line = lines[i + 1].strip()
                    
                    # Skip empty lines
                    if not current_line:
                        i += 1
                        continue
                        
                    # If current line doesn't end with sentence-ending punctuation
                    # and next line doesn't start with a capital letter or bullet point,
                    # join them as they're likely part of the same paragraph
                    if (not re.search(r'[.!?:;]$', current_line) and 
                        not (next_line and (next_line[0].isupper() or next_line[0] in '-•*'))):
                        lines[i] = current_line + " " + next_line
                        lines.pop(i + 1)
                    else:
                        i += 1
                
                # Reassemble the paragraph with single newlines between actual line breaks
                cleaned_paragraph = "\n".join(line for line in lines if line.strip())
                if cleaned_paragraph:
                    cleaned_paragraphs.append(cleaned_paragraph)
            
            # Rejoin paragraphs with double newlines
            result= "\n\n".join(cleaned_paragraphs)

        return result







