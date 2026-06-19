from .ph2_ai_logic.ph2_cohere_bridge import co

def is_coding_question(user_message):
    """
    Checks if the question needs our LeetCode documentation.
    Uses the modern .chat() endpoint (Required for 2025/2026 SDKs).
    """
    
    # We keep the prompt extremely short to save tokens and time
    router_prompt = (
        "Analyze the user message. Is it a question about programming, "
        "data structures, algorithms, or coding logic? "
        "Answer only 'Yes' or 'No'."
    )
    
    try:
        # We use command-light for the router because it's faster and cheaper
        response = co.chat(
            message=f"{router_prompt}\n\nUser Message: {user_message}",
            model='command-a-03-2025', 
            max_tokens=10,
            temperature=0
        )
        
        # Check if the model said 'yes' anywhere in the short response
        answer = response.text.strip().lower()
        return "yes" in answer

    except Exception as e:
        # LOG the error to your terminal so you can see it
        print(f"--- ROUTER ERROR ---")
        print(f"Error details: {e}")
        # Default to True so the RAG process continues if the router fails
        return True