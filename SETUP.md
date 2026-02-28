x# CramClutch Setup Guide

## 🚀 Quick Setup

### 1️⃣ Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables

1. Open the `.env` file in the project root
2. Replace `your_actual_key_here` with your actual Gemini API key:

```
GEMINI_API_KEY=your_actual_gemini_api_key
```

**Get your Gemini API key:** https://aistudio.google.com/app/apikey

### 4️⃣ Run the Application

```bash
streamlit run app.py
```

### 5️⃣ Test LLM Connection

1. Open the app in your browser (usually http://localhost:8501)
2. Go to the Dashboard tab
3. Click the "Test Gemini" button
4. If you see "✅ Gemini API connected successfully!" → Backend is alive! 🎉

## 📦 Dependencies

- `streamlit` - Web UI framework
- `google-generativeai` - Gemini LLM API
- `pdfplumber` - PDF text extraction
- `python-dotenv` - Environment variable management

## 🔒 Security

- **Never commit `.env` to git** (it's in `.gitignore`)
- **Never hardcode API keys** in source code
- Keep your API key secure and rotate it if exposed

## 🛠️ Troubleshooting

**Error: "GEMINI_API_KEY not found"**
- Make sure `.env` file exists in project root
- Check that API key is set correctly in `.env`
- Restart the Streamlit app after changing `.env`

**Error: Module not found**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Gemini API errors**
- Verify your API key is valid
- Check your API quota at Google AI Studio
- Ensure you have internet connection
