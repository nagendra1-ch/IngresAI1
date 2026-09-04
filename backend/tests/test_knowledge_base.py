import pytest
from app.services.knowledge_base import resolve_domain_knowledge, DOMAIN_KNOWLEDGE_ENTRIES

def test_resolve_what_is_ingres():
    res = resolve_domain_knowledge("What is INGRES?")
    assert res is not None
    assert res["topic"] == "WHAT_IS_INGRES"
    assert "India-Groundwater Resource Estimation System" in res["response"]
    assert "Central Ground Water Board (CGWB)" in res["response"]

def test_resolve_how_to_use_chatbot():
    res = resolve_domain_knowledge("How to use chatbot properly?")
    assert res is not None
    assert res["topic"] == "HOW_TO_USE_CHATBOT"
    assert "How to Use the IN-GRES AI Chatbot Properly" in res["response"]
    assert "Kadapa" in res["response"]

def test_resolve_gwra_categories():
    res = resolve_domain_knowledge("What do Safe, Semi-Critical, and Over-Exploited mean?")
    assert res is not None
    assert res["topic"] == "GWRA_CATEGORIES"
    assert "Stage of Groundwater Extraction (SOE %)" in res["response"]
    assert "Safe" in res["response"]
    assert "Over-Exploited" in res["response"]

def test_resolve_stage_of_extraction_formula():
    res = resolve_domain_knowledge("What is the formula for stage of extraction?")
    assert res is not None
    assert res["topic"] == "STAGE_OF_EXTRACTION"
    assert "Stage of Groundwater Extraction" in res["response"]
    assert "Existing Gross Groundwater Extraction" in res["response"]

def test_resolve_artificial_recharge_structures():
    res = resolve_domain_knowledge("What are artificial recharge structures?")
    assert res is not None
    assert res["topic"] == "ARTIFICIAL_RECHARGE_STRUCTURES"
    assert "Check Dams & Nala Bunds" in res["response"]
    assert "Percolation Tanks" in res["response"]

def test_resolve_gec_methodology():
    res = resolve_domain_knowledge("What is GEC methodology?")
    assert res is not None
    assert res["topic"] == "GEC_METHODOLOGY"
    assert "GEC-2015" in res["response"]
    assert "Water Table Fluctuation" in res["response"]

def test_resolve_units_of_measurement():
    res = resolve_domain_knowledge("What is ham?")
    assert res is not None
    assert res["topic"] == "DATA_SOURCES_AND_UNITS"
    assert "Hectare-Meter" in res["response"]

def test_resolve_depth_vs_indicator():
    res = resolve_domain_knowledge("What is the difference between depth to water level and groundwater indicator?")
    assert res is not None
    assert res["topic"] == "DEPTH_VS_INDICATOR"
    assert "m bgl" in res["response"]
    assert "Groundwater Level Indicator" in res["response"]

def test_resolve_dynamic_vs_static():
    res = resolve_domain_knowledge("Difference between dynamic and static groundwater")
    assert res is not None
    assert res["topic"] == "DYNAMIC_VS_STATIC"
    assert "Dynamic Groundwater Resource" in res["response"]
    assert "Static / In-Storage" in res["response"]

def test_resolve_agricultural_conservation():
    res = resolve_domain_knowledge("How can farmers save water?")
    assert res is not None
    assert res["topic"] == "AGRICULTURAL_CONSERVATION"
    assert "Micro-Irrigation" in res["response"]
    assert "Crop Diversification" in res["response"]

def test_resolve_net_availability():
    res = resolve_domain_knowledge("What is net groundwater availability?")
    assert res is not None
    assert res["topic"] == "NET_AVAILABILITY"
    assert "Net Groundwater Availability" in res["response"]

def test_resolve_conversational_pleasantries():
    res_hi = resolve_domain_knowledge("hi")
    assert res_hi is not None
    assert res_hi["topic"] == "GREETING_HELLO"

    res_how = resolve_domain_knowledge("how are you")
    assert res_how is not None
    assert res_how["topic"] == "HOW_ARE_YOU"

    res_thx = resolve_domain_knowledge("thank you so much")
    assert res_thx is not None
    assert res_thx["topic"] == "THANK_YOU"

    res_bye = resolve_domain_knowledge("goodbye")
    assert res_bye is not None
    assert res_bye["topic"] == "GOODBYE"

def test_resolve_non_domain_query_returns_none():
    res = resolve_domain_knowledge("What is the groundwater level in Kadapa?")
    # This is a specific location query, not a pure domain knowledge/FAQ query
    assert res is None
