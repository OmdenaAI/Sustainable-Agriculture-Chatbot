# Document Processing and Metadata Extraction for Sustainable Agriculture

A robust Python application that extracts text and metadata from both PDF documents and HTML webpages, generating standardized payloads for Qdrant vector database indexing. Focused on sustainable agriculture documents, it combines text extraction, LLM-powered metadata generation, and consistent output formatting.

## Overview

This application processes documents from URLs through the following pipeline:

1. **Document Download & Text Extraction**: Downloads PDFs or scrapes HTML content
2. **Section Identification**: Intelligently identifies logical sections and titles within the document
3. **Text Cleaning & Normalization**: Standardizes text formatting for better processing
4. **Metadata Generation**: Uses LLMs to extract document metadata (topics, audience, etc.)
5. **Payload Construction**: Builds a standardized payload for Qdrant vector database integration
6. **Output Generation**: Saves processed text and metadata to the filesystem

## Components

### Core Modules

- **extract_and_normalize_pdf.py**: Processing pipeline for PDF documents
- **extract_and_normalize_html.py**: Processing pipeline for HTML webpages
- **config/config.yaml**: Configuration for LLM integration, output paths, and extraction parameters

### Document Processing (`pdf/` and `html_text/`)

- **PDF Processing Modules**
  - PDF downloading and content extraction
  - Section and title detection
  - PDF-specific text normalization

- **HTML Processing Modules**
  - Web page scraping with JavaScript support
  - Content extraction from complex HTML structures
  - Section and title detection from HTML elements
  - Deduplication and cleaning of HTML content

### Common Utilities (`common/`)

- **DocumentUtils**: Core document processing functionality
  - Text extraction and cleaning
  - Section identification
  - File and directory management
  - Metadata payload construction
  - Organization name inference from URLs

- **MetadataGenerator**: LLM-powered metadata extraction
  - Integration with multiple LLM providers (OpenAI, Groq)
  - Structured metadata generation with schema validation
  - Fallback mechanisms for missing information
  - Retry logic for API resilience

## Inputs

- **Document URL**: The application takes a URL to a PDF document or HTML webpage as its primary input
- **Configuration**: Optional path to a custom configuration file

### Command-line Usage

For PDF documents:
```bash
python extract_and_normalize_pdf.py --url https://example.org/path/to/document.pdf --config config/config.yaml
```

For HTML webpages:
```bash
python extract_and_normalize_html.py --url https://example.org/path/to/webpage --config config/config.yaml
```

### Configuration Options

The application supports multiple LLM providers through configuration settings, with API keys sourced from environment variables for security:

#### OpenAI Configuration

```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  temperature: 0.3
```

Required environment variable: `OPENAI_API_KEY`

#### Groq Configuration

```yaml
llm:
  provider: "groq"
  model: "llama3-8b-8192"  # Alternative: "mixtral-8x7b-32768"
  temperature: 0.3
```

Required environment variable: `GROQ_API_KEY`

#### Environment Variables

API keys must be configured as environment variables for security. These can be set directly in your environment or through the `.env` file specified in the config:

```
# Example .env file
OPENAI_API_KEY=sk-...your-key-here...
GROQ_API_KEY=gsk_...your-key-here...
```

The path to this `.env` file is configured with:

```yaml
env_path: "~/src/python/.env"
```

#### General Configuration

```yaml
env_path: "~/src/python/.env"  # Path to environment variables file
llm_document_chunk_size: 4096  # Maximum text size for LLM processing
output_directory: "output"     # Directory for output files
schema_path: "schemas/base_payload.schema.json"  # Schema for validation

# PDF-specific configuration
section_title_filter:          # Filtering options for section titles
  ignore_if_contains:
    - "table of contents"
    - "page"
    - "framework"

# HTML-specific configuration
html_parameters:
  topic_page:
    title_selector: "h1, .article-title, .title, header h1"
    content_selectors: 
      - "article, .content, .article-content, main"
    subtopics_selector: "h2, h3"
    block_elements: ["p", "div", "section", "article", "blockquote"]
    list_elements: ["ul", "ol"]
  rendering:
    wait_time: 3000
    scroll: true
    js_patterns: [".gov", "javascript", "dynamic"]
```

