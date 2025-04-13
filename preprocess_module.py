# preprocess_module.py

import pandas as pd

def preprocess_csv(df):
    df = df.copy()

    # 1. Normalize column names
    df.columns = (
        df.columns.str.lower()
        .str.replace(r"\s*\(.*?\)", "", regex=True)
        .str.strip()
        .str.replace(" ", "_")
    )

    # 2. Compute current_value
    df['current_value'] = (
        df['monetary_value'] * (1 - df['depreciation_per_year'] / 100) ** df['age']
    ).astype(int)

    # 3. Safety assignments (excluding movers_safe)
    df['cabin_safe'] = df['airline_baggage_type'] == 'Hand Baggage'
    df['checkin_safe'] = df['airline_baggage_type'] == 'Check-in Baggage'

    # 4. Add a blank movers_safe column for user input later
    df['movers_safe'] = False

    return df
