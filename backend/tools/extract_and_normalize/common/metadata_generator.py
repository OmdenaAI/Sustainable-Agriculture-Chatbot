import json
import logging
import re
from openai import OpenAI
import groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime, timezone
from common.schema_prompt_builder import SchemaPromptBuilder

class MetadataGenerator:
    """Extracts metadata from documents using LLM processing."""
    
    def __init__(self, config, doc_utils, logger, prompt_builder):
        """
        Initialize with configuration, document utilities, logger and prompt builder.
        
        Args:
            config (dict): Configuration settings
            doc_utils (DocumentUtils): Document utilities instance
            logger (Logger): Logger instance
            prompt_builder (SchemaPromptBuilder): Schema prompt builder instance
        """
        self.config = config
        self.logger = logger
        # Use prompt_builder for schema access and validation
        self.prompt_builder = prompt_builder
        
        # LLM configuration
        llm_config = config.get("llm", {})
        self.llm_provider = llm_config.get("provider", "openai")
        self.llm_model = llm_config.get("model", "gpt-3.5-turbo")
        self.temperature = llm_config.get("temperature", 0.3)
        
        # Initialize appropriate LLM client and set provider-specific call method
        self.client = self._initialize_llm_client()
        
        # Set the appropriate call function based on provider
        self._llm_call_func = self._get_provider_call_function()
        
        self.doc_utils = doc_utils
        
        # Extract field descriptions from the prompt builder
        self.fields_section, self.array_fields = prompt_builder.get_field_descriptions()
        self.special_fields = ', '.join([f'`{field}`' for field in self.array_fields])

    def _initialize_llm_client(self):
        """Initialize the LLM client based on provider configuration."""
        result = None
        if self.llm_provider == "openai":
            result = OpenAI()  # The OpenAI client automatically uses OPENAI_API_KEY env var
        elif self.llm_provider == "groq":
            result = groq.Client()  # The Groq client automatically uses GROQ_API_KEY env var
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        return result
    
    def _get_provider_call_function(self):
        """Return the appropriate LLM call function based on provider."""
        result = None
        if self.llm_provider == "openai":
            result = self._call_openai
        elif self.llm_provider == "groq":
            result = self._call_groq
        else:
            raise ValueError(f"No call function available for provider: {self.llm_provider}")
        
        return result
    
    def _call_openai(self, prompt):
        """Call OpenAI's API with the given prompt."""
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content
    
    def _call_groq(self, prompt):
        """Call Groq's API with the given prompt."""
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def _call_llm(self, prompt):
        """Call LLM with retry logic for resilience."""
        self.logger.info(f"Calling {self.llm_provider} LLM model '{self.llm_model}'...")
        
        # Use the function pointer set during initialization
        return self._llm_call_func(prompt)

    def generate_metadata(self, url, text, chunk_size):
        """Generate metadata from document text and validate against schema."""
        prompt = self._build_prompt(text, chunk_size)
        try:
            # Get LLM response
            response_content = self._call_llm(prompt)
            metadata = json.loads(response_content)
            
            # Add source information
            metadata["source_url"] = url
            metadata['source_name'] = self.doc_utils.infer_source_name_from_url(url)

            # Add publication date if missing
            if not metadata.get("date_published"):
                metadata["date_published"] = self._infer_date(text)

            # Use prompt_builder to enforce schema and apply defaults
            metadata = self.prompt_builder.enforce_schema_and_apply_defaults(metadata)

            # Validate against schema
            self.prompt_builder.validate_metadata(metadata)
            
            return metadata
        except Exception as e:
            self.logger.exception("Metadata generation failed.")
            raise

    def _infer_date(self, text):
        """Extract date from text or default to current date."""
        result = None
        # Try to find year pattern (2000-2099) with proper word boundaries
        match = re.search(r"\b(20\d{2})\b", text)
        
        if match:
            inferred_year = match.group(1)
            result = f"{inferred_year}-01-01"
            self.logger.info(f"Inferred date_published from text: {result}")
        else:
            # Default to today's date if no year found
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            result = today_str
            self.logger.warning(f"No date_published found in metadata. Defaulting to today: {today_str}")

        return result
        
    def _build_prompt(self, text, chunk_size):
        """Build prompt using field descriptions from the schema."""
        prompt = f"""
        You are an expert metadata classification assistant for sustainable agriculture documents.

        Your task is to analyze the following document and extract structured metadata fields. Respond strictly with a VALID JSON object containing ONLY the fields listed below.

        DO NOT:
        - Guess or fabricate values
        - Include nulls, placeholders, or unknowns
        - Include fields not explicitly listed
        - Include UUIDs, URLs, source names, or chunk identifiers

        DO:
        - Be conservative and precise
        - Only include fields if clearly and repeatedly supported by the text

        Special instructions for {self.special_fields}:
        - Include an item in either list only if it is clearly stated or strongly implied in at least two distinct places in the document
        - A single mention — even if prominent — is not sufficient
        - Each item must appear in the accepted list below
        - Do not include similar, inferred, or fabricated terms not in the list
        - If no valid items meet the above criteria, omit the entire field — do not return an empty list

        Target JSON Fields:

        {self.fields_section}

        The output must:
        - Include only the above fields
        - Use only accepted values
        - Omit any list field if no valid repeated items are found
        - Be valid JSON with no additional commentary or text

        DOCUMENT STARTS HERE:
        {text[:chunk_size]}
        """
    
        return prompt
