import sys
print(f"Python yang dipakai: {sys.executable}")
try:
    import langchain
    print(f"LangChain terinstall versi: {langchain.__version__}")
    from langchain.chains import RetrievalQA
    print("Modul chains BERHASIL ditemukan!")
except ImportError as e:
    print(f"Masih Error: {e}")