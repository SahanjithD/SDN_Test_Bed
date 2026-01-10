import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 0. Output directory for figures
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)

# 1. Load the Data
try:
    df = pd.read_csv('traffic_data.csv')
    print("✅ File Loaded Successfully.\n")
except FileNotFoundError:
    print("❌ Error: traffic_data.csv not found!")
    exit()

# 2. Check Class Balance
print("--- Class Distribution ---")
counts = df['label'].value_counts()
print(counts)

if 0 not in counts or 1 not in counts:
    print("\n❌ CRITICAL ERROR: You are missing one of the labels (0 or 1).")
    print("   Do NOT train. Go back and collect the missing data.")
    exit()
else:
    print("\n✅ Balance looks good (You have both Normal and Attack data).")

# 3. Compare Traffic Patterns
print("\n--- Traffic Statistics (Averages) ---")
# Group by Label to see the difference
stats = df.groupby('label')[['packet_count', 'byte_rate']].mean()
print(stats)

# 4. Logic Check
normal_rate = stats.loc[0, 'byte_rate']
attack_rate = stats.loc[1, 'byte_rate']

print("\n--- Logic Check ---")
if attack_rate > (normal_rate * 2):
    print(f"✅ PASSED: Attack traffic is significantly faster ({attack_rate:.0f} vs {normal_rate:.0f})")
    print("   The model should easily learn to distinguish this.")
else:
    print(f"⚠️ WARNING: Attack traffic is similar to Normal traffic.")
    print("   The model might struggle. Did you use --flood?")

# 5. Peak Data Sample
print("\n--- Sample High-Volume Attack Data ---")
print(df[df['label'] == 1].nlargest(3, 'byte_rate'))

# 6. Visualization for model decision-making
print("\n--- Generating Plots ---")

# Map labels to human-readable names for plotting
df_plot = df.copy()
df_plot['label_name'] = df_plot['label'].map({0: 'Normal', 1: 'Attack'})

plt.figure(figsize=(8, 5))
sns.histplot(data=df_plot, x='byte_rate', hue='label_name', bins=50, kde=True, element='step', stat='density')
plt.title('Byte Rate Distribution by Class')
plt.xlabel('byte_rate')
plt.ylabel('density')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'byte_rate_hist.png'))
plt.close()

plt.figure(figsize=(8, 5))
sns.histplot(data=df_plot, x='packet_count', hue='label_name', bins=50, kde=True, element='step', stat='density')
plt.title('Packet Count Distribution by Class')
plt.xlabel('packet_count')
plt.ylabel('density')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'packet_count_hist.png'))
plt.close()

plt.figure(figsize=(8, 5))
sns.boxplot(data=df_plot, x='label_name', y='byte_rate')
plt.title('Byte Rate Boxplot by Class')
plt.xlabel('Class')
plt.ylabel('byte_rate')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'byte_rate_box.png'))
plt.close()

plt.figure(figsize=(8, 5))
sns.boxplot(data=df_plot, x='label_name', y='packet_count')
plt.title('Packet Count Boxplot by Class')
plt.xlabel('Class')
plt.ylabel('packet_count')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'packet_count_box.png'))
plt.close()

plt.figure(figsize=(8, 6))
sns.scatterplot(data=df_plot.sample(min(5000, len(df_plot)), random_state=42),
                x='packet_count', y='byte_rate', hue='label_name', alpha=0.6, s=20)
plt.title('Packet Count vs Byte Rate (sample)')
plt.xlabel('packet_count')
plt.ylabel('byte_rate')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'packet_vs_byte_scatter.png'))
plt.close()

# Correlation heatmap for numeric features
num_cols = ['packet_count', 'byte_count', 'duration_sec', 'byte_rate']
available = [c for c in num_cols if c in df_plot.columns]
if available:
    corr = df_plot[available].corr()
    plt.figure(figsize=(6, 5))
    sns.heatmap(corr, annot=True, cmap='viridis', fmt='.2f')
    plt.title('Feature Correlation Heatmap')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'feature_corr.png'))
    plt.close()

print(f"✅ Plots saved to: {FIG_DIR}")