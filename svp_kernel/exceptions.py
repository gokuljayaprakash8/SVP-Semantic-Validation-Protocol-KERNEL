# svp_kernel/exceptions.py

class SVPCoreException(Exception):
    """Base exception for all SVP Kernel runtime errors."""
    pass

class SVPSemanticDriftError(SVPCoreException):
    """Raised when an agent's execution sequence violates vector safety thresholds."""
    def __init__(self, message: str, drift_score: float, action: str):
        super().__init__(f"{message} | Action: '{action}' | Drift Score: {drift_score}")
        self.drift_score = drift_score
        self.action = action

class SVPAuthenticationError(SVPCoreException):
    """Raised when the API Gateway rejects the token."""
    pass

class SVPRateLimitExceeded(SVPCoreException):
    """Raised when the compute quota is exhausted."""
    pass
  
