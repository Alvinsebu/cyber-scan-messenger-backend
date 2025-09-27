
# train.py
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import (Input, Embedding, Conv1D, GlobalMaxPooling1D,
                                     Bidirectional, LSTM, Dense, Dropout, concatenate, Layer)
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.text import Tokenizer # pyright: ignore[reportMissingImports]
from tensorflow.keras.preprocessing.sequence import pad_sequences # type: ignore
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping # type: ignore
import re

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # suppress TensorFlow info/warning logs


# -----------------------
# Settings
# -----------------------
MAX_VOCAB = 30000
MAX_LEN = 100
EMBEDDING_DIM = 100
BATCH_SIZE = 64
EPOCHS = 8
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
df = pd.read_csv("cyberbullying_data.csv")

# -----------------------
# Clean & Preprocess
# -----------------------
def clean_text(t):
    t = t.lower()
    t = re.sub(r'http\S+', ' ', t)            # remove urls
    t = re.sub(r'@\w+', ' @user ', t)         # normalize mentions
    t = re.sub(r'[^a-z0-9@#\s\!\?\.\,\'\u2600-\u27BF]+', ' ', t)  # keep basic punctuation and symbols/emojis range
    t = re.sub(r'\s+', ' ', t).strip()
    return t

df['text_clean'] = df['text'].astype(str).apply(clean_text)

# -----------------------
# Tokenizer
# -----------------------
tokenizer = Tokenizer(num_words=MAX_VOCAB, oov_token="<OOV>")
tokenizer.fit_on_texts(df['text_clean'].tolist())
sequences = tokenizer.texts_to_sequences(df['text_clean'].tolist())
X = pad_sequences(sequences, maxlen=MAX_LEN, padding='post', truncating='post')
y = df['label'].values

# Save tokenizer
with open(os.path.join(MODEL_DIR, "tokenizer.json"), "w") as f:
    f.write(tokenizer.to_json())

# -----------------------
# Build hybrid model
# -----------------------
def build_model(vocab_size, embedding_dim=EMBEDDING_DIM, max_len=MAX_LEN):
    inp = Input(shape=(max_len,), name="input")
    x = Embedding(vocab_size, embedding_dim, input_length=max_len, name="emb")(inp)

    # CNN branch (captures local patterns)
    convs = []
    for k in [2,3,4]:
        c = Conv1D(filters=128, kernel_size=k, padding='valid', activation='relu')(x)
        p = GlobalMaxPooling1D()(c)
        convs.append(p)
    cnn_out = concatenate(convs)  # shape = sum(filters)

    # BiLSTM branch (context)
    bl = Bidirectional(LSTM(128, return_sequences=True))(x)

    # Simple attention
    class SimpleAttention(Layer):
        def __init__(self, **kwargs):
            super(SimpleAttention, self).__init__(**kwargs)
        def build(self, input_shape):
            self.w = self.add_weight(shape=(input_shape[-1],), initializer="random_normal", trainable=True)
            super(SimpleAttention, self).build(input_shape)
        def call(self, inputs):
            scores = tf.tensordot(inputs, self.w, axes=1)
            weights = tf.nn.softmax(scores, axis=1)
            context = tf.reduce_sum(inputs * tf.expand_dims(weights, -1), axis=1)
            return context

    att = SimpleAttention()(bl)
    merged = concatenate([cnn_out, att])
    dense = Dense(128, activation='relu')(merged)
    drop = Dropout(0.5)(dense)
    out = Dense(1, activation='sigmoid')(drop)

    model = Model(inputs=inp, outputs=out)
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

model = build_model(vocab_size=min(MAX_VOCAB, len(tokenizer.word_index)+1))
model.summary()

# -----------------------
# Train (simple)
# -----------------------
ckpt = ModelCheckpoint(os.path.join(MODEL_DIR, "bully_model.h5"), save_best_only=True, monitor='val_loss')
early = EarlyStopping(patience=3, monitor='val_loss', restore_best_weights=True)

# small train/val split
from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

history = model.fit(X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=EPOCHS,
                    batch_size=BATCH_SIZE,
                    callbacks=[ckpt, early])

# Save final model (Keras .h5)
model.save(os.path.join(MODEL_DIR, "bully_model_final.h5"))
print("Saved model and tokenizer in", MODEL_DIR)
