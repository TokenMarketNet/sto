



class TransactionService:
    """Base class for passing through tranasction creation data."""

    def create_transaction(self, params: dict) -> "TransactionResult":
        pass


class TransactionResult:
    """Base class for passing through tranasction result."""