from backend.llm_service import LLMService
import sys

def test_llm():
    print("Testing LLM Service...")
    try:
        llm = LLMService()
        print(f"Model: {llm.model}")
        
        text = "This is a test meeting. We decided to launch the product on Monday. John will handle the marketing."
        print(f"\nInput Text: {text}")
        
        print("\n--- Testing Summary ---")
        summary = llm.summarize(text)
        print(f"Summary Result: {summary}")
        
        print("\n--- Testing Task Extraction ---")
        tasks = llm.extract_tasks(text)
        print(f"Tasks Result: {tasks}")
        
        if summary and tasks:
            print("\n✅ LLM Service is working correctly!")
        else:
            print("\n❌ LLM Service returned empty results.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_llm()
