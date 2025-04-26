import time
import threading

class RateLimiter:
    """
    Rate limiter for API calls to prevent throttling.
    Supports both request-based and token-based rate limiting.
    """
    
    def __init__(self, calls_per_minute=0, tokens_per_minute=0):
        # Request-based rate limiting
        self.calls_per_minute = calls_per_minute if calls_per_minute and calls_per_minute > 0 else 0
        self.call_interval = 60.0 / self.calls_per_minute if self.calls_per_minute > 0 else 0
        self.last_call_time = 0
        
        # Token-based rate limiting
        self.tokens_per_minute = tokens_per_minute if tokens_per_minute and tokens_per_minute > 0 else 0
        self.token_interval = 60.0 / self.tokens_per_minute if self.tokens_per_minute > 0 else 0
        self.token_bucket = self.tokens_per_minute
        self.last_token_refill_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
    
    def _estimate_token_count(self, text):
        """
        Estimate token count based on a simple heuristic.
        
        This is a basic approximation. Different models tokenize differently,
        but this provides a reasonable estimate for rate limiting purposes.
        """
        result = 0

        if text:    
            # Simple estimation: approximately 4 characters per token for English text
            result = len(text) // 4
        return result
    
    def _refill_token_bucket(self):
        """Refill token bucket based on elapsed time."""
        if self.tokens_per_minute:
            current_time = time.time()
            elapsed = current_time - self.last_token_refill_time
            
            # Calculate tokens to add based on elapsed time
            tokens_to_add = int(elapsed * (self.tokens_per_minute / 60.0))
            
            if tokens_to_add > 0:
                self.token_bucket = min(self.token_bucket + tokens_to_add, self.tokens_per_minute)
                self.last_token_refill_time = current_time
    
    def wait(self, text=None):
        """
        Wait if necessary to comply with rate limits.
        
        Args:
            text: Text to estimate token count for token-based rate limiting
            
        Returns:
            int: Estimated token count if text was provided, otherwise 0
        """
        # If no rate limits are set, return immediately
        if not self.calls_per_minute and not self.tokens_per_minute:
            return 0 if not text else self._estimate_token_count(text)
            
        with self.lock:
            # Handle request-based rate limiting
            current_time = time.time()
            elapsed_since_last_call = current_time - self.last_call_time
            request_wait_time = max(0, self.call_interval - elapsed_since_last_call) if self.calls_per_minute else 0
            
            # Handle token-based rate limiting if enabled and text is provided
            token_wait_time = 0
            estimated_tokens = 0
            if self.tokens_per_minute and text:
                estimated_tokens = self._estimate_token_count(text)
                
                # Refill the token bucket based on elapsed time
                self._refill_token_bucket()
                
                # If not enough tokens, calculate wait time
                if estimated_tokens > self.token_bucket:
                    tokens_needed = estimated_tokens - self.token_bucket
                    token_wait_time = tokens_needed * self.token_interval
                
                # Update token bucket
                self.token_bucket = max(0, self.token_bucket - estimated_tokens)
            
            # Wait for the longer of the two wait times
            wait_time = max(request_wait_time, token_wait_time)
            if wait_time > 0:
                time.sleep(wait_time)
                
            self.last_call_time = time.time()
            
            return estimated_tokens 