"""
Domain Knowledge Base and FAQ Resolver for IN-GRES AI.
Provides authoritative, detailed domain information for:
- What is INGRES (India-Groundwater Resource Estimation System / Indian Ground Water Resource Estimation System)
- How to use the chatbot properly
- GEC-2015 Estimation Methodology
- GWRA Assessment Categories (Safe, Semi-Critical, Critical, Over-Exploited, Saline)
- Stage of Groundwater Extraction (SOE) Formula & Interpretation
- Depth to Water Level (m bgl) vs Groundwater Level Indicator (%)
- Dynamic vs Static / In-Storage Groundwater Resources
- Artificial Recharge Structures & Conservation Techniques
- Units of Measurement (ham, m bgl, mm, %) & Official Data Sources
- Net Groundwater Availability for Future Use
"""

import re
from typing import Optional, Dict, Any

DOMAIN_KNOWLEDGE_ENTRIES = {
    "GREETING_HELLO": {
        "title": "Welcome Greeting",
        "keywords": [
            "hi", "hii", "hiii", "hey", "heyy", "hello", "namaste", "vanakkam",
            "hola", "good morning", "good afternoon", "good evening", "greetings",
            "yo", "sup", "whats up", "what's up"
        ],
        "response": (
            "Hello! 👋 I am the **IN-GRES AI Assistant** for India's Ground Water Resource Estimation System.\n\n"
            "I can help you explore official groundwater datasets, assessments, and weather:\n\n"
            "• **Groundwater Levels & Trends** — *'What is the water level in Kadapa?'*\n"
            "• **GWRA Assessment Categories** — Safe, Semi-Critical, Critical, or Over-Exploited\n"
            "• **Rainfall & Recharge Data** — Annual rainfall and assessed recharge metrics\n"
            "• **Extraction & Availability** — Stage of extraction and net water availability\n"
            "• **Conservation Strategies** — Practical recommendations for recharge and conservation\n"
            "• **Live Weather Forecasts** — Current temperature and conditions for any district\n\n"
            "How can I assist you today? Feel free to ask a question or name any district or state!"
        )
    },

    "HOW_ARE_YOU": {
        "title": "How Are You",
        "keywords": [
            "how are you", "how are u", "how r u", "how are you doing", "how are u doing",
            "how do you do", "hows it going", "how's it going", "how is it going",
            "are you good", "how are things", "how you doing", "how r u doing"
        ],
        "response": (
            "Hello! I am doing great, thank you for asking! 😊\n\n"
            "I am the **IN-GRES AI Assistant**, ready to help you explore India's groundwater resources, official GWRA assessment categories, water table depths, rainfall records, conservation recommendations, and live weather.\n\n"
            "How can I assist you today? Feel free to ask a question or name any district or state!"
        )
    },

    "THANK_YOU": {
        "title": "Thank You",
        "keywords": [
            "thank you", "thanks", "thank u", "thx", "tq", "thank you so much",
            "thanks a lot", "thank you very much", "much appreciated", "thank you assistant"
        ],
        "response": (
            "You're very welcome! 😊\n\n"
            "If you have any more questions about groundwater levels, recharge, extraction, rainfall, or live weather for any district in India, feel free to ask anytime. Have a wonderful day! 💧"
        )
    },

    "GOODBYE": {
        "title": "Goodbye",
        "keywords": [
            "bye", "goodbye", "see you", "cya", "bye bye", "good night", "talk to you later"
        ],
        "response": (
            "Goodbye! 👋 Thank you for using the **IN-GRES AI Assistant**.\n\n"
            "Whenever you need groundwater statistics, GWRA assessments, or live weather updates, I'll be right here to assist. Take care! 💧"
        )
    },

    "WHO_ARE_YOU": {
        "title": "About IN-GRES AI Assistant",
        "keywords": [
            "who are you", "what are you", "who made you", "what is your name",
            "introduce yourself", "tell me about yourself", "who built you"
        ],
        "response": (
            "## 🤖 IN-GRES AI Virtual Assistant\n\n"
            "I am the **IN-GRES AI Assistant**, an intelligent conversational system built for **India's Ground Water Resource Estimation System (INGRES)** — developed by the **Central Ground Water Board (CGWB)**, Ministry of Jal Shakti, Government of India, in collaboration with **IIT Hyderabad**.\n\n"
            "### 🎯 What I Can Help You With:\n"
            "* 📊 **Groundwater Observations**: Depth to water level in **m bgl** and normalized indicators in **%**.\n"
            "* 🏷️ **GWRA Assessment Categories**: Safe, Semi-Critical, Critical, Over-Exploited, and Saline status.\n"
            "* 💧 **Recharge & Extraction**: Annual volumetric groundwater recharge and extraction in **ham** ($1\\text{ ham} = 10\\text{ million liters}$).\n"
            "* 🌧️ **Rainfall Records**: Official IMD annual and monsoon precipitation records.\n"
            "* ⚖️ **Comparative Analytics**: Side-by-side comparison tables between any two Indian districts.\n"
            "* 💡 **Conservation Advice**: Tailored artificial recharge recommendations (check dams, percolation tanks, farm ponds, micro-irrigation).\n"
            "* 🌤️ **Live Weather**: Real-time atmospheric conditions and 3-day weather forecasts via Open-Meteo.\n\n"
            "Feel free to ask a question or type any Indian district name to get started!"
        )
    },

    "WHAT_IS_INGRES": {
        "title": "What is INGRES?",
        "keywords": [
            "what is ingres", "what is in-gres", "what is ingres ai", "what is in gres",
            "tell me about ingres", "explain ingres", "what does ingres stand for",
            "ingres full form", "about ingres", "indian ground water resource estimation system",
            "india ground water resource estimation system", "what is this system", "who created ingres"
        ],
        "response": (
            "## 💧 What is INGRES?\n\n"
            "**INGRES** stands for **India-Groundwater Resource Estimation System** (also known as the **Indian Ground Water Resource Estimation System**).\n\n"
            "### 🏛️ Origin & Development\n"
            "* **Lead Agency**: Developed by the **Central Ground Water Board (CGWB)**, Department of Water Resources, River Development & Ganga Rejuvenation, **Ministry of Jal Shakti**, Government of India.\n"
            "* **Technical Partner**: Developed in collaboration with **IIT Hyderabad**.\n"
            "* **Role**: It is an official automated, GIS-based web application and computational engine designed to assess the dynamic groundwater resources of India.\n\n"
            "### 🎯 Key Objectives & Capabilities\n"
            "1. **Automated Resource Assessment**: Calculates groundwater recharge, extraction, and availability across states, districts, and assessment units using the **GEC (Ground Water Estimation Committee) Methodology** (GEC-2015).\n"
            "2. **Standardized Categorization**: Classifies assessment units into **Safe**, **Semi-Critical**, **Critical**, and **Over-Exploited** categories.\n"
            "3. **Transparent Planning**: Helps policy makers, agricultural planners, and groundwater managers implement targeted recharge structures and regulate extraction.\n\n"
            "### 🤖 About IN-GRES AI Assistant\n"
            "This **IN-GRES AI Virtual Assistant** is an intelligent conversational and analytics companion for the INGRES platform. It enables you to:\n"
            "* Query district-level water table depths (**m bgl**) and normalized indicator values (**%**).\n"
            "* Retrieve official **GWRA Assessment** categories and Stage of Extraction (**SOE %**).\n"
            "* Check annual rainfall (**mm**) and volumetric recharge (**ham**).\n"
            "* Compare groundwater metrics across any two districts in India.\n"
            "* Get tailored **artificial recharge and conservation recommendations**.\n"
            "* View **live real-time weather and 3-day forecasts** (powered by Open-Meteo).\n\n"
            "**Official Source:** Central Ground Water Board (CGWB) · Ministry of Jal Shakti · IN-GRES"
        )
    },

    "HOW_TO_USE_CHATBOT": {
        "title": "How to Use the IN-GRES AI Chatbot Properly",
        "keywords": [
            "how to use chatbot", "how to use chatbot properly", "how to use in-gres ai",
            "how to use ingres ai", "how to use", "how to ask questions", "chatbot guide",
            "user guide", "what can you do", "help guide", "help me use this", "instructions",
            "sample questions", "sample queries", "how does this work"
        ],
        "response": (
            "## 📖 How to Use the IN-GRES AI Chatbot Properly\n\n"
            "The **IN-GRES AI Assistant** allows you to explore official groundwater metrics, assessments, comparisons, conservation advice, and live weather through natural language.\n\n"
            "### 💡 Query Categories & Examples\n\n"
            "| Goal | Example Prompt | What You Receive |\n"
            "|---|---|---|\n"
            "| **Water Level & Depth** | *'What is the groundwater level in Kadapa?'* | Depth to water table (**m bgl**), normalized indicator (**%**), and observation period |\n"
            "| **GWRA Assessment Category** | *'Is Guntur district safe or over-exploited?'* | Official categorization (**Safe**, **Semi-Critical**, **Critical**, **Over-Exploited**) |\n"
            "| **Recharge & Extraction** | *'Show annual recharge and extraction for Kurnool'* | Annual recharge (**ham**), extraction volume, and stage of extraction (**%**) |\n"
            "| **Rainfall Records** | *'What is the annual rainfall in YSR District?'* | Official IMD recorded annual and seasonal rainfall (**mm**) |\n"
            "| **District Comparison** | *'Compare groundwater in Kadapa and Kurnool'* | Comprehensive side-by-side comparison table of all parameters |\n"
            "| **Rankings & Extremes** | *'Which district has the lowest groundwater level?'* | Top ranked districts sorted by depth, recharge, or extraction |\n"
            "| **State Overview** | *'Show groundwater statistics for Andhra Pradesh'* | State-wide aggregate summary and category distribution |\n"
            "| **Conservation Advice** | *'How to improve groundwater in Ananthapuramu?'* | Tailored recharge structures (check dams, percolation tanks, farm ponds) |\n"
            "| **Live Weather** | *'Current weather in Theni'* | Live temperature, humidity, wind, and 3-day forecast from Open-Meteo |\n"
            "| **Conceptual Knowledge** | *'What is GEC methodology?'* or *'What is Stage of Extraction?'* | Authoritative explanations of groundwater concepts and formulas |\n\n"
            "### 🌟 Pro Tips for Best Results\n"
            "1. **Include the District Name**: Specific district names (e.g., *'Kadapa'*, *'Kurnool'*, *'Guntur'*) return instant, verified database records.\n"
            "2. **Use Context Follow-Ups**: The chatbot remembers your current topic. After asking about a district, you can simply ask *'What is its rainfall?'* or *'Give conservation suggestions for it.'*\n"
            "3. **Ask Direct Metrics**: You can ask for specific metrics like *'stage of extraction'*, *'annual recharge'*, *'water level'*, or *'weather'*."
        )
    },

    "GWRA_CATEGORIES": {
        "title": "GWRA Assessment Categories Explained",
        "keywords": [
            "gwra categories", "assessment categories", "what is safe category",
            "what is semi critical", "what is semi-critical", "what is critical category",
            "what is over exploited", "what is over-exploited", "what is saline category",
            "category criteria", "safe semi critical critical over exploited", "categorization criteria",
            "what do categories mean", "stage of extraction categories"
        ],
        "response": (
            "## 📊 GWRA Assessment Categories & Criteria\n\n"
            "Under the **Ground Water Resource Assessment (GWRA)** methodology established by the Central Ground Water Board (CGWB), assessment units (districts, blocks, mandals, talukas) are categorized based on two main criteria:\n"
            "1. **Stage of Groundwater Extraction (SOE %)** = $(\\text{Total Extraction} / \\text{Extractable Resource}) \\times 100$\n"
            "2. **Long-Term Water Table Trends** (Pre-monsoon and Post-monsoon trends over a 10-year period)\n\n"
            "### 🏷️ Categorization Matrix\n\n"
            "| Category | Stage of Extraction (SOE) | Water Table Trend Criteria | Status & Management Implications |\n"
            "|---|:---:|---|---|\n"
            "| 🟢 **Safe** | **$\\le 70\\%$** | No significant long-term decline in pre- or post-monsoon water levels | Sustainable. Groundwater development is feasible under controlled monitoring. |\n"
            "| 🟡 **Semi-Critical** | **$> 70\\%$ and $\\le 90\\%$** | May exhibit significant decline in either pre-monsoon or post-monsoon water levels | Caution required. Intensive monitoring, water-use efficiency, and artificial recharge needed. |\n"
            "| 🟠 **Critical** | **$> 90\\%$ and $\\le 100\\%$** | Significant decline in both pre-monsoon and post-monsoon water levels | Severe stress. Extraction should be strictly regulated; heavy focus on rainwater harvesting. |\n"
            "| 🔴 **Over-Exploited** | **$> 100\\%$** | Extraction exceeds annual replenishable recharge; significant water table depletion | Unsustainable depletion. Pumping restrictions, micro-irrigation, and mandatory artificial recharge required. |\n"
            "| ⚪ **Saline** | Quality-based | Groundwater in assessment unit has electrical conductivity / salinity exceeding permissible limits | Fresh water resources are severely limited due to chemical/saline contamination. |\n\n"
            "**Source:** CGWB Ground Water Resource Assessment Guidelines (GEC-2015)"
        )
    },

    "STAGE_OF_EXTRACTION": {
        "title": "Stage of Groundwater Extraction (SOE)",
        "keywords": [
            "stage of groundwater extraction", "stage of extraction", "soe formula",
            "how is stage of extraction calculated", "formula for stage of extraction",
            "extraction percentage", "extraction rate formula", "stage of extraction definition",
            "what is stage of extraction"
        ],
        "response": (
            "## ⚙️ Stage of Groundwater Extraction (SOE)\n\n"
            "The **Stage of Groundwater Extraction (SOE)** is the primary metric used in India by CGWB to quantify the degree of groundwater utilization and resource sustainability in an assessment unit.\n\n"
            "### 📐 Mathematical Formula\n\n"
            "$$\\text{Stage of Groundwater Extraction (\\%)} = \\left( \\frac{\\text{Existing Gross Groundwater Extraction for All Uses (ham)}}{\\text{Annual Extractable Groundwater Resource (ham)}} \\right) \\times 100$$\n\n"
            "Where:\n"
            "* **Existing Gross Extraction**: Total volume of groundwater drafted annually for **Irrigation**, **Domestic**, and **Industrial** uses (in hectare-meters, `ham`).\n"
            "* **Annual Extractable Groundwater Resource**: Total Annual Recharge minus natural discharge during the non-monsoon season (usually $5\\% - 10\\%$ of annual recharge).\n\n"
            "### 📈 How to Interpret the Value:\n"
            "* **$\\le 70\\%$**: Safe zone (recharge comfortably exceeds extraction).\n"
            "* **$70\\% - 90\\%$**: Semi-critical zone (extraction is approaching recharge capacity).\n"
            "* **$90\\% - 100\\%$**: Critical zone (extraction almost equals annual replenishable recharge).\n"
            "* **$> 100\\%$**: Over-exploited zone (more groundwater is pumped out than nature replenishes, depleting static storage).\n\n"
            "**Source:** CGWB GEC-2015 Methodology"
        )
    },

    "DEPTH_VS_INDICATOR": {
        "title": "Depth to Water Level vs Groundwater Level Indicator",
        "keywords": [
            "difference between depth to water level and groundwater indicator",
            "depth to water level vs groundwater level indicator",
            "what is depth to water level", "what is groundwater level indicator",
            "m bgl vs percent", "m bgl vs percentage", "why is water level in percentage",
            "depth vs indicator", "depth to water table"
        ],
        "response": (
            "## 📏 Depth to Water Level vs Groundwater Level Indicator\n\n"
            "It is very important to distinguish between **Depth to Water Level** and the **Groundwater Level Indicator**, as they represent two distinct metrics:\n\n"
            "### 1. Depth to Water Level (`m bgl`)\n"
            "* **Definition**: The actual physical depth from the ground surface down to the static water table inside a monitoring well or piezometer.\n"
            "* **Unit**: Meters Below Ground Level (**m bgl**).\n"
            "* **Interpretation**: \n"
            "  * A **smaller depth** (e.g., $3.5\\text{ m bgl}$) means groundwater is shallow and near the surface.\n"
            "  * A **larger depth** (e.g., $22.0\\text{ m bgl}$) means the water table is deep underground.\n"
            "* **Data Source**: Measured directly at CGWB and State Groundwater observation wells.\n\n"
            "### 2. Groundwater Level Indicator (`%`)\n"
            "* **Definition**: An application-computed, normalized index ($0-100\\%$) representing the relative groundwater condition across observation networks.\n"
            "* **Unit**: Percentage (**%**).\n"
            "* **Crucial Rule**: The Groundwater Level Indicator is **not** the physical water depth, nor is it the Stage of Groundwater Extraction. It serves as a normalized dashboard metric.\n\n"
            "**Summary**: Physical observations are reported in **m bgl**, while normalized index scores are displayed in **%**."
        )
    },

    "GEC_METHODOLOGY": {
        "title": "GEC-2015 Groundwater Estimation Methodology",
        "keywords": [
            "gec methodology", "gec 2015", "gec-2015", "ground water estimation committee",
            "how is groundwater estimated", "how is recharge calculated", "recharge estimation method",
            "water table fluctuation method", "rainfall infiltration factor method", "wtf method", "rif method"
        ],
        "response": (
            "## 🔬 GEC-2015 Methodology for Groundwater Estimation\n\n"
            "In India, groundwater resource estimation is governed by the **GEC-2015 (Ground Water Resource Estimation Committee)** methodology recommended by the Ministry of Jal Shakti.\n\n"
            "### 1. Annual Recharge Assessment\n"
            "Groundwater recharge is evaluated separately for the **Monsoon Season** and **Non-Monsoon Season**:\n\n"
            "#### A. Monsoon Season Recharge\n"
            "Estimated using two primary methods:\n"
            "1. **Water Table Fluctuation (WTF) Method** (Preferred where sufficient well observations exist):\n"
            "   $$R = S_y \\times \\Delta h \\times A + E_m$$\n"
            "   * $S_y$ = Specific Yield of the aquifer\n"
            "   * $\\Delta h$ = Seasonal water table rise between pre-monsoon and post-monsoon\n"
            "   * $A$ = Geographic area of the assessment unit\n"
            "   * $E_m$ = Gross groundwater extraction during the monsoon period\n"
            "2. **Rainfall Infiltration Factor (RIF) Method** (Used when water level data is inadequate or in specific geological terrains):\n"
            "   $$R_{rf} = f \\times A \\times P$$\n"
            "   * $f$ = Rainfall infiltration factor ($4\\% - 22\\%$ depending on rock/soil type)\n"
            "   * $P$ = Normal monsoon rainfall\n\n"
            "#### B. Non-Monsoon Season Recharge\n"
            "Includes recharge from non-monsoon rainfall (via RIF), canal seepage, return flow from surface & groundwater irrigation, and seepage from tanks and water bodies.\n\n"
            "### 2. Extractable Resource & Extraction\n"
            "* **Annual Extractable Resource**: Total Annual Recharge minus natural baseflow / discharge during the non-monsoon period ($5-10\\%$ allowance).\n"
            "* **Gross Extraction**: Assessed based on tubewell/borewell censuses, power consumption data, and crop water requirement norms for irrigation, domestic, and industrial uses.\n\n"
            "**Source:** Report of the Ground Water Resource Estimation Committee (GEC-2015), CGWB"
        )
    },

    "DYNAMIC_VS_STATIC": {
        "title": "Dynamic vs Static (In-Storage) Groundwater Resources",
        "keywords": [
            "dynamic vs static", "dynamic groundwater", "static groundwater",
            "in-storage groundwater", "difference between dynamic and static groundwater",
            "static vs dynamic water resource"
        ],
        "response": (
            "## 🔄 Dynamic vs Static (In-Storage) Groundwater Resources\n\n"
            "Groundwater in an aquifer system is divided into two distinct components:\n\n"
            "### 1. Dynamic Groundwater Resource (Replenishable)\n"
            "* **What it is**: The volume of groundwater held within the **zone of water table fluctuation** (between the pre-monsoon and post-monsoon water tables).\n"
            "* **Replenishment**: Annually recharged and replenished by monsoon rainfall, river/canal seepage, and surface water bodies.\n"
            "* **Management Principle**: This is the sustainable annual 'budget' that should be utilized for irrigation, domestic, and industrial uses without depleting reserves.\n\n"
            "### 2. Static / In-Storage Groundwater Resource (Reserve)\n"
            "* **What it is**: The permanent groundwater volume stored in the aquifer **below the lowest historical pre-monsoon water table**.\n"
            "* **Replenishment**: Takes decades to centuries to replenish naturally.\n"
            "* **Management Principle**: Serves as emergency buffer during severe droughts. If continuous extraction exceeds dynamic recharge (SOE $> 100\\%$), static storage is mined, leading to irreversible aquifer compaction, land subsidence, and dried borewells.\n\n"
            "**Source:** CGWB National Aquifer Mapping and Management (NAQUIM)"
        )
    },

    "ARTIFICIAL_RECHARGE_STRUCTURES": {
        "title": "Artificial Recharge Structures & Techniques",
        "keywords": [
            "artificial recharge structures", "types of recharge structures", "methods of artificial recharge",
            "how to recharge groundwater", "check dams", "percolation tanks", "recharge shafts",
            "injection wells", "recharge techniques", "rainwater harvesting structures"
        ],
        "response": (
            "## 🏗️ Artificial Recharge Structures & Techniques\n\n"
            "Artificial recharge involves human-engineered structures that augment natural infiltration, directing surface runoff into subterranean aquifers.\n\n"
            "### Top Artificial Recharge Structures Recommended by CGWB:\n\n"
            "1. **Check Dams & Nala Bunds**\n"
            "   * Built across small 1st to 3rd order streams to impound surface runoff, reduce flow velocity, and enhance percolation into shallow unconfined aquifers.\n\n"
            "2. **Percolation Tanks / Ponds**\n"
            "   * Surface water bodies constructed on permeable soils in valleys. They store monsoon runoff specifically designed to allow slow, deep percolation.\n\n"
            "3. **Recharge Shafts & Injection Wells**\n"
            "   * **Recharge Shafts**: Vertical pits ($1-3\\text{ m}$ diameter, $10-30\\text{ m}$ deep) filled with graded boulders, gravel, and sand to penetrate impermeable upper clay layers.\n   * **Injection Wells**: Used for deep confined aquifers to pump or gravity-feed filtered rainwater directly into depleted aquifers.\n\n"
            "4. **Rooftop Rainwater Harvesting (RWH)**\n"
            "   * Collecting clean rainwater from rooftops of residential, commercial, and institutional buildings and channeling it through sand filters into recharge pits or defunct borewells.\n\n"
            "5. **Contour Trenches & Bunding**\n"
            "   * Excavated along hillsides and slopes to break runoff speed, minimize soil erosion, and increase soil moisture absorption.\n\n"
            "6. **Sub-surface Dykes (Groundwater Dams)**\n"
            "   * Underground impermeable barriers constructed across riverbeds to halt sub-surface baseflow, raising the upstream water table.\n\n"
            "**Source:** CGWB Master Plan for Artificial Recharge to Ground Water in India"
        )
    },

    "AGRICULTURAL_CONSERVATION": {
        "title": "Agricultural Groundwater Conservation Practices",
        "keywords": [
            "how can farmers save water", "agricultural conservation", "groundwater conservation in agriculture",
            "how to reduce groundwater extraction for farming", "irrigation water management",
            "crop diversification for water saving", "farming water saving"
        ],
        "response": (
            "## 🌾 Agricultural Groundwater Conservation Practices\n\n"
            "Agriculture accounts for **over $85\\%$** of total groundwater extraction in India. Implementing efficient water practices can save massive volumes of groundwater:\n\n"
            "### 1. Micro-Irrigation Technologies\n"
            "* **Drip Irrigation**: Delivers water directly to crop root zones, reducing evaporation and runoff losses. Saves **$30\\% - 60\\%$** water compared to flood irrigation with **$20\\% - 40\\%$** higher crop yields.\n"
            "* **Sprinkler Systems**: Highly effective for closely spaced crops (pulses, wheat, oilseeds), ensuring uniform application.\n\n"
            "### 2. Crop Diversification\n"
            "* Shift from water-intensive crops (paddy, sugarcane) in water-stressed districts to low-water-demand crops such as **millets (Bajra, Ragi, Jowar)**, pulses, oilseeds, and vegetables.\n\n"
            "### 3. Smart Agronomic Practices\n"
            "* **Laser Land Leveling**: Smooths fields to achieve uniform water spreading, reducing water application by **$20\\% - 25\\%$**.\n"
            "* **Alternate Wetting and Drying (AWD)**: Practiced in paddy cultivation to avoid continuous submergence, cutting water usage by up to **$30\\%$**.\n"
            "* **Mulching & Soil Health**: Applying organic mulch to retain soil moisture and reduce evaporation.\n"
            "* **Direct Seeded Rice (DSR)**: Eliminates nursery puddling and standing water requirements in rice cultivation.\n\n"
            "**Source:** Ministry of Agriculture & CGWB Guidelines"
        )
    },

    "DATA_SOURCES_AND_UNITS": {
        "title": "Units of Measurement and Data Sources",
        "keywords": [
            "what is ham", "what does ham mean", "what is m bgl", "what is mbgl",
            "units of measurement in ingres", "data sources of ingres", "where does ingres data come from",
            "what is hectare meter", "hectare metre"
        ],
        "response": (
            "## 📐 Units of Measurement & Official Data Sources\n\n"
            "### 📏 Units of Measurement Used in INGRES\n\n"
            "| Unit | Full Name | Explanation & Conversion |\n"
            "|:---:|---|---|\n"
            "| **ham** | **Hectare-Meter** | Volume of water required to cover 1 hectare of land ($10,000\\text{ m}^2$) to a depth of 1 meter.<br>• $1\\text{ ham} = 10,000\\text{ m}^3 = 10,000,000\\text{ liters}$ ($10\\text{ million liters}$). |\n"
            "| **m bgl** | **Meters Below Ground Level** | Depth from the ground surface down to the water level inside an observation well or piezometer. |\n"
            "| **mm** | **Millimeters** | Standard depth of precipitation / rainfall recorded over a given area. |\n"
            "| **%** | **Percentage** | Unit for Stage of Groundwater Extraction ($[\\text{Extraction}/\\text{Extractable}] \\times 100$) and normalized indicators. |\n\n"
            "### 🌐 Official Data Sources\n"
            "1. **GWRA National Reports**: Central Ground Water Board (CGWB) & Ministry of Jal Shakti assessment database.\n"
            "2. **Groundwater Observation Network**: CGWB and State Groundwater Department National Hydrograph Monitoring Stations (piezometers and open wells).\n"
            "3. **Rainfall Dataset**: India Meteorological Department (IMD) gridded rainfall data.\n"
            "4. **Live Weather & Forecasts**: Open-Meteo API for real-time temperature, precipitation, and conditions."
        )
    },

    "NET_AVAILABILITY": {
        "title": "Net Groundwater Availability for Future Use",
        "keywords": [
            "what is net groundwater availability", "net groundwater availability",
            "net water availability", "net availability for future use", "how is net availability calculated"
        ],
        "response": (
            "## 💧 Net Groundwater Availability for Future Use\n\n"
            "**Net Groundwater Availability for Future Use** represents the remaining unallocated extractable groundwater volume in an assessment unit that can safely be developed for future economic activities (primarily agriculture/irrigation).\n\n"
            "### 📐 Calculation Formula\n\n"
            "$$\\text{Net Groundwater Availability (ham)} = \\text{Annual Extractable Resource} - \\text{Allocation for Domestic \\& Industrial Requirements for the next 25 years}$$\n\n"
            "### 📌 Significance:\n"
            "* It ensures that adequate groundwater reserves are prioritized and locked for projected human drinking and industrial needs over a 25-year planning horizon.\n"
            "* If Net Groundwater Availability is **zero or negative**, no new commercial or agricultural tubewell permits are issued in that assessment unit.\n\n"
            "**Source:** CGWB Ground Water Resource Assessment Methodology (GEC-2015)"
        )
    }
}


