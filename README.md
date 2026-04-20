# CaloriQ: Multimodal Nutrition VQA System

CaloriQ is an AI-powered nutrition analysis platform that allows users to snap photos of nutrition labels and ask natural language questions about their food. The system combines a polished Material 3 Flutter interface with a robust Python backend leveraging OCR and Large Language Models (LLMs).

---

## 🚀 The Big Integration: From Demo to Reality

Originally, this project consisted of two separate entities:
1.  **`backend/` & `flutter_app/`**: A functional but basic-UI prototype with a working ML backend.
2.  **`demoProject-main/`**: A highly polished, premium UI design that used mock data.

### What we did:
We performed a "heart transplant" on the application. We **gutted the old UI** from `flutter_app` and replaced it entirely with the premium design from `demoProject-main`. We then **wired the new UI** to the real Python backend API.

**Status of `demoProject-main`:**
> [!IMPORTANT]
> The `demoProject-main` folder is now **100% obsolete**. All its assets, providers, and UI logic have been migrated into `projects/flutter_app`. You can safely delete the `demoProject-main` folder without breaking the application.

---

## 📂 Project Architecture

The project is divided into three core pillars:

### 1. 📱 Mobile Application (`flutter_app/`)
A high-performance Flutter app built with **Riverpod** for state management and **GoRouter** for navigation.
- **Direct Camera-to-Chat Flow**: No more dummy "Result Screens." When you snap a photo, the app uploads it and takes you directly to the AI chat.
- **VQA Chat Interface**: An interactive messaging UI where you can ask questions like *"Is this keto-friendly?"* or *"How many calories?"*.
- **Authentication**: Real JWT-based login and signup flow.
- **Branding**: Custom "CaloriQ" branding with a consistent Material 3 design system.

### 2. ⚙️ Backend API (`backend/`)
A Flask-based microservice that handles the "heavy lifting."
- **Image Preprocessing**: Uses OpenCV to resize, grayscale, and denoise images for better OCR accuracy.
- **OCR Engine**: Primarily uses **EasyOCR** with a fallback to **PyTesseract** to extract text from labels.
- **Intelligence**:
    - **Nutrition Parser**: Regex-based extraction of Calories, Protein, Fat, Carbs, and Ingredients.
    - **Qwen VQA Engine**: Integrated with the **Qwen 2.5 LLM** (via Ollama) to answer complex nutrition questions.
    - **Health Scoring**: A rule-based system that calculates a health score (1-10) based on nutritional density.

### 3. 🧪 Machine Learning Lab (`ml/`)
The Research & Development (R&D) hub where the intelligence was born.
- **`dataset_generation/`**: Scripts that generate thousands of synthetic nutrition labels and QA pairs to train and test the models.
- **`training/`**: The "Gym" where we train baseline models to recognize patterns in label text.
- **`inference/`**: A testing ground where developers can run images through the model manually to check for accuracy without using the mobile app.

---

## 🛠️ Setup & Running

### 1. Backend Setup
```powershell
cd backend
pip install -r requirements.txt
# Create a .env file with ENABLE_QWEN=true
python app.py
```

### 2. Flutter Setup
Ensure your backend is running, then launch the app:
```powershell
cd flutter_app
flutter pub get
# Use the correct API URL for your environment (localhost for ADB reverse)
flutter run --dart-define=API_BASE_URL=http://localhost:5000/api
```

### 3. ADB Tunneling (For Physical Devices)
If running on a real Android phone via USB:
```powershell
adb reverse tcp:5000 tcp:5000
```

---

## 📝 Current Features
- [x] **Full UI/UX Integration**: Premium design from DemoProject.
- [x] **AI Chat**: Direct integration with Qwen LLM for nutrition Q&A.
- [x] **Real OCR**: Image-to-text processing for live photos.
- [x] **JWT Auth**: Secure user registration and login.
- [x] **Direct Flow**: Camera capture leads straight to conversation.

---

## ⚠️ Important Developer Notes
- **Timeout**: The `ask-question` timeout is set to **90 seconds** to allow the CPU-based EasyOCR and Qwen model enough time to process high-resolution images.
- **Dependencies**: Ensure you have Python 3.11+ and the requirements from `backend/requirements.txt` installed.
