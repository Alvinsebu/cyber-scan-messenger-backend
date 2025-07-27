import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
# Save a file named cyberbullying_data.csv with comment,bullying columns

df = pd.read_csv('cyberbullying_data.csv')
X = df['comment']
y = df['bullying']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english')),
    ('clf', LogisticRegression())
])

pipeline.fit(X_train, y_train)

print(classification_report(y_test, pipeline.predict(X_test)))

joblib.dump(pipeline, 'cyberbully_model.pkl')
