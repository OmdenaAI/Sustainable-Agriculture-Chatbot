stop_words = ['seeming', 'once', "'re", 'are', 'own', "'s", 'now', 'ca', 'herein', 'the', 'herself', 'everywhere', 'otherwise', 'anyway', 'as', 'under', 'too', 'seemed', 'mostly', 'so', 'and', 'keep', '’s', 'no', 'anything', 'third', 'either', 'therefore', 'from', 'whom', 'none', 'various', 'his', 're', 'who', 'again', 'name', 'were', 'whereupon', "'m", 'anyhow', 'until', 'forty', 'six', 'every', 'is', 'thru', 'therein', 'whence', 'whole', '‘d', 'hereby', 'thus', 'him', 'first', 'only', 'eight', 'well', '’re', 'several', 'since', 'just', 'in', 'much', 'whither', 'should', 'however', 'whoever', 'move', 'i', 'amount', 'down', 'through', 'very', 'itself', 'together', 'front', 'further', 'side', 'even', 'with', 'indeed', 'throughout', 'most', 'those', 'three', 'across', 'during', 'my', '’d', 'towards', 'quite', 'fifty', 'always', 'really', 'hundred', 'whereas', 'of', 'often', 'everyone', 'others', 'elsewhere', 'twenty', 'whether', 'upon', 'yours', 'whatever', 'must', 'for', 'this', 'already', 'among', 'nor', 'becomes', 'about', 'becoming', 'also', 'that', 'though', 'how', 'made', 'two', 'get', 'we', 'wherein', 'myself', 'our', 'become', 'nevertheless', 'over', 'see', 'seems', 'perhaps', 'around', 'neither', 'when', 'done', 'have', 'here', 'before', "'ll", 'can', 'he', 'alone', 'somehow', 'himself', 'unless', 'n’t', 'does', 'former', 'their', 'eleven', 'at', 'used', 'show', 'please', 'due', 'except', 'above', 'its', 'below', 'full', 'all', 'using', 'serious', '‘ve', 'latter', 'nothing', 'each', '’m', 'go', 'noone', 'top', 'hereupon', 'hers', 'cannot', 'was', 'off', 'within', "'d", 'ten', 'ours', '’ll', 'along', 'nowhere', 'why', 'may', "'ve", 'few', 'per', 'formerly', 'been', 'which', 'out', 'twelve', '‘ll', 'n‘t', 'almost', 'there', 'everything', 'still', 'yourselves', 'latterly', 'these', 'call', 'ever', 'whereafter', 'nobody', 'be', 'am', "n't", 'moreover', 'could', 'yourself', 'me', 'against', 'between', 'someone', 'somewhere', 'you', 'ourselves', 'onto', 'thereby', 'anywhere', 'while', 'hence', 'she', 'back', '‘s', 'her', 'themselves', 'being', 'then', 'else', 'many', 'to', 'your', 'afterwards', 'without', 'whenever', 'toward', 'because', 'one', 'beforehand', 'fifteen', 'a', 'us', 'although', 'behind', 'take', 'hereafter', 'beside', 'or', 'what', 'never', 'something', 'other', 'became', 'nine', 'amongst', 'has', 'thence', 'give', 'say', 'least', 'whose', 'sometimes', 'an', 'via', '‘m', 'empty', 'but', 'into', 'such', 'anyone', 'more', 'bottom', 'thereafter', 'last', 'next', '’ve', 'beyond', 'by', 'on', 'sixty', 'less', 'seem', 'did', 'rather', 'sometime', 'some', 'after', 'mine', 'make', 'another', 'put', 'if', 'whereby', 'yet', 'doing', 'regarding', 'wherever', 'might', 'them', 'where', 'meanwhile', 'same', 'five', 'it', 'than', 'do', 'thereupon', 'four', '‘re', 'would', 'up', 'will', 'part', 'they', 'any', 'namely', 'enough', 'not', 'both', 'besides', 'had']

instructional_stop_words = [
    # === Formatting / Structure ===
    "format", "formats",
    "structure", "structures", "structuring", "structured",
    "form", "forms",
    "present", "presentation", "presenting", "presented",
    "matrix", "matrices",
    "table", "tables",
    "list", "lists",
    "enumerate", "enumeration", "itemize",
    "column", "columns",
    "row", "rows",
    "cell", "cells",

    # === File/Data Types ===
    "json", "yaml", "csv", "xml", "markdown", "text", "texts",
    "file", "files",
    "data", "dataset", "datasets",
    "content", "contents",

    # === Instructional Verbs ===
    "must", "should", "shall", "need", "required",
    "can", "could", "may",
    "do", "does", "doing", "did", "done",
    "show", "shows", "showing", "shown",
    "indicate", "indicates", "indicating", "indicated",
    "explain", "explains", "explaining", "explained",
    "answer", "answers", "answering", "answered",
    "give", "gives", "giving", "given",
    "write", "writes", "writing", "written",
    "generate", "generated", "generating",

    # === Prompting / Instruction ===
    "example", "examples",
    "case", "cases",
    "scenario", "scenarios",
    "response", "responses",
    "solution", "solutions",
    "description", "descriptions",
    "summary", "summaries",
    "title", "titles",
    "introduction", "introductions",
    "conclusion", "conclusions",
    "preference", "preferences",
    "question", "questions",

    # === Clarity / Formatting Adjectives ===
    "clear", "clearly",
    "brief", "concise",
    "detailed", "complete", "comprehensive",
    "precise", "accurate", "specific",

    # === Meta / LLM Context ===
    "assistant", "assistants",
    "user", "users",
    "chat", "conversation", "prompt", "instruction",
    "system", "model", "models",
    "language", "LLM", "query", "queries",
    "task", "tasks", "goal", "objectives", 
    "ways", "way"
]
