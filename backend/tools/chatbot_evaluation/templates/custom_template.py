from typing import List
from deepeval.metrics.answer_relevancy.template import AnswerRelevancyTemplate



class CustomAnswerRelevancyTemplate(AnswerRelevancyTemplate):
    @staticmethod
    def generate_statements(actual_output: str):
        return f"""
Given the text, break it down and generate a list of distinct statements it presents. 
Each statement should convey a complete idea. Ambiguous phrases or even standalone words that resemble claims or ideas may also be considered statements.

Example:
Example text:  
To improve soil health, farmers should reduce tillage, plant cover crops, and use compost. Regenerative practices also promote biodiversity and help sequester carbon in the soil.

Expected JSON output:
{{
  "statements": [
    "Farmers should reduce tillage.",
    "Planting cover crops improves soil health.",
    "Compost use is encouraged.",
    "Regenerative practices promote biodiversity.",
    "These practices help sequester carbon in the soil."
  ]
}}

===== END OF EXAMPLE ======

**
IMPORTANT: Return only valid JSON with the key "statements" mapping to a list of strings.
No explanation or text outside the JSON is needed.
**

Text:  
{actual_output}

JSON:
"""



    @staticmethod
    def generate_verdicts(input: str, statements: str):
        return f"""
For the provided list of statements, assess whether each statement is relevant to **addressing the input question or request**, which is specifically about sustainable agriculture.

Please return your answer as a list of JSON objects under the key `verdicts`. Each object must include a `verdict` and, if applicable, a `reason`.

- The `verdict` must be strictly one of the following:  
  - "yes" — The statement directly contributes to answering the input in a meaningful and relevant way.  
  - "idk" — The statement is potentially useful or indirectly related but does not clearly address the input.  
  - "no" — The statement is unrelated or irrelevant.

- Include a `reason` **only if the verdict is "no"**, clearly explaining why the statement does not relate to the input.

⚠️ IMPORTANT:  
- Return only valid JSON.  
- The number of `verdicts` **must exactly match** the number of statements provided.  
- Do not add explanations outside the JSON output.

Example Input:  
What are good ways to restore soil fertility using regenerative agriculture and permaculture?

Example Statements:  
[
  "Reducing tillage helps preserve soil structure.",
  "Using synthetic fertilizers increases yield.",
  "Applying compost improves organic matter in soil.",
  "Installing solar panels is good for clean energy."
]

Example JSON Response:  
{{
  "verdicts": [
    {{ "verdict": "yes" }},
    {{ "verdict": "no", "reason": "Synthetic fertilizers are generally avoided in regenerative practices." }},
    {{ "verdict": "yes" }},
    {{ "verdict": "idk" }}
  ]
}}

Now complete the task using the actual input and statements provided below.

Input:  
{input}

Statements:  
{statements}

JSON Response:
"""


    @staticmethod
    def generate_reason(
        irrelevant_statements: List[str], input: str, score: float
    ):
        return f"""
Given the **answer relevancy score**, the **list of reasons for irrelevant statements** in the actual output, and the **original input**, provide a **concise explanation** for why the score is appropriate.

Your explanation should:
- Justify **why the score is not higher**, referencing the irrelevant content.
- Also explain **why it deserves the current score**, even if not perfect.
- If there are **no irrelevant statements**, simply return a **positive and encouraging comment** (keep it professional and not overly enthusiastic).

⚠️ IMPORTANT: Return only a valid JSON object with a single key `"reason"`.

Example JSON:
{{
  "reason": "The score is 3.5 because the answer included strong points about compost and cover crops, but also mentioned synthetic fertilizers, which go against regenerative principles."
}}

Answer Relevancy Score:  
{score}

Reasons why the score can't be higher (irrelevant statements):  
{irrelevant_statements}

Input:  
{input}

JSON:
"""

