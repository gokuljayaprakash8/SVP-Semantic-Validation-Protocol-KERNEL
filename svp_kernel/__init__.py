# svp_kernel/__init__.py
from .client import SVPClient
from .decorators import ZeroTrustRuntime
from .exceptions import SVPCoreException, SVPSemanticDriftError

class SVP:
    """
    Semantic Validation Protocol (SVP) Kernel
    Enterprise-grade vector validation for autonomous agent runtimes.
    """
    def __init__(self, api_key: str):
        self.client = SVPClient(api_key=api_key)
        self.runtime = ZeroTrustRuntime(self.client)
        
    def audit(self, actions: list, custom_policies: list = None):
        """Pass a list of strings to calculate cumulative semantic drift."""
        return self.client.audit_sync(actions, custom_policies)
        
    def protect(self, core_intent: str):
        """Decorator to wrap LangChain/CrewAI tools and enforce zero-trust execution."""
        return self.runtime.protect(core_intent)

__version__ = "1.0.0-enterprise"
__all__ = ["SVP", "SVPCoreException", "SVPSemanticDriftError"]
