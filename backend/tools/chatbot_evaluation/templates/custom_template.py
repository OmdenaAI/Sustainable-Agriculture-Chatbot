from typing import List
from deepeval.metrics.answer_relevancy.template import AnswerRelevancyTemplate



class CustomAnswerRelevancyTemplate(AnswerRelevancyTemplate):
    @staticmethod
    def generate_statements(actual_output: str):
        return f"""Given the response from a chatbot about regenerative agriculture, break it down into individual statements. Statements can include specific techniques (e.g., composting, rotational grazing), environmental principles, or benefits. Ambiguous phrases or general claims should also be included.

===== START OF EXAMPLE ======
Example text: 
To improve soil health, farmers should reduce tillage, plant cover crops, and use compost. Regenerative practices also promote biodiversity and help sequester carbon in the soil.

Example JSON
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
IMPORTANT: Please only return JSON format with the "statements" key mapping to a list of strings. No words or explanation is needed.
**

Text:
{actual_output}

JSON:
"""

    @staticmethod
    def generate_verdicts(input: str, statements: str):
        return f"""For each statement from a chatbot response, decide whether it is relevant to the user input about regenerative agriculture. Consider ecological accuracy, relevance to the practice of regenerative agriculture, and the presence of greenwashing or vague claims.
Please generate a list of JSON with two keys: `verdict` and `reason`.
The 'verdict' key should STRICTLY be either a 'yes', 'idk' or 'no'.
Verdict options:
- 'yes': The statement is clearly relevant and accurate to address the original input.
- 'no': The statement is not relevant or contradicts regenerative principles.
- 'idk': The statement is vague, unrelated, or only indirectly supportive.

Provide a reason ONLY if the verdict is 'no'.

===== START OF EXAMPLE ======
Example Input:
What are good ways to restore soil fertility using regenerative agriculture?

Example statements:
[
    "Reducing tillage helps preserve soil structure.",
    "Using synthetic fertilizers increases yield.",
    "Applying compost improves organic matter in soil.",
    "Installing solar panels is good for clean energy."
]

Example JSON:
{{
    "verdicts": [
        {{
            "verdict": "yes"
        }},
        {{
            "verdict": "no",
            "reason": "Synthetic fertilizers can harm soil biology and contradict regenerative practices."
        }},
        {{
            "verdict": "yes"
        }},
        {{
            "verdict": "idk"
        }}
    ]
}}
===== END OF EXAMPLE ======


**
IMPORTANT: Only return JSON format with a 'verdicts' key mapping to a list of JSON objects.
Since you are going to generate a verdict for each statement, the number of 'verdicts' SHOULD BE STRICTLY EQUAL to the number of `statements`.
**
        

Input:
{input}

Statements:
{statements}

JSON:
"""

    @staticmethod
    def generate_reason(
        irrelevant_statements: List[str], input: str, score: float
    ):
        return f"""Given the answer relevancy score and list of irrelevant statements made in the actual output, and the input, provide a CONCISE and SHORT reason for the score. If the response was excellent, acknowledge its alignment with ecological practices. If there were irrelevant parts, highlight what could be improved.
        The irrelevant statements represent things in the actual output that is irrelevant to addressing whatever is asked/talked about in the input.
        If there is nothing irrelevant, just say something positive with an upbeat encouraging tone (but don't overdo it otherwise it gets annoying).



===== START OF EXAMPLE ======
Example JSON:
{{
    "reason": "The score is 3.5 because the response included a useful explanation of cover cropping, but mentioned synthetic fertilizers which are typically avoided in regenerative practices."
}}

===== END OF EXAMPLE ======


**
IMPORTANT: Please make sure to only return in JSON format, with the 'reason' key providing the reason.
**

Answer Relevancy Score:
{score}

Reasons why the score can't be higher based on irrelevant statements in the actual output:
{irrelevant_statements}

Input:
{input}

JSON:
"""
