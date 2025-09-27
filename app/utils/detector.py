import os
import re
import numpy as np
import pandas as pd
from collections import Counter
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from tensorflow.keras.layers import Layer
import tensorflow as tf

# -----------------------------
# Custom Layer Definition (1D weight to match saved model)
# -----------------------------
class SimpleAttention(Layer):
    def __init__(self, **kwargs):
        super(SimpleAttention, self).__init__(**kwargs)

    def build(self, input_shape):
        # 1D attention weight vector
        self.W = self.add_weight(
            name='att_weight',
            shape=(input_shape[-1],),  # match saved model
            initializer='random_normal',
            trainable=True
        )
        super(SimpleAttention, self).build(input_shape)

    def call(self, x):
        # Compute attention scores
        e = tf.keras.backend.tanh(tf.keras.backend.dot(x, tf.expand_dims(self.W, -1)))
        a = tf.keras.backend.softmax(e, axis=1)
        output = x * a
        return tf.keras.backend.sum(output, axis=1)

# -----------------------------
# Paths and constants
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "models")
TRAIN_CSV = os.path.join(BASE_DIR, "cyberbullying_data.csv")
MAX_LEN = 100

# -----------------------------
# Text Cleaning
# -----------------------------
def clean_text(t):
    t = str(t).lower()
    t = re.sub(r'http\S+', ' ', t)
    t = re.sub(r'@\w+', ' @user ', t)
    t = re.sub(r'[^a-z0-9@#\s\!\?\.\,\'\u2600-\u27BF]+', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# -----------------------------
# Load Tokenizer
# -----------------------------
with open(os.path.join(MODEL_DIR, "tokenizer.json"), "r") as f:
    tk_json = f.read()
tokenizer = tokenizer_from_json(tk_json)

# -----------------------------
# Load Model with custom layer
# -----------------------------
model = load_model(os.path.join(MODEL_DIR, "bully_model.h5"),
                   compile=False,
                   custom_objects={'SimpleAttention': SimpleAttention})

# -----------------------------
# Convert sentence to model input
# -----------------------------
def sentence_to_input(s):
    s_clean = clean_text(s)
    seq = tokenizer.texts_to_sequences([s_clean])
    pad = pad_sequences(seq, maxlen=MAX_LEN, padding='post', truncating='post')
    return pad

# -----------------------------
# Generate BAD_WORDS dynamically
# -----------------------------
def generate_bad_words(csv_path, min_bully_freq=2, max_non_bully_freq=1):
    df = pd.read_csv(csv_path)
    bullying_texts = df[df['label'] == 1]['text'].apply(clean_text)
    non_bullying_texts = df[df['label'] == 0]['text'].apply(clean_text)

    def get_word_counts(text_series):
        words = " ".join(text_series).split()
        return Counter(words)

    bully_counts = get_word_counts(bullying_texts)
    non_bully_counts = get_word_counts(non_bullying_texts)

    bad_words_dynamic = set()
    for word, count in bully_counts.items():
        if count >= min_bully_freq and non_bully_counts.get(word, 0) <= max_non_bully_freq:
            bad_words_dynamic.add(word)
    return bad_words_dynamic

BAD_WORDS = generate_bad_words(TRAIN_CSV)

def lexical_flag(s):
    s_words = clean_text(s).split()
    found = [w for w in BAD_WORDS if w in s_words]
    return found

# -----------------------------
# Predict Text
# -----------------------------
def predict_text(s, threshold=0.5):
    x = sentence_to_input(s)
    prob = float(model.predict(x, verbose=0)[0][0])
    lex = lexical_flag(s)
    label = 1 if prob >= threshold or len(lex) > 0 else 0
    return {"probability": prob, "label": int(label), "found_lexical": lex}

# -----------------------------
# Wrapper Function
# -----------------------------
def is_bullying(text, threshold=0.6):
    result = predict_text(text, threshold=threshold)
    print(result)
    return bool(result["label"])
