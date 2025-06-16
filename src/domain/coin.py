from dataclasses import dataclass

@dataclass
class Coin:
    """Represents a cryptocurrency with its basic properties."""
    symbol: str
    name: str
    precision: int

    def __post_init__(self):
        """Validate the coin data after initialization."""
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Name must be a non-empty string")
        if not isinstance(self.precision, int) or self.precision < 0:
            raise ValueError("Precision must be a non-negative integer") 