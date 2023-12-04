import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.model_selection import train_test_split
train = pd.read_parquet("Zzzs_train.parquet")


def make_features(df):
    df['timestamp'] = pd.to_datetime(df['timestamp']).apply(lambda t: t.tz_localize(None))
    df["hour"] = df["timestamp"].dt.hour

    periods = 20
    df["anglez"] = abs(df["anglez"])
    df["anglez_diff"] = df.groupby('series_id')['anglez'].diff(periods=periods).fillna(method="bfill").astype('float16')
    df["enmo_diff"] = df.groupby('series_id')['enmo'].diff(periods=periods).fillna(method="bfill").astype('float16')
    df["anglez_rolling_mean"] = df["anglez"].rolling(periods, center=True).mean().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["enmo_rolling_mean"] = df["enmo"].rolling(periods, center=True).mean().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["anglez_rolling_max"] = df["anglez"].rolling(periods, center=True).max().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["enmo_rolling_max"] = df["enmo"].rolling(periods, center=True).max().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["anglez_rolling_std"] = df["anglez"].rolling(periods, center=True).std().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["enmo_rolling_std"] = df["enmo"].rolling(periods, center=True).std().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["anglez_diff_rolling_mean"] = df["anglez_diff"].rolling(periods, center=True).mean().fillna(
        method="bfill").fillna(method="ffill").astype('float16')
    df["enmo_diff_rolling_mean"] = df["enmo_diff"].rolling(periods, center=True).mean().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["anglez_diff_rolling_max"] = df["anglez_diff"].rolling(periods, center=True).max().fillna(method="bfill").fillna(
        method="ffill").astype('float16')
    df["enmo_diff_rolling_max"] = df["enmo_diff"].rolling(periods, center=True).max().fillna(method="bfill").fillna(
        method="ffill").astype('float16')

    return df


features = ["hour",
            "anglez",
            "anglez_rolling_mean",
            "anglez_rolling_max",
            "anglez_rolling_std",
            "anglez_diff",
            "anglez_diff_rolling_mean",
            "anglez_diff_rolling_max",
            "enmo",
            "enmo_rolling_mean",
            "enmo_rolling_max",
            "enmo_rolling_std",
            "enmo_diff",
            "enmo_diff_rolling_mean",
            "enmo_diff_rolling_max",
            ]
train   = make_features(train)

X = train[features]
y = train["awake"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=None)
model = Sequential([
    Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.5),
    Dense(32, activation='relu'),
    Dropout(0.5),
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

es =  tf.keras.callbacks.EarlyStopping(monitor='val_loss', mode='min',patience=10, verbose=1)
mc = tf.keras.callbacks.ModelCheckpoint("best_model.keras", monitor= 'val_loss', mode='min', save_best_only=True, verbose=1)
model.fit(
    X_train, y_train,
    validation_split = 0.3,
    batch_size = 64,
    callbacks =[es,mc],
    epochs = 10
)