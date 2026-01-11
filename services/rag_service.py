import os
from dotenv import load_dotenv

# --- PERBAIKAN IMPORT ---
# Gunakan import standar ini (setelah update library, ini yang paling stabil)
import langchain_classic
from langchain_classic.chains import RetrievalQA 
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import untuk Model Lokal & Google
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_core.prompts import PromptTemplate
# ------------------------

load_dotenv()
# ... (kode selanjutnya tetap sama) ...
my_api_key = os.getenv("GEMINI_API_KEY")
if my_api_key:
    os.environ["GEMINI_API_KEY"] = my_api_key

class RagService:
    def __init__(self):
        self.vector_store = None
        self.qa_chain = None
        
        # 1. MODEL CHAT (Tetap Gemini biar pintar)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0.3,
            google_api_key=my_api_key
        )
        
        # 2. MODEL EMBEDDING (GANTI KE LOKAL / OFFLINE)
        # Model 'all-MiniLM-L6-v2' itu kecil, cepat, dan akurat untuk standar RAG
        print("📥 Memuat Model Embedding Lokal (HuggingFace)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Cek apakah index vector sudah ada
        if os.path.exists("faiss_index"):
            try:
                self.load_vector_db()
            except Exception as e:
                print(f"⚠️ Gagal load index lama: {e}. Silakan build ulang.")
        else:
            print("⚠️ Index belum ada. Silakan panggil API build_index.")

    def build_index(self):
        """Membangun Database Vektor Menggunakan CPU (Cepat & Tanpa Limit)"""
        print("🔄 Sedang membaca data wayang...")
        
        # 1. Load Data
        pdf_loader = PyPDFDirectoryLoader("data_wayang/")
        txt_loader = DirectoryLoader("data_wayang/", glob="*.txt", loader_cls=TextLoader)
        
        documents = []
        documents.extend(pdf_loader.load())
        documents.extend(txt_loader.load())

        if not documents:
            return "❌ Tidak ada file di folder data_wayang!"

        # 2. Pecah text (Chunks)
        # Kita bisa perbesar chunk karena local processing kuat
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"📊 Total potongan data: {len(chunks)} chunks")

        # 3. Buat Vector Store (LANGSUNG GASPOLL - TANPA JEDA/DELAY)
        print("🚀 Memproses Embedding (Menggunakan CPU Laptop)...")
        
        # Tidak perlu batching rumit atau time.sleep karena ini OFFLINE
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # 4. Simpan ke local storage
        self.vector_store.save_local("faiss_index")
        print("✅ Database Wayang berhasil dibuat (Mode Turbo)!")
        
        # Reload chain agar langsung siap pakai
        self.load_vector_db()
        return True

    def load_vector_db(self):
        """Memuat index yang sudah disimpan"""
        # Allow dangerous deserialization karena file kita buat sendiri (Aman)
        self.vector_store = FAISS.load_local(
            "faiss_index", 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        prompt_template = """
        Kamu adalah Asisten Pintar bernama "Cepot" yang ahli tentang budaya Wayang.
        Jawab pertanyaan berdasarkan konteks berikut ini. Jika jawaban tidak ada di konteks,
        katakan "Maaf, Cepot belum mempelajari hal itu di kitab data wayang."
        
        Konteks:
        {context}

        Pertanyaan: {question}

        Jawaban (Bahasa Indonesia yang sopan):
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": PROMPT}
        )
        print("✅ Sistem RAG Siap Digunakan!")

    def get_answer(self, query):
        if not self.qa_chain:
            return "⚠️ Database belum siap. Admin harus menjalankan /api/rag/build dulu."
        
        try:
            result = self.qa_chain.invoke({"query": query})
            return result.get("result", "Maaf, terjadi kesalahan.")
        except Exception as e:
            return f"Error: {str(e)}"

# Singleton Instance
rag_service = RagService()