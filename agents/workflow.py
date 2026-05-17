"""
Single-call AI orchestration for reflective journal generation.
"""

import json
import re
from typing import Dict

from langchain_core.messages import HumanMessage

from utils.llm import get_llm
from utils.logger import get_logger

logger = get_logger("WorkflowEngine")


def extract_json(text: str) -> dict:
    try:
        # Look for the first '{' and the last '}'
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group()
            return json.loads(json_str)
    except Exception as e:
        logger.warning(f"JSON extraction failed: {e}")
    return {}


class DynamicAssignmentWorkflow:
    def __init__(self, topic: str):
        self.topic = topic
        self.llm = get_llm()

    def execute(self) -> Dict[str, str]:
        logger.info(f"Generating content for topic: {self.topic}")
        raw_text = self.run_ai_pipeline(self.topic)
        parsed = self._parse_reflective_json(raw_text)
        
        if self._is_empty_payload(parsed):
            logger.warning("AI payload empty or invalid; applying fallback content.")
            return self._fallback_payload()
            
        return parsed

    def run_ai_pipeline(self, topic: str) -> str:
        prompt = f"""
Generate a HIGHLY DETAILED academic reflective journal.

Topic: {topic}

Return a FLAT JSON object where each value is a SINGLE STRING containing the full content for that section. Use \\n\\n for paragraph breaks.

Follow STRICT structure for the content:

1. Experience (Class Content)
- Write at least 3–5 paragraphs
- Explain concepts in depth
- Include examples explained in class
- Use formal academic tone

2. Feelings (Emotional Reactions)
- Write 1–2 paragraphs
- Include personal understanding and difficulty
- Reflect on learning experience

3. Learning (Key Insights)
- Write in detailed structured format:
  a) Concept 1 explanation  
  b) Concept 2 explanation  
  c) Concept 3 explanation  
- Each point must be clearly explained in 4–6 lines
- Include technical explanation where needed

4. Application (Practical Use)
- Provide 8–10 real-world applications
- Use bullet points
- Each application must be meaningful and specific

5. Conclusion
- Write a strong academic summary paragraph
- Highlight importance of topic

---

IMPORTANT:

- Return ONLY valid JSON
- The JSON must be flat: {{ "experience": "...", "feelings": "...", "learning": "...", "application": "...", "conclusion": "..." }}
- Each field MUST be a string, NOT an object or array.
- Do NOT include "Final Answer"
- Do NOT include extra text
- Do NOT shorten content
- Ensure LONG and DETAILED output (10-mark level depth)

---

FORMAT:

{{
  "experience": "Paragraph 1...\\n\\nParagraph 2...\\n\\nParagraph 3...",
  "feelings": "...",
  "learning": "a) ...\\nb) ...\\nc) ...",
  "application": "• ...\\n• ...",
  "conclusion": "..."
}}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content if hasattr(response, "content") else str(response)

    def _parse_reflective_json(self, text: str) -> Dict[str, str]:
        required = ["experience", "feelings", "learning", "application", "conclusion"]
        
        # Try direct parse first
        try:
            cleaned = text.strip()
            # Remove markdown blocks if AI ignored instructions
            cleaned = re.sub(r"```json\s*", "", cleaned)
            cleaned = re.sub(r"```\s*", "", cleaned)
            
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return {k: str(parsed.get(k, "")).strip() for k in required}
        except:
            pass

        # Use regex extraction as fallback
        extracted = extract_json(text)
        if isinstance(extracted, dict) and extracted:
            return {k: str(extracted.get(k, "")).strip() for k in required}

        return {k: "" for k in required}

    def _is_empty_payload(self, payload: Dict[str, str]) -> bool:
        # Check if any required field is empty
        return not all((payload.get(k, "") or "").strip() for k in ["experience", "feelings", "learning", "application", "conclusion"])

    def _fallback_payload(self) -> Dict[str, str]:
        return {
            "experience": f"I actively engaged with the topic '{self.topic}' through structured reflection and analysis of its core concepts.",
            "feelings": "Initially, I felt a bit overwhelmed by the breadth of the topic, but as I progressed, I became more engaged and curious.",
            "learning": "I learned that this topic is fundamental to understanding practical applications in the field, specifically regarding efficiency and accuracy.",
            "application": "I will apply these insights by incorporating the learned frameworks into my future projects and decision-making processes.",
            "conclusion": "This reflection has solidified my understanding of the topic and motivated me to explore it further in real-world scenarios.",
        }
