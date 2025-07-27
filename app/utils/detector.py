import joblib
import os

model_path = os.path.join(os.path.dirname(__file__), '../../cyberbully_model.pkl')
model = joblib.load(model_path)

def is_bullying(text):
    prediction = model.predict([text])
    return bool(prediction[0])