def resolve_domain_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """
    Checks if user query matches any domain knowledge/FAQ topic.
    Returns dictionary with title, response, and topic key if matched; else None.
    """
    q_clean = query.lower().strip()
    q_clean_alpha = re.sub(r'[^\w\s]', '', q_clean).strip()
    
    # 1. First check regex / conversational pleasantries & specific patterns below
    # (Checked in order so specific pleasantries like 'how are you' or 'thank you' take precedence over generic 'hi')

                
    # Check for specific conversational & conceptual questions using regex patterns
    # 0. Common conversational pleasantries
    if re.search(r'\b(how\s+are\s+(you|u)|how\s+r\s+u|how\s+are\s+you\s+doing|how\s+are\s+u\s+doing|how\s+do\s+you\s+do|how(\'s|\s+is)\s+it\s+going|how\s+are\s+things)\b', q_clean):
        return {
            "topic": "HOW_ARE_YOU",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["HOW_ARE_YOU"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["HOW_ARE_YOU"]["response"],
            "sources": ["IN-GRES Assistant"]
        }

    if re.search(r'\b(thank\s+(you|u)|thanks|thx|tq|much\s+appreciated)\b', q_clean):
        return {
            "topic": "THANK_YOU",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["THANK_YOU"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["THANK_YOU"]["response"],
            "sources": ["IN-GRES Assistant"]
        }

    if re.match(r'^(bye+|goodbye+|see\s+you|cya|good\s+night|talk\s+to\s+you\s+later)(\s+.*)?$', q_clean):
        return {
            "topic": "GOODBYE",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["GOODBYE"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["GOODBYE"]["response"],
            "sources": ["IN-GRES Assistant"]
        }

    if re.search(r'\b(who\s+are\s+you|what\s+are\s+you|who\s+made\s+you|introduce\s+yourself|tell\s+me\s+about\s+yourself|who\s+built\s+you)\b', q_clean):
        return {
            "topic": "WHO_ARE_YOU",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["WHO_ARE_YOU"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["WHO_ARE_YOU"]["response"],
            "sources": ["Central Ground Water Board (CGWB)", "IN-GRES"]
        }

    if re.match(r'^(h+i+|h+e+y+|hello+|namaste|vanakkam|hola|greetings|good\s+(morning|afternoon|evening|day)|sup|yo|what\'?s\s+up)(\s+.*)?$', q_clean):
        return {
            "topic": "GREETING_HELLO",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["GREETING_HELLO"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["GREETING_HELLO"]["response"],
            "sources": ["IN-GRES Assistant Guide"]
        }

    # 1. What is INGRES?
    if re.search(r'\b(what\s+is|about|explain|tell\s+me\s+about)\s+(ingres|in-gres|in\s+gres)\b', q_clean):
        return {
            "topic": "WHAT_IS_INGRES",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["WHAT_IS_INGRES"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["WHAT_IS_INGRES"]["response"],
            "sources": ["Central Ground Water Board (CGWB)", "Ministry of Jal Shakti", "IN-GRES"]
        }
        
    # 2. How to use chatbot / guide
    if re.search(r'\b(how\s+to\s+use|user\s+guide|chatbot\s+guide|how\s+do\s+i\s+use|how\s+can\s+i\s+use)\b', q_clean):
        return {
            "topic": "HOW_TO_USE_CHATBOT",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["HOW_TO_USE_CHATBOT"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["HOW_TO_USE_CHATBOT"]["response"],
            "sources": ["IN-GRES Assistant Guide"]
        }

    # 3. Stage of extraction formula / definition
    if re.search(r'\b(stage\s+of\s+(ground\s*water\s+)?extraction|soe\s+formula|formula\s+for\s+stage)\b', q_clean):
        return {
            "topic": "STAGE_OF_EXTRACTION",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["STAGE_OF_EXTRACTION"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["STAGE_OF_EXTRACTION"]["response"],
            "sources": ["CGWB GEC-2015 Methodology"]
        }

    # 4. GEC methodology
    if re.search(r'\b(gec\s+methodology|gec\s*2015|how\s+is\s+ground\s*water\s+estimated|estimation\s+methodology)\b', q_clean):
        return {
            "topic": "GEC_METHODOLOGY",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["GEC_METHODOLOGY"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["GEC_METHODOLOGY"]["response"],
            "sources": ["Report of GEC-2015, CGWB"]
        }

    # 5. Assessment categories criteria
    if re.search(r'\b(assessment\s+categories|categories\s+mean|category\s+mean|what\s+is\s+(the\s+)?(safe|semi[\s-]critical|critical|over[\s-]exploited|saline)\s+category|what\s+do(es)?\s+(safe|semi[\s-]critical|critical|over[\s-]exploited).*mean|categorization\s+criteria|safe\s+semi[\s-]critical)\b', q_clean):
        return {
            "topic": "GWRA_CATEGORIES",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["GWRA_CATEGORIES"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["GWRA_CATEGORIES"]["response"],
            "sources": ["CGWB GWRA Guidelines"]
        }

    # 6. Depth vs Indicator
    if re.search(r'\b(depth\s+to\s+water\s+level\s+vs|m\s*bgl\s+vs|water\s+level\s+indicator\s+vs|difference\s+between\s+depth\s+and\s+(groundwater\s+)?indicator)\b', q_clean):
        return {
            "topic": "DEPTH_VS_INDICATOR",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["DEPTH_VS_INDICATOR"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["DEPTH_VS_INDICATOR"]["response"],
            "sources": ["CGWB & IN-GRES Metadata Standards"]
        }

    # 7. Units (what is ham / m bgl)
    if re.search(r'\b(what\s+is\s+ham|what\s+does\s+ham\s+mean|what\s+is\s+m\s*bgl|units\s+of\s+measurement|data\s+sources)\b', q_clean):
        return {
            "topic": "DATA_SOURCES_AND_UNITS",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["DATA_SOURCES_AND_UNITS"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["DATA_SOURCES_AND_UNITS"]["response"],
            "sources": ["CGWB & IN-GRES Standards"]
        }

    # 8. Artificial recharge structures
    if re.search(r'\b(artificial\s+recharge\s+structures|methods\s+of\s+artificial\s+recharge|recharge\s+structures|types\s+of\s+recharge|how\s+to\s+recharge\s+groundwater)\b', q_clean):
        return {
            "topic": "ARTIFICIAL_RECHARGE_STRUCTURES",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["ARTIFICIAL_RECHARGE_STRUCTURES"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["ARTIFICIAL_RECHARGE_STRUCTURES"]["response"],
            "sources": ["CGWB Master Plan for Artificial Recharge"]
        }

    # 9. Dynamic vs Static Groundwater
    if re.search(r'\b(dynamic\s+vs\s+static|dynamic\s+groundwater|static\s+groundwater|in-storage\s+groundwater|difference\s+between\s+dynamic\s+and\s+static)\b', q_clean):
        return {
            "topic": "DYNAMIC_VS_STATIC",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["DYNAMIC_VS_STATIC"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["DYNAMIC_VS_STATIC"]["response"],
            "sources": ["CGWB NAQUIM Guidelines"]
        }

    # 10. Agricultural conservation
    if re.search(r'\b(how\s+can\s+farmers\s+save|agricultural\s+(groundwater\s+)?conservation|save\s+water\s+in\s+agriculture|farming\s+water\s+saving|reduce\s+water\s+in\s+farming|farmers\s+save\s+water)\b', q_clean):
        return {
            "topic": "AGRICULTURAL_CONSERVATION",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["AGRICULTURAL_CONSERVATION"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["AGRICULTURAL_CONSERVATION"]["response"],
            "sources": ["Ministry of Agriculture & CGWB Guidelines"]
        }

    # 11. Net groundwater availability
    if re.search(r'\b(net\s+(ground\s*water\s+)?availability|net\s+availability\s+for\s+future\s+use|net\s+water\s+availability)\b', q_clean):
        return {
            "topic": "NET_AVAILABILITY",
            "title": DOMAIN_KNOWLEDGE_ENTRIES["NET_AVAILABILITY"]["title"],
            "response": DOMAIN_KNOWLEDGE_ENTRIES["NET_AVAILABILITY"]["response"],
            "sources": ["CGWB GEC-2015 Methodology"]
        }

    # 12. Fallback: check exact keywords or full phrases with word boundaries
    for topic_key, entry in DOMAIN_KNOWLEDGE_ENTRIES.items():
        for kw in entry["keywords"]:
            kw_clean = re.sub(r'[^\w\s]', '', kw).strip().lower()
            if not kw_clean:
                continue
            # For single words, enforce exact whole word or whole query match
            if ' ' not in kw_clean:
                if q_clean_alpha == kw_clean or re.search(r'\b' + re.escape(kw_clean) + r'\b', q_clean_alpha):
                    # If it's a very short greeting/slang (e.g. 'yo', 'hi'), only match if query is very short (<= 3 words)
                    if len(q_clean_alpha.split()) <= 3 or topic_key not in {"GREETING_HELLO", "GOODBYE"}:
                        return {
                            "topic": topic_key,
                            "title": entry["title"],
                            "response": entry["response"],
                            "sources": ["Central Ground Water Board (CGWB)", "Ministry of Jal Shakti", "IN-GRES"]
                        }
            else:
                # Multi-word phrase matching
                if kw_clean in q_clean_alpha:
                    return {
                        "topic": topic_key,
                        "title": entry["title"],
                        "response": entry["response"],
                        "sources": ["Central Ground Water Board (CGWB)", "Ministry of Jal Shakti", "IN-GRES"]
                    }

    return None

