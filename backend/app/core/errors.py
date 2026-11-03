class SilverSurfError(Exception):
    """Base exception for all SilverSurf errors."""
    pass


class ValidationError(SilverSurfError):
    """Raised when scraped data fails validation rules (V1-V5)."""
    pass


class ParserIntegrityError(ValidationError):
    """Raised when HTML/PDF structure does not meet minimum schema integrity."""
    pass


class QuarantineError(ValidationError):
    """Raised when record is moved to quarantine (e.g. >12% DoD move)."""
    pass


class SourceFetchError(SilverSurfError):
    """Raised when upstream source cannot be reached or returns an error."""
    pass


class RateNotFoundError(SilverSurfError):
    """Raised when requested rate does not exist."""
    pass
