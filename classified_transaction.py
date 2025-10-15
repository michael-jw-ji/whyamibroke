from datetime import datetime
from app import db

class ClassifiedTransaction(db.Model):
    __tablename__ = "classified_transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))

    def __repr__(self):
        return f"<ClassifiedTransaction {self.id} {self.description} {self.amount} {self.category}>"
