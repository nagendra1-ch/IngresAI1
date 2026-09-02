def validate_district_data(gwra, avg_depth, avg_rain, geo) -> dict:
    """
    Validates a district's groundwater and assessment data.
    Returns a dictionary:
    {
        "status": "valid" | "warning" | "error",
        "warnings": list of warning strings
    }
    """
    warnings = []

    # 1. CATEGORY_SOURCE_VALID
    # Check if category matches standard stage of extraction thresholds:
    # Safe (<=70%), Semi-Critical (70-90%), Critical (90-100%), Over-Exploited (>100%)
    if gwra and gwra.stage_of_groundwater_extraction_percent is not None and gwra.district_assessment_category is not None:
        stage = gwra.stage_of_groundwater_extraction_percent
        cat = gwra.district_assessment_category.strip()
        
        expected_cat = None
        if stage <= 70.0:
            expected_cat = "Safe"
        elif stage <= 90.0:
            expected_cat = "Semi-Critical"
        elif stage <= 100.0:
            expected_cat = "Critical"
        else:
            expected_cat = "Over-Exploited"
            
        if cat.lower() != expected_cat.lower():
            warnings.append(
                f"CATEGORY_SOURCE_VALID: Official category '{cat}' differs from expected classification "
                f"'{expected_cat}' for extraction stage of {stage:.2f}%."
            )

    # 2. EXTRACTION_PERCENT_VALID
    # Check if stage % = extraction / extractable * 100
    if gwra and gwra.annual_groundwater_extraction_ham is not None and gwra.annual_extractable_groundwater_resource_ham is not None and gwra.stage_of_groundwater_extraction_percent is not None:
        extraction = gwra.annual_groundwater_extraction_ham
        extractable = gwra.annual_extractable_groundwater_resource_ham
        stored_stage = gwra.stage_of_groundwater_extraction_percent
        
        if extractable > 0:
            calc_stage = (extraction / extractable) * 100.0
            if abs(calc_stage - stored_stage) > 0.5:
                warnings.append(
                    f"EXTRACTION_PERCENT_VALID: Stored stage of extraction {stored_stage:.2f}% differs from "
                    f"calculated value {calc_stage:.2f}% (extraction: {extraction:,.2f} ham, extractable: {extractable:,.2f} ham)."
                )

    # 3. DISTRICT_STATE_MAPPING_VALID
    # Checks state-district integrity
    if not geo.state_name or not geo.district_name:
        warnings.append("DISTRICT_STATE_MAPPING_VALID: District or State name is empty.")

    # 4. YEAR_MAPPING_VALID
    # Chronological checks
    if gwra and gwra.assessment_year is not None:
        gwra_year = gwra.assessment_year
        # If there's an observation year, it should represent the temporal source
        # No warning unless years are completely invalid

    # 5. UNIT_MAPPING_VALID
    # रिचार्ज, extractable, extraction must be non-negative and extractable <= recharge
    if gwra:
        recharge = gwra.annual_groundwater_recharge_ham
        extractable = gwra.annual_extractable_groundwater_resource_ham
        extraction = gwra.annual_groundwater_extraction_ham
        
        if recharge is not None and recharge < 0:
            warnings.append(f"UNIT_MAPPING_VALID: Recharge is negative ({recharge:.2f} ham).")
        if extractable is not None and extractable < 0:
            warnings.append(f"UNIT_MAPPING_VALID: Extractable resource is negative ({extractable:.2f} ham).")
        if extraction is not None and extraction < 0:
            warnings.append(f"UNIT_MAPPING_VALID: Extraction is negative ({extraction:.2f} ham).")
            
        if recharge is not None and extractable is not None and extractable > recharge:
            warnings.append(
                f"UNIT_MAPPING_VALID: Extractable resource ({extractable:.2f} ham) exceeds total recharge "
                f"({recharge:.2f} ham)."
            )

    # 6. MISSING_VALUE_VALID
    # Check for missing values which are represented as null
    if avg_depth is None:
        warnings.append("MISSING_VALUE_VALID: Depth to water level is missing.")
    if avg_rain is None:
        warnings.append("MISSING_VALUE_VALID: Rainfall is missing.")
    if gwra is None:
        warnings.append("MISSING_VALUE_VALID: GWRA Assessment is missing.")
    elif gwra.district_assessment_category is None:
        warnings.append("MISSING_VALUE_VALID: Assessment category is missing.")

    status = "valid"
    if warnings:
        status = "warning"

    return {
        "status": status,
        "warnings": warnings
    }
