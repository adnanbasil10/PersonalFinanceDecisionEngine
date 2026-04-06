import asyncio
import os
import sys

# Setup environment to load the app correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.user import User
from app.ml.data_generator import generate_transactions
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionCreate

def populate_latest_user():
    db = SessionLocal()
    try:
        # Get the latest user
        user = db.query(User).order_by(User.id.desc()).first()
        if not user:
            print("No users found. Please register on the frontend first!")
            return

        print(f"Found user: {user.email} (ID: {user.id})")
        print("Checking if user already has transactions...")
        
        existing_txns = TransactionService.get_transactions(db, user.id, skip=0, limit=1)
        if existing_txns:
            print(f"User {user.email} already has transactions. Deleting them to start fresh...")
            from app.models.transaction import Transaction
            db.query(Transaction).filter(Transaction.user_id == user.id).delete()
            db.commit()

        print(f"Generating 400 realistic transactions for the last 6 months for {user.email}...")
        
        # We'll use the synthetic data generator
        import pandas as pd
        from datetime import datetime
        
        # Generate transactions dataframe
        df = generate_transactions(n_transactions=400, months=6)
        
        # Format for bulk upload
        txns_to_create = []
        for _, row in df.iterrows():
            # DataGenerator has columns: date, amount, category, merchant
            txns_to_create.append(
                TransactionCreate(
                    date=pd.to_datetime(row['date']).date(),
                    amount=float(row['amount']),
                    category=row['category'],
                    merchant=str(row['merchant']),
                    description=f"Generated {row['category']} transaction"
                )
            )
            
        print("Saving to database via TransactionService...")
        # Bulk create uses batches automatically
        from app.schemas.transaction import TransactionBulkUpload
        TransactionService.bulk_create(db, user.id, txns_to_create)
        
        print("\n✅ SUCCESS! Added 400 transactions.")
        print("👉 Tell the user to simply REFRESH their browser page!")
        
    finally:
        db.close()

if __name__ == "__main__":
    populate_latest_user()
