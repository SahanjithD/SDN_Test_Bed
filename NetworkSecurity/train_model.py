import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# 1. Load Data
print("Loading traffic_data.csv...")
try:
    df = pd.read_csv('traffic_data.csv')
except FileNotFoundError:
    print("Error: traffic_data.csv not found!")
    exit()

# 2. Clean Data (Basic)
df = df[df['duration_sec'] > 0] # Remove zero-duration errors

# --- NEW: NOISE FILTER ---
# Drop rows with very few packets (ARP, Hello messages, etc.)
# Real attacks and downloads have thousands of packets.
print(f"Original Row Count: {len(df)}")
df = df[df['packet_count'] > 10]
print(f"Filtered Row Count: {len(df)} (Removed noise)")
# -------------------------

# 3. Feature Engineering
df['packet_rate'] = df['packet_count'] / df['duration_sec']
df['packet_size'] = df['byte_count'] / df['packet_count']
df.replace([np.inf, -np.inf], 0, inplace=True)
df.fillna(0, inplace=True)

# DEBUG: Print Stats to prove separation
print("\n--- Feature Averages by Label ---")
print(df.groupby('label')[['packet_rate', 'packet_size']].mean())
print("---------------------------------\n")

# 4. Select Features
feature_cols = ['packet_rate', 'byte_rate', 'packet_size', 'packet_count', 'byte_count']
X = df[feature_cols]
y = df['label']

# 5. Split & Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Improved Random Forest Model...")
clf = RandomForestClassifier(n_estimators=100)
clf.fit(X_train, y_train)

# 6. Accuracy Check
y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {acc * 100:.2f}%")

# 7. Save
joblib.dump(clf, 'ddos_model.pkl')
print("Success! Filtered model saved.")