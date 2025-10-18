import ollama
from ollama import chat
import pandas as pd
import logging
from datetime import date
import json, re
from ddgs import DDGS
import os

logger = logging.getLogger(__name__)


class ExpenseClassifier:
    def __init__(self):
        ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

        self.ollama_client = ollama.Client(host=ollama_host)

        self.confidence_threshold = 0.6
        self.category_schema = """
            Classify this expense into one of the following categories and subcategories:
            - HOME: Mortgage, Rent, Property Tax, Home Insurance, Utilities, Maintenance, Furniture/Appliances, Home Improvement
            - TRANSPORTATION: Car Payment, Car Insurance, Gas, Public Transit, Parking, Tolls, Maintenance, Ride Share, Taxi
            - DAILY LIVING: Groceries, Restaurants, Clothing, Personal Care, Haircut, Phone, Internet, Subscription Services
            - ENTERTAINMENT: Movies, Concerts, Plays, Sports, Recreation, Video Games
            - HEALTH: Health Insurance, Gym, Doctor, Dentist, Medicine, Prescription, Veterinarian, Life Insurance
            - VACATION: Airfare, Flight, Accommodations, Souvenirs
            - OTHER
            """

    def classify_transaction(self, description, amount, company=None):
        ollama_result = self.ask_ollama(description, amount)
        confidence = ollama_result.get("confidence", 0)

        if confidence >= self.confidence_threshold:
            return self._normalize_output(ollama_result, description, amount)

        query = description
        web_info = self.search_web(query)

        enriched_prompt = (
            f"{self.category_schema}\n\n"
            f"Transaction: {description}\n"
            f"Amount: {amount}\n"
            f"Context from web: {web_info}\n\n"
            "Re-evaluate and respond strictly in JSON format with keys "
            "category, subcategory, and confidence (0.0–1.0)."
        )

        refined_result = self.ask_ollama(enriched_prompt, amount)
        refined_confidence = refined_result.get("confidence", 0)

        if refined_confidence >= self.confidence_threshold:
            return self._normalize_output(refined_result, description, amount)

        return self._normalize_output(ollama_result, description, amount)

    def ask_ollama(self, description, amount):
        try:
            prompt = (
                f"You are an expense classification assistant for college students.\n"
                f"{self.category_schema}\n\n"
                "Respond strictly in valid JSON format like this:\n"
                '{ "category": string, "subcategory": string, "confidence": number }\n\n'
                f"Description: {description}\n"
                f"Amount: {amount}\n"
                "Category and subcategory must match one of the above options exactly."
            )

            response = self.ollama_client.chat(
                model="llama3",
                messages=[
                    {
                        "role": "system",
                        "content": "You classify college-related expenses into predefined categories.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            text = response["message"]["content"]

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())

                parsed.setdefault("category", "OTHER")
                parsed.setdefault("subcategory", "OTHER")
                parsed.setdefault("confidence", 0.0)

                parsed.pop("company", None)
                parsed.pop("vendor_name", None)

                return parsed
            else:
                logger.warning(f"No JSON detected in Ollama output: {text[:100]}")
                return {
                    "category": "OTHER",
                    "subcategory": "OTHER",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error(f"Ollama classification error: {e}")
            return {
                "category": "OTHER",
                "subcategory": "OTHER",
                "confidence": 0.0,
            }

    def _normalize_output(self, classification_result, description, amount):
        return {
            "date": date.today().isoformat(),
            "description": description,
            "amount": amount,
            "category": classification_result.get("category", "OTHER"),
            "subcategory": classification_result.get("subcategory", "OTHER"),
        }

    def search_web(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            context = " ".join(r.get("body", "") for r in results if "body" in r)
            logger.info(f"DDGS query: {query}, max_results=3")
            return context[:1000] if context else ""
        except Exception as e:
            logger.error(f"web search error: {e}")
            return ""
