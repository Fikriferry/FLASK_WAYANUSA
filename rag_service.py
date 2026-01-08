from langchain.chains import RetrievalQA 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter # Perhatikan ini pakai text_splitters (pakai s)
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

class RagService:
    def __init__(self):
        self.vector_store = None
        self.qa_chain = None
        # Inisialisasi Model Gemini khusus RAG
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0.3, # Rendah biar faktual, tidak halusinasi
            google_api_key=GOOGLE_API_KEY
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", 
            google_api_key=GOOGLE_API_KEY
        )
        
        # Cek apakah index vector sudah ada (biar gak build ulang terus)
        if os.path.exists("faiss_index"):
            self.load_vector_db()
        else:
            print("⚠️ Index belum ada. Silakan panggil fungsi build_index() sekali saja.")

    def build_index(self):
        """Membaca file di folder data_wayang dan membuat database vector"""
        print("🔄 Sedang membaca data wayang...")
        
        # 1. Load Data (PDF & TXT)
        pdf_loader = PyPDFDirectoryLoader("data_wayang/")
        txt_loader = DirectoryLoader("data_wayang/", glob="*.txt", loader_cls=TextLoader)
        
        documents = []
        documents.extend(pdf_loader.load())
        documents.extend(txt_loader.load())

        if not documents:
            return "❌ Tidak ada file di folder data_wayang!"

        # 2. Pecah text panjang jadi potongan kecil (Chunks)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        # 3. Buat Vector Store (FAISS)
        print("🔄 Membuat embeddings (ini butuh koneksi internet)...")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # 4. Simpan ke local storage
        self.vector_store.save_local("faiss_index")
        print("✅ Database Wayang berhasil dibuat!")
        return True

    def load_vector_db(self):
        """Load database yang sudah disimpan"""
        self.vector_store = FAISS.load_local(
            "faiss_index", 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )

    def get_answer(self, query):
        """Fungsi utama untuk tanya jawab RAG"""
        if not self.vector_store:
            self.load_vector_db()

        # Prompt khusus agar bot bertingkah seperti ahli wayang
        prompt_template = """
        Anda adalah Ki Sabda, ahli pewayangan dari Wayanusa.
        Jawablah pertanyaan berdasarkan konteks berikut ini. 
        Jika jawaban tidak ada di konteks, katakan "Maaf, ilmu saya belum sampai ke sana (Data tidak ditemukan)."
        
        Konteks:
        {context}

        Pertanyaan: {question}

        Jawaban:
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}), # Ambil 3 potongan teks teratas
            chain_type_kwargs={"prompt": PROMPT}
        )

        result = qa_chain.invoke({"query": query})
        return result["result"]

# Inisialisasi Service (Single Instance)
rag_service = RagService()