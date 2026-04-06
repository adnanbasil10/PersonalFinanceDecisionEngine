"""
Synthetic financial data generator.
Produces 3000-5000 realistic transactions with seasonal patterns,
weekend effects, merchant diversity, and income-aware spending behavior.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random


# Category definitions with spending profiles
CATEGORY_PROFILES = {
    "Food": {
        "merchants": [
            "Swiggy", "Zomato", "McDonald's", "Domino's", "Starbucks",
            "KFC", "Subway", "Pizza Hut", "Haldirams", "Cafe Coffee Day",
            "Local Restaurant", "Street Food", "Barbeque Nation",
        ],
        "amount_range": (50, 1500),
        "frequency_weight": 0.22,
        "weekend_boost": 1.3,
    },
    "Transport": {
        "merchants": [
            "Uber", "Ola", "Rapido", "Metro Card", "Petrol Pump",
            "Indian Railways", "IRCTC", "Toll Plaza", "Parking",
        ],
        "amount_range": (30, 2000),
        "frequency_weight": 0.12,
        "weekend_boost": 0.7,
    },
    "Entertainment": {
        "merchants": [
            "Netflix", "Amazon Prime", "Hotstar", "PVR Cinemas",
            "BookMyShow", "Spotify", "YouTube Premium", "Gaming Zone",
        ],
        "amount_range": (99, 2000),
        "frequency_weight": 0.06,
        "weekend_boost": 1.5,
    },
    "Shopping": {
        "merchants": [
            "Amazon", "Flipkart", "Myntra", "Ajio", "Reliance Digital",
            "Croma", "DMart", "Shoppers Stop", "Lifestyle",
        ],
        "amount_range": (200, 8000),
        "frequency_weight": 0.08,
        "weekend_boost": 1.4,
    },
    "Bills": {
        "merchants": [
            "Electricity Board", "Jio", "Airtel", "Vi", "BSNL",
            "Water Board", "Gas Connection", "Internet Provider",
        ],
        "amount_range": (200, 5000),
        "frequency_weight": 0.05,
        "weekend_boost": 0.8,
    },
    "Healthcare": {
        "merchants": [
            "Apollo Pharmacy", "1mg", "PharmEasy", "Hospital",
            "Dr. Consultation", "Lab Tests", "Dental Clinic",
        ],
        "amount_range": (100, 5000),
        "frequency_weight": 0.04,
        "weekend_boost": 0.6,
    },
    "Education": {
        "merchants": [
            "Udemy", "Coursera", "Book Store", "Unacademy",
            "Stationery Shop", "College Fees", "Coaching Center",
        ],
        "amount_range": (100, 10000),
        "frequency_weight": 0.03,
        "weekend_boost": 0.5,
    },
    "Groceries": {
        "merchants": [
            "BigBasket", "Blinkit", "Zepto", "JioMart",
            "Local Grocery", "Vegetable Market", "DMart",
        ],
        "amount_range": (100, 4000),
        "frequency_weight": 0.14,
        "weekend_boost": 1.2,
    },
    "Rent": {
        "merchants": ["Landlord", "Housing Society", "PG Accommodation"],
        "amount_range": (5000, 25000),
        "frequency_weight": 0.02,
        "weekend_boost": 1.0,
    },
    "Utilities": {
        "merchants": [
            "Gas Cylinder", "Water Purifier Service", "AC Repair",
            "Plumber", "Electrician", "Home Maintenance",
        ],
        "amount_range": (100, 3000),
        "frequency_weight": 0.03,
        "weekend_boost": 0.9,
    },
    "Subscriptions": {
        "merchants": [
            "Gym Membership", "Magazine", "Cloud Storage",
            "Antivirus", "LinkedIn Premium", "News Subscription",
        ],
        "amount_range": (99, 3000),
        "frequency_weight": 0.03,
        "weekend_boost": 1.0,
    },
    "Travel": {
        "merchants": [
            "MakeMyTrip", "Goibibo", "Booking.com", "AirBnB",
            "Hotel", "Resort", "Travel Agent",
        ],
        "amount_range": (500, 15000),
        "frequency_weight": 0.03,
        "weekend_boost": 1.6,
    },
    "Personal Care": {
        "merchants": [
            "Salon", "Spa", "Nykaa", "Body Shop",
            "Grooming Products", "Laundry",
        ],
        "amount_range": (100, 3000),
        "frequency_weight": 0.04,
        "weekend_boost": 1.3,
    },
    "Gifts": {
        "merchants": [
            "Gift Shop", "Flower Delivery", "Amazon Gift",
            "Archies", "Ferns N Petals",
        ],
        "amount_range": (200, 5000),
        "frequency_weight": 0.02,
        "weekend_boost": 1.2,
    },
    "Investments": {
        "merchants": [
            "Zerodha", "Groww", "SIP Payment", "Mutual Fund",
            "Fixed Deposit", "PPF",
        ],
        "amount_range": (500, 20000),
        "frequency_weight": 0.04,
        "weekend_boost": 0.5,
    },
    "Other": {
        "merchants": [
            "ATM Withdrawal", "Miscellaneous", "Cash Payment",
            "Transfer", "UPI Payment",
        ],
        "amount_range": (50, 5000),
        "frequency_weight": 0.05,
        "weekend_boost": 1.0,
    },
}

# Monthly income for generating realistic spending ratios
DEFAULT_MONTHLY_INCOME = 75000  # INR


def generate_transactions(
    n_transactions: int = 4000,
    months: int = 12,
    monthly_income: float = DEFAULT_MONTHLY_INCOME,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic financial transactions.

    Args:
        n_transactions: Target number of transactions (3000-5000)
        months: Number of months of history
        monthly_income: Monthly income for spending ratios
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns: date, amount, category, merchant, description
    """
    np.random.seed(seed)
    random.seed(seed)

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    records = []

    # Calculate daily transaction target
    total_days = (end_date - start_date).days
    daily_target = n_transactions / total_days

    current_date = start_date

    while current_date <= end_date:
        day_of_week = current_date.weekday()
        is_weekend = day_of_week >= 5
        day_of_month = current_date.day
        month = current_date.month

        # Seasonal spending multiplier
        seasonal_mult = 1.0
        if month == 12:  # December — holiday spending
            seasonal_mult = 1.4
        elif month == 11:  # November — Diwali season
            seasonal_mult = 1.5
        elif month in [1, 2]:  # Post-holiday austerity
            seasonal_mult = 0.85
        elif month in [6, 7]:  # Monsoon — less travel
            seasonal_mult = 0.9

        # Salary week boost (1st-5th of month)
        salary_mult = 1.3 if day_of_month <= 5 else 1.0

        # End-of-month tightening
        if day_of_month >= 25:
            salary_mult *= 0.8

        # Number of transactions for this day
        n_daily = max(1, int(np.random.poisson(daily_target * seasonal_mult * salary_mult)))

        for _ in range(n_daily):
            # Select category based on frequency weights
            categories = list(CATEGORY_PROFILES.keys())
            weights = [CATEGORY_PROFILES[c]["frequency_weight"] for c in categories]
            weights = np.array(weights) / sum(weights)
            category = np.random.choice(categories, p=weights)

            profile = CATEGORY_PROFILES[category]

            # Select merchant
            merchant = random.choice(profile["merchants"])

            # Calculate amount
            low, high = profile["amount_range"]
            amount = np.random.lognormal(
                mean=np.log((low + high) / 3), sigma=0.5
            )
            amount = np.clip(amount, low, high * 1.5)

            # Apply weekend boost
            if is_weekend:
                amount *= profile["weekend_boost"]

            # Apply seasonal multiplier
            amount *= seasonal_mult

            # Rent is monthly — only on 1st or 2nd
            if category == "Rent" and day_of_month > 5:
                continue

            # Subscriptions are roughly monthly
            if category == "Subscriptions" and day_of_month > 7:
                if random.random() > 0.15:
                    continue

            amount = round(amount, 2)

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "amount": amount,
                "category": category,
                "merchant": merchant,
                "description": f"{category} - {merchant}",
            })

        current_date += timedelta(days=1)

    df = pd.DataFrame(records)

    # Trim to target size if overshot significantly
    if len(df) > n_transactions * 1.2:
        df = df.sample(n=n_transactions, random_state=seed).sort_values("date").reset_index(drop=True)

    print(f"Generated {len(df)} transactions over {months} months")
    print(f"Categories: {df['category'].nunique()}")
    print(f"Merchants: {df['merchant'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nCategory distribution:")
    print(df["category"].value_counts().to_string())

    return df


def save_dataset(df: pd.DataFrame, output_dir: str = None) -> str:
    """Save the generated dataset to CSV."""
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data",
        )
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "sample_transactions.csv")
    df.to_csv(filepath, index=False)
    print(f"\nDataset saved to {filepath}")
    return filepath


if __name__ == "__main__":
    df = generate_transactions(n_transactions=4000, months=12)
    save_dataset(df)
