from pathlib import Path
import os
from typing import Optional
from prefect import task
from pipeline.config_manager import ConfigManager
from pipeline.tool_executor import ToolExecutor

class Chunker:
    """
    Chunks text documents into smaller pieces for more efficient processing and embedding.
    """
    
    def __init__(self, config_manager: ConfigManager, tool_executor: ToolExecutor, logger):
        """
        Initialize the chunker with configuration.
        
        Args:
            config_manager: Configuration manager instance
            tool_executor: Tool executor instance
            logger: Logger instance to use throughout the class
        """
        self.logger = logger
        self.config_manager = config_manager
        self.tool_executor = tool_executor
        
        # Get chunker configuration
        self.config = config_manager.get_tool_config("chunker")
        
        # Get Docker configuration
        self.docker_config = self.config_manager.get_docker_config("chunker")
    
    def is_enabled(self) -> bool:
        """
        Check if chunking is enabled in configuration.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.config_manager.is_tool_enabled("chunker")
    
    @task(name="chunk-document")
    def process(self, input_dir: Path) -> Optional[Path]:
        """
        Process extracted content by chunking it into smaller pieces.
        
        Args:
            input_dir: Directory containing extracted content
            
        Returns:
            Path to the chunked document directory or None if chunking failed
        """
        output_dir = None
        
        # Process only if all conditions are met
        if self.is_enabled() and input_dir is not None and input_dir.exists():
            # Get volume configuration using ConfigManager Facade methods
            output_volume = self.config_manager.get_output_volume("chunker")
            input_volume = self.config_manager.get_input_volume("chunker")
            extra_volumes = self.config_manager.get_extra_volumes("chunker")
            
            # Validate output volume and get host path
            host_path = self.config_manager.get_host_path_from_volume(output_volume)
            
            if host_path:
                # Create chunked directory structure
                chunked_dir = Path(host_path) / "chunked"
                chunked_dir.mkdir(parents=True, exist_ok=True)
                
                # Create output directory with same name as input inside the chunked directory
                output_dir = chunked_dir / input_dir.name
                os.makedirs(output_dir, exist_ok=True)
                
                self.logger.info(f"Chunking content from {input_dir}")
                
                # Get Docker image and configuration
                image_name = self.config_manager.get_docker_image("chunker") 
                env_file = self.config_manager.get_env_file("chunker")
                
                # Map input and output paths
                container_input_path = f"/app/input/{input_dir.name}"
                container_output_path = f"/app/output/chunked/{input_dir.name}"
                
                # Prepare arguments
                args = [
                    "--input", container_input_path,
                    "--output", container_output_path
                ]
                
                # Add chunk size if specified
                chunk_size = self.config.get("chunk_size")
                if chunk_size:
                    args.extend(["--chunk-size", str(chunk_size)])
                    
                # Add chunk overlap if specified
                chunk_overlap = self.config.get("chunk_overlap")
                if chunk_overlap:
                    args.extend(["--chunk-overlap", str(chunk_overlap)])
                
                # Add config if specified
                config_path = self.config_manager.get_config_path("chunker")
                if config_path:
                    args.extend(["--config", config_path])
                
                # Execute the chunker
                result = self.tool_executor.execute_tool(
                    image_name=image_name,
                    args=args,
                    input_volume=input_volume,
                    output_volume=output_volume,
                    env_file=env_file,
                    extra_volumes=extra_volumes,
                    tool_name="chunker",
                    timeout=self.config_manager.get_timeout("chunking"),
                    doc_id=input_dir.name
                )
                
                # Check result
                if result.get("status") == "success":
                    self.logger.info(f"Successfully chunked content from {input_dir}")
                else:
                    self.logger.error(f"Failed to chunk content from {input_dir}. Error: {result.get('error', 'Unknown error')}")
                    output_dir = None
            else:
                self.logger.error("Invalid output volume configuration")
        else:
            # Log the reason why processing was skipped
            if not self.is_enabled():
                self.logger.info("Chunker is disabled, skipping")
            elif input_dir is None:
                self.logger.warning("Input directory is None")
            elif not input_dir.exists():
                self.logger.warning(f"Input directory does not exist: {input_dir}")
                
        return output_dir 