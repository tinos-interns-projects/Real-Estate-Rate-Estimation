# Prepare a cleaned and optimized Python (.py) script for training a Random Forest model with better performance

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")

# Load the dataset
df = pd.read_csv("housing.csv")

# Drop unnecessary columns
if 'society' in df.columns:
    df.drop('society', axis=1, inplace=True)

# Fill missing values with mode or median
for col in ['location', 'size', 'availability']:
    if col in df.columns and not df[col].mode().empty:
        df[col].fillna(df[col].mode()[0], inplace=True)

for col in ['bath', 'balcony']:
    if col in df.columns:
        df[col].fillna(df[col].median(), inplace=True)

# Extract numeric value from 'size' column
df['size'] = df['size'].str.extract('(\\d+)').astype(float)

# Convert 'total_sqft' to float
def convert_sqft(value):
    try:
        if '-' in str(value):
            tokens = value.split('-')
            return (float(tokens[0]) + float(tokens[1])) / 2
        return float(value)
    except:
        return None

df['total_sqft'] = df['total_sqft'].apply(convert_sqft)
df.dropna(subset=['total_sqft'], inplace=True)

# Remove outliers
def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    return df[(df[column] >= Q1 - 1.5 * IQR) & (df[column] <= Q3 + 1.5 * IQR)]

for col in ['price', 'total_sqft', 'bath', 'size']:
    df = remove_outliers_iqr(df, col)

# Remove top/bottom 1% prices
q1 = df['price'].quantile(0.01)
q99 = df['price'].quantile(0.99)
df = df[(df['price'] > q1) & (df['price'] < q99)]

# Log transform the target
df['price_log'] = np.log1p(df['price'])

# Define features and target
X = df[['area_type', 'availability', 'location', 'size', 'total_sqft', 'bath', 'balcony']]
y = df['price_log']

# Categorical columns to be OneHotEncoded
categorical = ['area_type', 'availability', 'location']
numerical = ['size', 'total_sqft', 'bath', 'balcony']

# Preprocessing pipeline
preprocessor = ColumnTransformer(transformers=[
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical)
], remainder='passthrough')

# Full pipeline with Random Forest
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(random_state=42))
])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
pipeline.fit(X_train, y_train)

# Predict and inverse transform log1p
y_pred_log = pipeline.predict(X_test)
y_pred = np.expm1(y_pred_log)
y_actual = np.expm1(y_test)

# Evaluate
mae = mean_absolute_error(y_actual, y_pred)
mse = mean_squared_error(y_actual, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_actual, y_pred)

print(f"MAE: {mae:.2f}")
print(f"MSE: {mse:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R² Score: {r2:.4f}")