import tensorflow as tf
import pandas as pd
model = tf.keras.models.load_model('best_model.keras')
test  = pd.read_parquet("zzzs_train.parquet")
test = test[:100000]
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

test  = make_features(test)

X_test = test[features]


test["awake"] = model.predict(X_test)[:,0]
test["not_awake"] = 1 - model.predict(X_test)[:,0]
smoothing_length = 2*230
test["score"]  = test["awake"].rolling(smoothing_length,center=True).mean().fillna(method="bfill").fillna(method="ffill")
test["smooth"] = test["not_awake"].rolling(smoothing_length,center=True).mean().fillna(method="bfill").fillna(method="ffill")
test["smooth"] = test["smooth"].round()
test.to_csv('final.csv', index=False)