## Outputs

The application generates several outputs in the configured output directory:

### Text Files

- **Page-level text files (PDF)**: `{base_filename}_page{page_number}.txt`
  - Contains the cleaned text content of each page
  - Includes the section title as a header

- **Content text files (HTML)**: `{base_filename}_page1.txt`
  - Contains the cleaned text content from the webpage
  - Includes the page title as a header

### Metadata

- **Base payload JSON**: `{base_filename}_base_payload.json`
  - Contains all extracted metadata including:
    - Document title, language, region/country
    - Publication date (extracted or inferred)
    - Document type (scientific, policy, etc.)
    - Sustainability dimensions (environmental, economic, social)
    - Key topics (agricultural innovation, soil health, etc.)
    - Intended audience (farmers, policymakers, researchers, NGOs)
    - Source organization
    - Document identifier (stable UUID derived from URL)

## Architecture Details

### Error Handling

The application implements robust error handling throughout:
- Document processing errors are caught, allowing processing to continue
- LLM API calls include retry logic with exponential backoff
- HTML scraping includes fallbacks for JavaScript-rendered content
- All operations are wrapped in try/except blocks with detailed logging

### Metadata Schema Validation

All generated metadata is validated against a JSON schema to ensure consistency and completeness.

### Text Processing

The text cleaning process:
1. Removes control characters and form feeds
2. Normalizes whitespace and newlines
3. Preserves paragraph structure with double line breaks
4. Handles Unicode and special characters appropriately
5. For HTML, provides deduplication of content to handle repeated elements

### HTML Processing Features

The HTML processor includes:
- Support for JavaScript-rendered websites using Playwright
- Intelligent content extraction with configurable selectors
- Handling of dynamic content loaded through scrolling
- Clean extraction of structured content (lists, headers, paragraphs)
- Rate limiting and polite scraping practices

### LLM Provider Abstraction

The application supports multiple LLM providers through a provider-agnostic interface:
- Provider-specific client initialization
- Consistent prompt templates across providers
- Unified error handling and retry logic
- Configuration-driven provider selection

## Dependencies

- **PDF Processing**: PyMuPDF (fitz)
- **HTML Processing**: BeautifulSoup4, Playwright
- **LLM Integration**: OpenAI and Groq API clients
- **Data Validation**: jsonschema
- **Resilience**: tenacity for retry logic
- **HTTP Operations**: requests
- **Configuration**: PyYAML, python-dotenv

## Environment Setup

The project uses a Conda environment defined in `environment.yaml` for dependency management. To set up the environment:

1. Ensure you have [Conda](https://docs.conda.io/en/latest/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed
2. Clone this repository
3. Create and activate the environment with:

```bash
conda env create -f environment.yaml
conda activate extract-and-normalize
```

4. If processing HTML with JavaScript, initialize Playwright browsers:

```bash
playwright install chromium
```

This will install all required dependencies including:
- Python 3.10
- Core packages: requests, urllib3, PyYAML, nltk
- HTML parsing: BeautifulSoup4, Playwright
- LLM clients: openai, groq
- Support libraries: python-dotenv, PyMuPDF, jsonschema, tenacity

## Extending the Application

### Adding New LLM Providers

To add support for a new LLM provider:
1. Update the `_initialize_llm_client` method in `MetadataGenerator`
2. Add provider-specific logic to the `_call_llm` method
3. Update the configuration template with provider-specific options

### Supporting Different Document Types

To adapt the application for different document types:
1. Modify the schema in `schemas/` directory
2. Update the prompt template in `MetadataGenerator._build_prompt()`
3. Adjust the document processing parameters in `config.yaml`

### Adding New HTML Selectors

To improve HTML content extraction for specific websites:
1. Update the `content_selectors` list in the configuration
2. Add specific selectors for different website structures
3. Test with a variety of target websites to ensure robust extraction

