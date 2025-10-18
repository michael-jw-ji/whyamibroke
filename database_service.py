from datetime import datetime, timezone
from database import db
from classified_transaction import ClassifiedTransaction
import logging

logger = logging.getLogger(__name__)


def save_classified_transaction(transaction_data, classification_result):
    # Ensure description and amount come from the original POST request
    description = transaction_data.get("description")
    amount = transaction_data.get("amount")

    # The classification_result dictionary already contains 'category', 'subcategory', 'date', 'description', and 'amount'
    # due to the _normalize_output function in ExpenseClassifier, but we ensure we are using the transaction_data
    # for description and amount, and classification_result for category and subcategory.

    if not description or amount is None:
        logger.error(
            "Attempted to save transaction with missing description or amount."
        )
        raise ValueError("Transaction data must include 'description' and 'amount'.")

    try:
        # Construct the ClassifiedTransaction object using ONLY the columns defined in the model.
        # This explicitly avoids passing any unknown keyword arguments like 'company' or 'vendor_name'.
        new_transaction = ClassifiedTransaction(
            date=classification_result.get(
                "date", datetime.now(timezone.utc)
            ),  # Use date from classification or fallback
            description=description,  # Use original description
            amount=amount,  # Use original amount
            category=classification_result.get("category", "OTHER"),
            subcategory=classification_result.get("subcategory", "OTHER"),
        )

        db.session.add(new_transaction)
        db.session.commit()
        logger.info(f"Saved new transaction ID: {new_transaction.id}")
        return new_transaction.id

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to commit transaction to database: {e}")
        raise
