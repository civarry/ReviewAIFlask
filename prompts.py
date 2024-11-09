# Question generation prompts
COMPLEXITY_INSTRUCTIONS = {
    "Easy": "Generate questions that are straightforward and easily understandable, focusing on key concepts.",
    "Medium": "Create questions that are understandable but include a subtle twist or require connecting concepts.",
    "Hard": "Formulate questions that challenge the user to think critically or make inferences based on the document."
}

def get_question_generation_prompt(question_count, complexity):
    """Generate the prompt for question generation."""
    complexity_text = COMPLEXITY_INSTRUCTIONS.get(complexity, "Specify a valid complexity level.")
    
    return f"""Generate {question_count} unique questions based strictly on the provided document.

    Required: Analyze the provided document to identify key concepts, terminology, and logical flow.

    {complexity_text}

    Instructions:
    1. **Unique Questions**: Each question should cover different content or phrasing.
    2. **Open-ended**: Formulate questions that require critical thinking or inference.
    3. **Document-Based**: Rely solely on the document's content—no external assumptions.

    Output only the questions, with no commentary or additional information."""

def get_answer_validation_prompt(question, answer):
    """Generate the prompt for answer validation."""
    return f"""
    Validation Task
    --------------
    Question: {question}
    Answer: {answer}
    
    Instructions for Validation:
    1. Compare answer against retrieved context from uploaded document
    2. Focus on factual accuracy and completeness
    3. Check if answer directly addresses the question
    4. Ignore any information not from the document context
    
    Required Output Format:
    Verdict: [One word: Correct or Incorrect]
    Feedback: [One clear sentence explaining the verdict, max 30 words]
    """