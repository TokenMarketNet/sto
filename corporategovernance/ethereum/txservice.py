from corporategovernance import txservice



class LocalAccountTransactionSigningService(txservice.TransactionService):

    def create_transaction(self, params) -> "TransactionResult":
        pass


class LocalAccountSignedTransactionResult(txservice.TransactionService):
    pass


class LocalAccountBroadcastedTransactionResult(txservice.TransactionService):
    pass