

# 🛠️ Conversant-AI Backend 🛠️

Welcome to the backend of **Conversant-AI**, the engine that powers real-time language learning and feedback. This backend is built with **FastAPI** and provides secure APIs for user authentication, language processing, and more.

This project serves as the backend for the Conversant-AI frontend.

---

## 🌟 Features

- **User Authentication**: Secure login, registration, and token-based authentication.
- **Access and Refresh Tokens**: Implements JWT-based authentication with token refresh capabilities.
- **Real-Time Language Feedback**: Processes user input and provides corrections and feedback.
- **Database Integration**: Stores user data, preferences, and session details securely.
- **Scalable API Design**: Built with FastAPI for high performance and scalability.
- **Testing**: Includes unit tests for critical components.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ installed on your machine.
- MongoDB running locally or accessible via a connection string.
- Node.js installed (if testing with the frontend).

### Installation

1. Clone the repository:
  ```git clone https://github.com/your-username/conversant-ai-backend.git```
  ```cd conversant-ai-backend```

2. Create and activate a virtual environment:
  ```python3 -m venv venv```
  ```source venv/bin/activate  # On Windows: venv\Scripts\activate```

3. Install dependencies:
  ```pip install -r requirements.txt```

4. Set up environment variables:
    Create a .env file in the root directory based on ```.env.template```

## 🖥️ Running the App
1. Start the backend server:
  ```uvicorn app.app:app --reload```
2. If testing with the frontend, ensure the backend is accessible from the frontend:
    - Run the app to allow calls from Expo Go:
  ```uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload```
    - Replace localhost in the frontend API URL with your machine's local IP address (e.g., ```http://192.168.x.x:8000```).
3. Ensure MongoDB is running locally or accessible via the MONGO_URI in your .env file.


## 🛠️ Project Technologies
**FastAPI**: High-performance web framework for building APIs.
**MongoDB**: NoSQL database for storing user data and application state.
**PyJWT**: Library for creating and verifying JSON Web Tokens.
**Pydantic**: Data validation and settings management.
**Uvicorn**: ASGI server for running the FastAPI app.
**bcrypt**: Secure password hashing.
**dotenv**: For managing environment variables.

## 🔗 Links
  - [➡️ Frontend GitHub Repository](#)
  - [➡️ Backend GitHub Repository](#)
  - [➡️ Live Site](#)

## ✨ Demo
TBA

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.