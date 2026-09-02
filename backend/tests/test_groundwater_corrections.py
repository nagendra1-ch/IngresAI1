import unittest
import sqlite3
import os
from app.utils.calculations import calculate_stage_of_extraction
from app.utils.validation import validate_district_data
from app.models import Geography, GWRAAssessment
from app.database import SessionLocal

class TestGroundwaterCorrections(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.db_path = r"c:\Users\chnag\OneDrive\Attachments\Desktop\ingres1\ingres_ai.db"
        cls.db_exists = os.path.exists(cls.db_path)

    def test_calculate_stage_of_extraction_formula(self):
        # stage (%) = extraction / extractable * 100
        # Check calculation with normal parameters
        stage = calculate_stage_of_extraction(100.0, 45.0)
        self.assertEqual(stage, 45.0)
        
        # Check calculation with 0 extractable resource (prevent division by zero)
        stage_zero = calculate_stage_of_extraction(0.0, 50.0)
        self.assertEqual(stage_zero, 0.0)
        
        # Check None values return None
        self.assertIsNone(calculate_stage_of_extraction(None, 45.0))
        self.assertIsNone(calculate_stage_of_extraction(100.0, None))

    def test_validation_layer_warnings(self):
        # Create a mock geography
        class MockGeography:
            def __init__(self):
                self.state_name = "Rajasthan"
                self.district_name = "Ajmer"

        # Create a mock GWRA assessment with an anomalous classification
        # stage = 138.14%, category = Safe (Ajmer anomaly)
        class MockGWRA:
            def __init__(self):
                self.stage_of_groundwater_extraction_percent = 138.14
                self.district_assessment_category = "Safe"
                self.annual_groundwater_extraction_ham = 46389.72
                self.annual_extractable_groundwater_resource_ham = 33580.91
                self.annual_groundwater_recharge_ham = 37312.12
                self.assessment_year = 2025

        geo = MockGeography()
        gwra = MockGWRA()
        
        dq = validate_district_data(gwra, avg_depth=None, avg_rain=None, geo=geo)
        
        self.assertEqual(dq["status"], "warning")
        self.assertTrue(any("CATEGORY_SOURCE_VALID" in w for w in dq["warnings"]))
        self.assertTrue(any("MISSING_VALUE_VALID" in w for w in dq["warnings"]))

    def test_database_target_records_integrity(self):
        if not self.db_exists:
            self.skipTest("Database ingres_ai.db not found, skipping integration checks.")
            
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 1. Ajmer check
        cur.execute("""
            SELECT g.district_name, a.district_assessment_category, a.stage_of_groundwater_extraction_percent
            FROM geographies g
            JOIN gwra_assessments a ON g.id = a.geography_id
            WHERE g.normalized_district_name = 'AJMER' AND g.normalized_mandal_name IS NULL
        """)
        row = cur.fetchone()
        self.assertIsNotNone(row)
        dist, cat, stage = row
        self.assertEqual(cat, "Safe")
        self.assertAlmostEqual(stage, 138.14, places=1)
        
        # 2. Ahmedabad check
        cur.execute("""
            SELECT g.district_name, a.district_assessment_category, a.stage_of_groundwater_extraction_percent
            FROM geographies g
            JOIN gwra_assessments a ON g.id = a.geography_id
            WHERE g.normalized_district_name = 'AHMEDABAD' AND g.normalized_mandal_name IS NULL
        """)
        row = cur.fetchone()
        self.assertIsNotNone(row)
        dist, cat, stage = row
        self.assertEqual(cat, "Over-Exploited")
        self.assertAlmostEqual(stage, 72.74, places=1)

        # 3. UP Ananthapuramu check (must be 0, mapped to Hapur)
        cur.execute("""
            SELECT id FROM geographies 
            WHERE normalized_district_name = 'ANANTHAPURAMU' AND normalized_state_name = 'UTTAR PRADESH'
        """)
        self.assertEqual(len(cur.fetchall()), 0)
        
        # 4. Hapur check (UP Hapur must exist and contain the assessment)
        cur.execute("""
            SELECT g.district_name, a.district_assessment_category, a.stage_of_groundwater_extraction_percent
            FROM geographies g
            JOIN gwra_assessments a ON g.id = a.geography_id
            WHERE g.normalized_district_name = 'HAPUR' AND g.normalized_mandal_name IS NULL
        """)
        row = cur.fetchone()
        self.assertIsNotNone(row)
        dist, cat, stage = row
        self.assertEqual(cat, "Critical")
        self.assertAlmostEqual(stage, 93.93, places=1)
        
        conn.close()

    def test_district_fallbacks_integration(self):
        if not self.db_exists:
            self.skipTest("Database ingres_ai.db not found, skipping integration checks.")
        
        db = SessionLocal()
        try:
            from app.routes.districts import search_districts
            results = search_districts(query="Ajmer", state=None, db=db, current_user=None)
            self.assertTrue(len(results) >= 1)
            ajmer = results[0]
            self.assertEqual(ajmer["district_name"], "Ajmer")
            self.assertIsNotNone(ajmer["depth_to_water_level_m_bgl"])
            self.assertIsNotNone(ajmer["rainfall_mm"])
            self.assertIsNotNone(ajmer["stage_of_groundwater_extraction_percent"])
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
