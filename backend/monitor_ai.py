import asyncio
import json
from app.services.content_generation import get_ai_client

async def test_ai_responses():
    print("\n===== TESTING GEMINI AI QUIZ GENERATION =====")
    
    # The prompt we updated in the backend code
    system_message = """
You are an AI quiz creator specializing in educational assessment.
Create 2 multiple-choice questions based on the following context:

Some planets in our solar system have rings. Saturn has the most visible rings.

For each question:
1. The question should test understanding of concepts from the context
2. Create 4 options with only one being correct
3. Do NOT add any prefixes like A, B, C, D or 1, 2, 3, 4 to the options
4. Each option should be the raw text without any prefixes or numbering
5. Provide a brief explanation for the correct answer

Return the quiz questions in the following JSON format:
[
  { 
    "text": "Question text here?",
    "options": ["Option text without prefixes", "Option text without prefixes", "Option text without prefixes", "Option text without prefixes"],
    "correct_answer": "The full text of the correct option without any prefixes",
    "explanation": "Brief explanation of why this is correct"
  }
]

IMPORTANT: Return only the JSON array without any markdown formatting or code blocks.
DO NOT include any prefixes like "A:", "B:", "1)", "2)" etc. in the options.
"""

    # Get the AI client
    try:
        ai_client = get_ai_client()
        print("Successfully got AI client")
        
        # Call the AI service
        response = await ai_client.chat_completions_create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": "Generate 2 questions about this context."}
            ],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Print the raw response
        print("\nRAW AI RESPONSE:")
        raw_content = response.choices[0].message.content
        print(raw_content)
        
        # Try to parse as JSON and prettify
        try:
            parsed_json = json.loads(raw_content)
            print("\nPARSED RESPONSE (PRETTY):")
            print(json.dumps(parsed_json, indent=2))
            
            # Check specifically for option formatting
            if isinstance(parsed_json, dict) and "questions" in parsed_json:
                questions = parsed_json["questions"]
            elif isinstance(parsed_json, list):
                questions = parsed_json
            else:
                questions = []
                
            if questions:
                print("\nOPTION FORMAT ANALYSIS:")
                for i, q in enumerate(questions):
                    print(f"\nQuestion {i+1}: {q.get(text, No text)}")
                    options = q.get("options", [])
                    print(f"Options ({len(options)}):")
                    for j, opt in enumerate(options):
                        print(f"  Option {j+1}: \"{opt}\"")
                        # Check for prefixes
                        if opt and any(opt.startswith(prefix) for prefix in ["A", "B", "C", "D", "a", "b", "c", "d", "1", "2", "3", "4"]):
                            if any(opt.startswith(f"{prefix}{sep}") for prefix in ["A", "B", "C", "D", "a", "b", "c", "d", "1", "2", "3", "4"] for sep in [".", ")", ":", " "]):
                                print("    ⚠️ DETECTED PREFIX in option!")
        
        except json.JSONDecodeError as e:
            print(f"\nError parsing JSON: {e}")
    
    except Exception as e:
        print(f"Error during AI testing: {str(e)}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(test_ai_responses())

