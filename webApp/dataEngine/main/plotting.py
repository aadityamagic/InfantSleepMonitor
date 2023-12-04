import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('final.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
plt.plot(df['timestamp'], df['smooth'], marker='o', linestyle='-')
plt.xlabel('Timestamp')
plt.ylabel('Hours of Sleep')
plt.title('Sleep Pattern Over Time')
tick_locations = df['timestamp'].iloc[::1440]
tick_labels = tick_locations.dt.strftime('%m/%d/%Y %H:%M:%S')

plt.xticks(tick_locations, tick_labels, rotation=45, ha='right')
plt.savefig('sleep_pattern.png')
plt.show()