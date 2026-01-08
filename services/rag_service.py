try:
    from langchain.chains import RetrievalQA
except ImportError:
    # Fallback untuk versi terbaru jika struktur berubah
    from langchain_community.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter # Perhatikan ini pakai text_splitters (pakai s)
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import time

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
        """Membaca file di folder data_wayang dan membuat database vector dengan MODE SABAR"""
        print("🔄 Sedang membaca data wayang...")
        
        # 1. Load Data
        pdf_loader = PyPDFDirectoryLoader("data_wayang/")
        txt_loader = DirectoryLoader("data_wayang/", glob="*.txt", loader_cls=TextLoader)
        
        documents = []
        documents.extend(pdf_loader.load())
        documents.extend(txt_loader.load())

        if not documents:
            return "❌ Tidak ada file di folder data_wayang!"

        # 2. Pecah text panjang (Chunks)
        # Kita perkecil chunk size sedikit agar paketnya lebih ringan
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        print(f"📊 Total potongan data: {len(chunks)} chunks")

        # 3. Buat Vector Store dengan RETRY MECHANISM
        print("🔄 Membuat embeddings (Mode Super Sabar)...")
        
        # KITA KURANGI JADI SANGAT KECIL
        batch_size = 5  # Cuma kirim 5 potong sekaligus
        normal_delay = 5 # Istirahat 5 detik kondisi normal
        
        # Inisialisasi vector store kosong dulu (trik biar loop di bawah rapi)
        self.vector_store = None 

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # --- LOGIKA RETRY (PANTANG MENYERAH) ---
            success = False
            while not success:
                try:
                    if self.vector_store is None:
                        # Batch pertama: Bikin baru
                        self.vector_store = FAISS.from_documents(batch, self.embeddings)
                    else:
                        # Batch selanjutnya: Tambahkan
                        self.vector_store.add_documents(batch)
                    
                    # Kalau berhasil sampai sini, set sukses
                    success = True
                    print(f"   ✅ Batch {i//batch_size + 1} berhasil disimpan.")
                    time.sleep(normal_delay) # Istirahat normal

                except Exception as e:
                    # Kalau Error 429 (Quota Exceeded)
                    if "429" in str(e):
                        print("   ⚠️ Kena Limit Google! Menunggu 60 detik agar dingin...")
                        time.sleep(60) # TUNGGU 1 MENIT PENUH
                        print("   🔄 Mencoba mengirim ulang batch ini...")
                    else:
                        # Kalau error lain (misal internet mati), raise errornya
                        print(f"❌ Error tak terduga: {e}")
                        raise e
            # ---------------------------------------
        
        # 4. Simpan ke local storage
        if self.vector_store:
            self.vector_store.save_local("faiss_index")
            print("✅ Database Wayang berhasil dibuat dengan penuh perjuangan!")
            return True
        else:
            return "❌ Gagal membuat index."

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