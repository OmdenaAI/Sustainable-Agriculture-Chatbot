import logging
from typing import List, Dict, Any, Optional
import httpx
import random

from app.core.config import settings
from app.core.exceptions import AIServiceError

# Setup logging
logger = logging.getLogger(__name__)

class AIService:
    """
    Service for interacting with AI models
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"  # Groq's LLaMA 3 model
        self.mock_mode = True  # Set to True for testing without an API call
        self.mock_responses = self._init_mock_responses()
    
    def _init_mock_responses(self) -> Dict[str, List[str]]:
        """Initialize dictionary of mock responses for different topics"""
        return {
            "default": [
                "As a sustainable agriculture assistant, I'm designed to provide information about farming practices, soil management, crop rotation, and other agricultural topics. How can I help you today?",
                "I'm your sustainable agriculture assistant, ready to discuss topics like organic farming, permaculture, regenerative agriculture, and more. What would you like to learn about?",
                "Welcome! I can provide information about sustainable farming practices, soil health, water conservation, and other agricultural topics. What specific information are you looking for?"
            ],
            "permaculture": [
                "Permaculture is a holistic design approach to agriculture that mimics natural ecosystems. It's based on three core ethics: Earth Care, People Care, and Fair Share. Permaculture designs integrate elements like water management, soil building, and biodiversity to create sustainable, self-sufficient systems. Key principles include using renewable resources, producing no waste, and valuing diversity. Techniques often include food forests, swales for water harvesting, companion planting, and integrating animals with plant systems.",
                "Permaculture, developed by Bill Mollison and David Holmgren in the 1970s, is a design philosophy that creates sustainable human settlements by following nature's patterns. It combines permanent agriculture and permanent culture, focusing on building systems that are sustainable and regenerative. Permaculture gardens typically feature multiple layers (from canopy trees to root crops), diverse plant species that support each other, water-harvesting earthworks, and minimal external inputs. This approach builds soil, increases biodiversity, and creates resilient food systems."
            ],
            "organic farming": [
                "Organic farming is an agricultural method that relies on natural processes and materials instead of synthetic chemicals. It prohibits most synthetic pesticides and fertilizers, GMOs, antibiotics, and growth hormones. Organic farmers build soil health through practices like crop rotation, cover cropping, and application of compost and manure. They manage pests using biological controls, trap crops, and resistant varieties. Organic certification requires following specific standards for at least three years before products can be labeled as organic.",
                "Organic farming focuses on producing food without synthetic chemicals while promoting ecological balance. Key practices include maintaining soil fertility through natural amendments like compost and manure, implementing crop rotations to disrupt pest cycles, using mechanical and biological pest control methods, and often incorporating livestock into the farm system. Organic methods typically lead to improved soil health, increased biodiversity, and reduced water pollution compared to conventional farming."
            ],
            "soil health": [
                "Soil health is foundational to sustainable agriculture. Healthy soil has good structure (aggregation), high organic matter content, diverse microbial communities, and proper nutrient cycling. Farmers can build soil health through practices like minimizing tillage, keeping soil covered with plants or mulch, maintaining living roots in the soil year-round, and diversifying crop rotations. Cover crops are particularly valuable for adding organic matter, preventing erosion, and fixing nitrogen. Healthy soils retain more water, require fewer inputs, and produce more resilient crops.",
                "Soil health refers to the soil's capacity to function as a living ecosystem that supports plants, animals, and humans. Key indicators include soil organic matter, biological activity, water infiltration rate, and aggregate stability. The soil food web—containing bacteria, fungi, protozoa, nematodes, arthropods, and earthworms—plays a crucial role in nutrient cycling and disease suppression. Practices that damage soil health include excessive tillage, leaving soil bare, overuse of synthetic fertilizers, and lack of crop diversity."
            ],
            "crop rotation": [
                "Crop rotation is the practice of growing different crops in sequence on the same land. This technique helps break pest and disease cycles, improves soil structure, balances nutrient use, and can reduce weed pressure. Effective rotations typically alternate between crop families and types, such as following a heavy feeding crop (like corn) with a soil-building legume (like soybeans). More complex rotations might include 5-7 years of different crops. Benefits include reduced need for external inputs, improved yields, and greater farm resilience.",
                "Crop rotation is a systematic approach to deciding which crops to plant where and when. By changing what's grown in a field from year to year, farmers can disrupt pest life cycles, manage soil nutrients more efficiently, and reduce erosion. Rotations often alternate between crops with different root structures, nutrient needs, and pest susceptibilities. For example, deep-rooted crops can follow shallow-rooted ones to access different soil layers. Legumes in the rotation add nitrogen to the soil, benefiting subsequent crops."
            ],
            "sustainable agriculture": [
                "Sustainable agriculture involves farming practices that meet society's present food needs without compromising the ability of future generations to meet their own needs. It integrates three main objectives: environmental health, economic profitability, and social equity. Sustainable farming methods include reducing tillage, using cover crops, integrating livestock and crops, practicing precise resource management, and implementing agroforestry systems. These approaches aim to minimize environmental impacts while maintaining productivity and supporting rural communities.",
                "Sustainable agriculture is a holistic approach to food production that balances environmental stewardship, farm profitability, and community well-being. Key practices include conserving soil and water resources, reducing dependence on non-renewable energy, promoting biodiversity, and maintaining the economic viability of farm operations. Sustainable systems often emphasize local production and distribution, reducing food miles and strengthening food security. This approach treats the farm as an interconnected system rather than focusing on maximizing yield of a single crop."
            ],
            "regenerative agriculture": [
                "Regenerative agriculture goes beyond sustainability to actively restore and enhance natural resources. This approach focuses on rebuilding soil organic matter, restoring biodiversity, improving the water cycle, and enhancing ecosystem services. Common regenerative practices include no-till farming, cover cropping, composting, managed grazing, and agroforestry. Unlike conventional farming that often degrades land over time, regenerative methods aim to leave the land better with each growing season, sequestering carbon and increasing resilience to climate extremes.",
                "Regenerative agriculture is a conservation and rehabilitation approach to farming that focuses on topsoil regeneration, biodiversity enhancement, and improving the water cycle. It emphasizes building soil health through minimizing soil disturbance, keeping soil covered, maintaining living roots, and maximizing crop diversity. Properly managed livestock can play a key role through holistic planned grazing. Regenerative systems capture carbon in soil and aboveground biomass, potentially helping to reverse climate change while producing nutrient-dense food."
            ],
            "companion planting": [
                "Companion planting is the strategic placement of different plants near each other to provide mutual benefits. These benefits include pest management (like marigolds repelling nematodes), improved pollination (by attracting beneficial insects), nutrient sharing (legumes fixing nitrogen for heavy feeders), or physical support (like corn supporting bean vines). Classic companion combinations include the Native American 'Three Sisters' of corn, beans, and squash, and planting aromatic herbs near vegetables to confuse or repel pests. Effective companion planting requires understanding plant relationships and careful garden planning.",
                "Companion planting leverages the natural relationships between plants to improve growth and protect against pests. Some plants exude chemicals that either attract beneficial insects or deter harmful ones. For example, basil planted with tomatoes can improve flavor and repel tomato hornworms. Other companions provide physical benefits, like tall plants creating shade for sun-sensitive crops. Some plant combinations improve soil fertility, such as deep-rooted plants bringing nutrients up for shallow-rooted neighbors. Understanding these synergistic relationships can reduce the need for external inputs in the garden."
            ],
            "composting": [
                "Composting is the biological decomposition of organic materials into a nutrient-rich soil amendment. The process requires balancing 'green' materials (nitrogen-rich items like food scraps and fresh plant matter) with 'brown' materials (carbon-rich items like dried leaves, straw, or wood chips). Microorganisms break down these materials through aerobic decomposition, generating heat in the process. Well-managed compost piles reach temperatures of 130-150°F, sufficient to kill most weed seeds and pathogens. The finished product improves soil structure, enhances nutrient retention, and introduces beneficial microorganisms to the soil ecosystem.",
                "Composting transforms organic waste into a valuable soil amendment rich in plant nutrients and beneficial microorganisms. The process typically takes 3-12 months, depending on materials, management, and climate conditions. A properly balanced compost has a carbon-to-nitrogen ratio of about 30:1. Regular turning aerates the pile and speeds decomposition. Compost can be applied as a soil amendment, top dressing, mulch, or component in potting mixes. Its benefits include improving soil structure, enhancing water retention, suppressing certain plant diseases, and reducing the need for synthetic fertilizers."
            ],
            "cover crops": [
                "Cover crops are plants grown primarily to benefit the soil rather than for harvest. They provide numerous benefits, including preventing erosion, suppressing weeds, fixing nitrogen (legumes), breaking up compacted soil layers (deep-rooted species), and adding organic matter. Common cover crops include clover, vetch, and peas (legumes); rye, wheat, and oats (grasses); and buckwheat, mustard, and radishes (broadleaves). The timing of planting and termination is crucial, with methods including mowing, rolling, crimping, or incorporating into the soil before the next crop is planted.",
                "Cover crops serve as living mulch during periods when fields might otherwise be bare, particularly over winter or between cash crops. They capture and recycle nutrients that might otherwise leach from the soil, especially nitrogen which can pollute waterways. Different cover crop species address specific needs: legumes add nitrogen, grasses build organic matter and capture excess nitrogen, and brassicas like radish can penetrate compacted soil layers. Many farmers use cover crop mixtures to maximize benefits. Modern no-till systems often use cover crops as part of their management, terminating them with rollers or crimpers to create mulch for the following crop."
            ],
            "hydroponics": [
                "Hydroponics is a soil-less growing method where plants receive nutrients directly through water solutions. This controlled environment agriculture technique provides precise nutrition and growing conditions, leading to faster growth rates and higher yields in less space than conventional farming. Common hydroponic systems include deep water culture (plants float on nutrient solution), nutrient film technique (thin film of flowing solution), and drip systems (solution dripped onto growing medium). While hydroponics requires more technology and energy than soil-based methods, it uses up to 90% less water and can be practiced in urban environments or areas with poor soil quality.",
                "Hydroponics grows plants in nutrient solutions without soil, allowing for year-round production in controlled environments. Plants in hydroponic systems typically grow 30-50% faster than in soil because roots have direct access to nutrients and more oxygen. Common growing media include rockwool, coconut coir, perlite, and expanded clay pellets, which provide physical support while remaining inert. Hydroponic systems require careful monitoring of pH (typically 5.5-6.5), nutrient concentration, and oxygen levels. Major advantages include water efficiency, reduced pest and disease pressure, and the ability to grow in non-traditional locations like rooftops and indoors."
            ],
            "carrots": [
                "Carrots are root vegetables that grow best in loose, sandy loam with good drainage. They prefer cool temperatures (60-70°F) and can be planted as soon as soil can be worked in spring, with additional plantings every 2-3 weeks for continuous harvest. Carrots require consistent moisture, especially during germination, but waterlogged soil causes forking and splitting. Common problems include forked roots (from rocky soil or recent manure), green shoulders (from sun exposure), and carrot rust fly (whose larvae tunnel into roots). Harvest when roots reach desired size, typically 60-80 days after planting, depending on variety.",
                "Carrots (Daucus carota) are biennial plants grown as annuals, belonging to the Apiaceae family along with parsley and celery. They're rich in beta-carotene, fiber, potassium, and antioxidants. For best growth, soil should be free of stones and worked to at least 12 inches deep. Companion plants that benefit carrots include onions, leeks, and rosemary (which help repel carrot flies), while dill should be avoided as it can cross-pollinate with carrots, affecting seed quality. Carrots store well in the ground during cool weather and can be kept for months in cold storage with high humidity."
            ],
            "himalayas": [
                "Agriculture in the Himalayas involves unique challenges and opportunities due to the mountainous terrain and varied climatic zones. Traditional farming in this region focuses on terraced fields that prevent erosion on steep slopes. Major crops include rice, wheat, maize, millet, barley, and potatoes, with fruit trees like apple, pear, and apricot grown at middle elevations. Indigenous knowledge systems have developed crop varieties adapted to high altitudes, cold temperatures, and short growing seasons. Climate change poses significant challenges, with retreating glaciers affecting water availability for irrigation.",
                "Himalayan agriculture is characterized by vertical zonation, with different crops grown at different elevations based on temperature and precipitation patterns. Lower elevations (up to 1,800m) support subtropical crops, middle elevations (1,800-2,800m) are suitable for temperate crops, and higher areas (above 2,800m) grow cold-resistant crops like barley and buckwheat. Many farmers practice mixed crop-livestock systems, with animals providing draft power, manure, and additional income. Agroforestry is common, integrating trees with crops to provide fruits, fodder, fuel, and environmental services such as slope stabilization."
            ],
            "mountain farming": [
                "Mountain farming requires adaptation to steep slopes, thin soils, limited growing seasons, and extreme weather conditions. Terracing is a primary technique to create level planting areas and prevent erosion. In many mountain regions, farmers have developed specialized crop varieties that mature quickly during short frost-free periods and withstand harsh conditions. Traditional mountain agriculture often maintains high crop diversity as insurance against crop failure, with farmers growing multiple varieties of staple crops. These regions frequently maintain rare landraces and heirloom varieties that have become important genetic resources for plant breeding programs.",
                "Mountain agriculture faces unique challenges but also offers advantages. Challenges include difficult mechanization on steep terrain, soil erosion risks, and limited infrastructure. Benefits include lower pest and disease pressure at higher elevations, temperature conditions that can enhance flavor in fruits and vegetables, and unique microclimates that allow specialized production. Mountain farms often serve multiple functions beyond food production, including maintaining traditional cultural landscapes, watershed protection, and biodiversity conservation, leading many governments to provide special support for mountain farming communities."
            ]
        }
    
    async def generate_response(
        self,
        message: str,
        context: List[Dict[str, Any]],
        history: List[Dict[str, str]],
        user_id: str
    ) -> str:
        """
        Generate a response using the AI model
        """
        # If in mock mode, return a specific response based on the topic
        if self.mock_mode:
            logger.info(f"Using mock mode for AI response. Message: '{message}'")
            
            # Handle specific combined queries directly
            if "carrots" in message.lower() and "himalayas" in message.lower():
                logger.info("Detected special case: carrots in himalayas")
                return "Carrots can be grown in the Himalayan region, particularly at middle elevations (1,800-2,800m). In these areas, the cool climate is ideal for carrot cultivation, which thrives in temperatures between 60-70°F. Farmers in the Himalayas often grow carrots on terraced fields with well-drained soil. The region's traditional farming practices include using local organic matter to enrich the soil, which is beneficial for root crops like carrots. The Himalayan carrots are known for their sweet taste, which many attribute to the cooler growing conditions and mineral-rich mountain soil."
            
            # Determine the topic from the message
            message_lower = message.lower().strip()
            logger.info(f"Lowercase message: '{message_lower}'")
            
            # Extract keywords from the message
            words = message_lower.replace('?', '').replace('!', '').replace('.', '').replace(',', '').split()
            logger.info(f"Words extracted: {words}")
            
            # Check if any word in the message directly matches a topic
            matched_topics = []
            
            # First try to match exact phrases
            for topic in self.mock_responses.keys():
                if topic != "default" and topic in message_lower:
                    logger.info(f"Found topic phrase in message: {topic}")
                    matched_topics.append((topic, 10))  # Higher score for exact matches
            
            # Then try to match individual words
            for word in words:
                if len(word) < 3:
                    continue  # Skip short words
                
                for topic in self.mock_responses.keys():
                    if topic == "default":
                        continue
                    
                    # Check if the word is in the topic or the topic is in the word
                    if word == topic:
                        logger.info(f"Found exact word match: {word}")
                        matched_topics.append((topic, 9))  # High score for exact word match
                    elif word in topic:
                        logger.info(f"Word '{word}' is part of topic '{topic}'")
                        matched_topics.append((topic, 5))  # Medium score
                    elif topic in word and len(topic) >= 4:
                        logger.info(f"Topic '{topic}' is part of word '{word}'")
                        matched_topics.append((topic, 3))  # Lower score
            
            # Sort by score (highest first) and remove duplicates
            if matched_topics:
                # Sort by score
                matched_topics.sort(key=lambda x: x[1], reverse=True)
                logger.info(f"All matched topics with scores: {matched_topics}")
                
                # Keep highest score for each topic
                unique_topics = []
                seen_topics = set()
                for topic, score in matched_topics:
                    if topic not in seen_topics:
                        unique_topics.append(topic)
                        seen_topics.add(topic)
                
                # Pick the first one (highest score)
                selected_topic = unique_topics[0]
                logger.info(f"Selected topic: {selected_topic}")
                
                # Generate custom response for combined topics
                if len(unique_topics) > 1 and "carrots" in unique_topics and "himalayas" in unique_topics:
                    logger.info("Found compound topic: carrots in himalayas")
                    return "Carrots can be grown in the Himalayan region, particularly at middle elevations (1,800-2,800m). In these areas, the cool climate is ideal for carrot cultivation, which thrives in temperatures between 60-70°F. Farmers in the Himalayas often grow carrots on terraced fields with well-drained soil. The region's traditional farming practices include using local organic matter to enrich the soil, which is beneficial for root crops like carrots. The Himalayan carrots are known for their sweet taste, which many attribute to the cooler growing conditions and mineral-rich mountain soil."
                
                return random.choice(self.mock_responses[selected_topic])
            
            logger.info("No specific topic found in message")
            
            # Special handling for words not in our topics
            for word in words:
                if word == "carrots":
                    logger.info("Found 'carrots' without matching topic")
                    return self.mock_responses["carrots"][0]
                elif word == "himalayas":
                    logger.info("Found 'himalayas' without matching topic")
                    return self.mock_responses["himalayas"][0]
            
            # If no specific topic is found, or it's a follow-up question
            if "expand" in message_lower or "tell me more" in message_lower or "elaborate" in message_lower:
                logger.info("Follow-up question detected, checking history")
                # If we have history, try to determine the previous topic
                if history and len(history) >= 2:
                    logger.info(f"History available: {len(history)} messages")
                    previous_user_msg = ""
                    for msg in reversed(history):
                        if msg["role"] == "user":
                            previous_user_msg = msg["content"].lower()
                            logger.info(f"Previous user message: '{previous_user_msg}'")
                            break
                    
                    # Check if the previous message mentioned a specific topic
                    for topic in self.mock_responses.keys():
                        if topic != "default" and topic in previous_user_msg:
                            logger.info(f"Found topic in previous message: {topic}")
                            return random.choice(self.mock_responses[topic])
                    
                    # Check for individual words in previous message
                    prev_words = previous_user_msg.replace('?', '').replace('!', '').replace('.', '').replace(',', '').split()
                    for word in prev_words:
                        if word in self.mock_responses and word != "default":
                            logger.info(f"Found keyword match in previous message: {word}")
                            return random.choice(self.mock_responses[word])
                else:
                    logger.info("No history available or not enough messages")
            
            # If no specific topic is found, return a default response
            logger.info("Returning default response")
            return random.choice(self.mock_responses["default"])
            
        try:
            # Format context for the prompt
            context_text = ""
            if context:
                context_text = "\n\n".join([doc["text"] for doc in context])
            
            # Create system message with agriculture focus and context
            system_message = {
                "role": "system",
                "content": f"""You are an agriculture expert assistant. 
Your goal is to provide helpful, accurate information about farming, crops, livestock, and agricultural practices.
Always base your answers on the provided context when available.

When you don't know the answer or don't have enough context, admit it and suggest what information might help.
Keep responses concise, practical, and focused on helping farmers and agricultural professionals.

Context information:
{context_text}"""
            }
            
            # Format conversation history
            messages = [system_message]
            
            # Add history messages
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request to AI provider
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Extract the generated text
                generated_text = response_data["choices"][0]["message"]["content"]
                
                return generated_text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise AIServiceError(f"AI API error: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise AIServiceError(f"AI request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise AIServiceError(f"Error generating response: {str(e)}")