# cyber-scan-messenger-backend
backend service for cyber detection app

# 🛡️ Cyberbullying Detection Web App (Flask + ML)

A full-stack Flask-based API that detects cyberbullying in comments using a trained machine learning model. Users can register, log in, create posts, and comment—while the system flags harmful content.

---

## 🚀 Features

- 🔒 User Authentication (JWT-based)
- 📝 Create Posts and Comments
- 🤖 Cyberbullying Detection using ML
- 🧠 Model trained with TF-IDF + Logistic Regression
- 🔗 MySQL Database
- 🔄 REST API with Flask Blueprints
- 🌐 CORS-enabled for frontend integration

---

## 📦 Tech Stack

- Flask, Flask-JWT-Extended, SQLAlchemy
- scikit-learn, pandas, joblib
- MySQL (via `mysql-connector-python`)
- Marshmallow + Webargs for validation
- CORS and dotenv support

---

## ⚙️ Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/flask_cyberbully_app.git
cd flask_cyberbully_app

### Create Virtual Environment

python -m venv venv
# Activate:
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

### Install Dependencies
pip install -r requirements.txt


## 🔐 Environment Variables
Create a .env file to avoid hardcoding secrets:
SECRET_KEY=****
JWT_SECRET_KEY=****
DATABASE_URL=*****

Update your config.py to read from .env

🧠 Train the ML Model
Use the following to train your model before starting the app:
python train_model.py
It saves the model, tokenizer in models folder.

Ensure you have a CSV named cyberbullying_data.csv with columns: text, lab.

🧪 Initialize Database


python run.py


🧰 API Endpoints

| Endpoint              | Method | Description                  | Auth |
| --------------------- | ------ | ---------------------------- | ---- |
| `/api/register`       | POST   | Register new user            | ❌    |
| `/api/login`          | POST   | Login and get JWT token      | ❌    |
| `/api/post`           | POST   | Create a new post            | ✅    |
| `/api/comment/<post>` | POST   | Add comment & check bullying | ✅    |


📁 Directory Structure

flask_cyberbully_app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── post.py
│   │   └── comment.py
│   └── utils/
│       └── detector.py
├── config.py
├── train_model.py
├── run.py
├── requirements.txt
└── .env (optional, ignored in git)


🛡️ Security Note
Add .env and config.py to .gitignore to avoid pushing secrets:

.env
config.py


📬 Contact
For suggestions or collaboration, contact: [Alvin.Sebastian] – [alvinsebastian779@gmail.com]

