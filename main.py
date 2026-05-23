import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from transformers import pipeline

# ============================================================
# STEP 1: LOAD FAQ DATA
# ============================================================
def load_faqs(filepath):
    """Load FAQ data from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['faqs']

# ============================================================
# STEP 2: CREATE FAQ CHATBOT CLASS
# ============================================================
class FAQChatbot:
    def __init__(self, faqs_path='data/faqs.json'):
        """Initialize the FAQ Chatbot"""
        print("📚 Loading FAQs...")
        self.faqs = load_faqs(faqs_path)
        
        # Extract questions and answers
        self.questions = [faq['question'] for faq in self.faqs]
        self.answers = [faq['answer'] for faq in self.faqs]
        
        print(f"✓ Loaded {len(self.faqs)} FAQs")
        
        # Initialize embedding model
        print("🔄 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create embeddings for all FAQ questions
        print("📝 Creating embeddings for all FAQs...")
        self.question_embeddings = self.embedding_model.encode(
            self.questions, 
            convert_to_numpy=True
        )
        
        # Create FAISS index
        print("🗂️ Building FAISS vector database...")
        dimension = self.question_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(self.question_embeddings))
        
        # Initialize LLM for answer generation
        print("🤖 Loading LLM (GPT-2)...")
        self.generator = pipeline("text-generation", model="gpt2")
        
        print("✅ Chatbot initialized successfully!\n")
    
    def retrieve_relevant_faqs(self, user_query, top_k=2):
        """Retrieve relevant FAQs based on user query"""
        # Convert user query to embedding
        query_embedding = self.embedding_model.encode(
            [user_query], 
            convert_to_numpy=True
        )
        
        # Search FAISS index for similar questions
        distances, indices = self.index.search(query_embedding, k=top_k)
        
        # Get the relevant FAQ answers
        retrieved_faqs = []
        for idx in indices[0]:
            retrieved_faqs.append({
                'question': self.questions[idx],
                'answer': self.answers[idx],
                'id': self.faqs[idx]['id']
            })
        
        return retrieved_faqs
    
    def generate_response(self, user_query, retrieved_faqs):
        """Generate response using retrieved FAQs"""
        # Create context from retrieved FAQs
        context = "\n\n".join([
            f"Q: {faq['question']}\nA: {faq['answer']}" 
            for faq in retrieved_faqs
        ])
        
        # Create prompt for LLM
        prompt = f"""Based on the following FAQ information, answer the user's question naturally.

FAQ Knowledge Base:
{context}

User Question: {user_query}

Answer:"""
        
        # Generate answer using LLM
        response = self.generator(prompt, max_length=100, num_return_sequences=1)
        
        return response[0]['generated_text']
    
    def chat(self, user_query):
        """Main chat function"""
        print(f"\n👤 You: {user_query}")
        
        # Step 1: Retrieve relevant FAQs
        print("\n🔍 Retrieving relevant FAQs...")
        retrieved_faqs = self.retrieve_relevant_faqs(user_query, top_k=2)
        
        print("📖 Found relevant FAQs:")
        for faq in retrieved_faqs:
            print(f"  • Q: {faq['question']}")
        
        # Step 2: Generate response
        print("\n✍️ Generating response...")
        response = self.generate_response(user_query, retrieved_faqs)
        
        print(f"\n🤖 Chatbot: {response}\n")
        
        return response

# ============================================================
# STEP 3: MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("         FAQ CHATBOT - Powered by RAG")
    print("="*60)
    
    # Initialize chatbot
    chatbot = FAQChatbot('data/faqs.json')
    
    # Example queries
    queries = [
        "What is Python used for?",
        "How do I install Python on my computer?",
        "How can I handle errors in my code?",
        "Tell me about lists and dictionaries",
        "What are decorators?"
    ]
    
    print("\n" + "="*60)
    print("Starting FAQ Chatbot Demo...")
    print("="*60)
    
    for query in queries:
        chatbot.chat(query)
        print("-" * 60)
    
    # Interactive mode
    print("\n" + "="*60)
    print("Interactive Mode - Type 'exit' to quit")
    print("="*60 + "\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'exit':
            print("👋 Goodbye!")
            break
        
        if user_input:
            chatbot.chat(user_input)