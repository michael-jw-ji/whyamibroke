from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from classified_transaction import ClassifiedTransaction
from expense_classifier import ExpenseClassifier
from database import db
import os
import logging
from database_service import save_classified_transaction


load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

db.init_app(app)

ENABLE_CLASSIFIER = os.getenv("ENABLE_CLASSIFIER", "False").lower() in (
    "true",
    "1",
    "yes",
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if ENABLE_CLASSIFIER:
    classifier = ExpenseClassifier()
    logger.info("Expense Classifier (Ollama) initialized.")
else:
    classifier = None
    logger.info(
        "Expense Classifier (Ollama) is NOT enabled. Classification will be skipped."
    )


# Main route (your original one)
@app.route("/", methods=["GET"])
def test():
    return "hello world"


# Health check route (for AWS target group)
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/api/classify_transaction", methods=["POST"])
def classify_and_store():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()

    # Required fields
    description = data.get("description")
    amount = data.get("amount")

    # Optional field (Removed from saving, kept for classifier prompt if needed)
    company = data.get("company")

    if description is None or amount is None:
        return jsonify({"msg": "Missing 'description' or 'amount' field"}), 400

    try:
        # Check if the classifier is enabled
        if not classifier:
            category = "UNCLASSIFIED"
            subcategory = "UNCLASSIFIED"
            confidence = 0.0
            logger.warning("Classifier is disabled, using default UNCLASSIFIED status.")
            
            # Use save_classified_transaction helper function
            save_classified_transaction(
                transaction_data={"description": description, "amount": amount},
                classification_result={"category": category, "subcategory": subcategory}
            )
            
            new_transaction_id = "N/A (Classifier Disabled)" # Placeholder since we don't return the ID directly here

        else:
            # 1. Call your custom classifier logic
            classification_result = classifier.classify_transaction(
                description, amount, company
            )

            # 2. Extract results with fallbacks
            category = classification_result.get("category", "OTHER")
            subcategory = classification_result.get("subcategory", "OTHER")
            confidence = classification_result.get("confidence", 0.0)

            # 3. Save to database using the dedicated service function
            # This function correctly filters the data to only use DB columns
            new_transaction_id = save_classified_transaction(
                transaction_data={"description": description, "amount": amount},
                classification_result=classification_result
            )

        logger.info(
            f"Processed transaction ID {new_transaction_id}: {category}/{subcategory}"
        )

        return jsonify(
            {
                "status": "success",
                "id": new_transaction_id,
                "description": description,
                "amount": amount,
                "classified_category": category,
                "classified_subcategory": subcategory,
                "confidence": confidence,
            }
        ), 201

    except Exception as e:
        logger.error(f"Error processing transaction: {e}")
        # Return a 500 status code for server-side errors
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Run on port 80 for ECS (HTTP, ALB handles HTTPS)
    app.run(host="0.0.0.0", port=7000) 
