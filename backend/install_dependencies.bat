@echo off
echo ============================================================
echo   Installing Alfresco RAG Dependencies
echo ============================================================
echo.

echo [1/3] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [2/3] Installing core dependencies...
pip install langchain==0.3.14
pip install langchain-community==0.3.14
pip install langchain-openai==0.3.0
pip install langchain-core==0.3.28
pip install chromadb==0.5.23
pip install python-alfresco-api==0.1.3
echo.

echo [3/3] Installing all requirements...
pip install -r requirements.txt
echo.

echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Run: python fix_and_test.py
echo   2. Or run: python test_alfresco_rag.py
echo.
pause
