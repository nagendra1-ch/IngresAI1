/**
 * Formats rainfall data dynamically based on period metadata.
 * Conforms to:
 * - Case 1 (Monthly): Rainfall: X.X mm, Period: Monthly, Year
 * - Case 2 (Annual): Annual Rainfall: X.X mm, Period: Year
 * - Case 3 (Unknown): Rainfall: X.X mm, Period: Year
 */
export const getRainfallDisplay = (rainfall) => {
  if (!rainfall) {
    return {
      label: "Rainfall",
      value: "N/A",
      period: "N/A"
    };
  }

  // Handle both nested and flat API fields
  const valRaw = rainfall.value_mm !== undefined ? rainfall.value_mm : (rainfall.rainfall_mm !== undefined ? rainfall.rainfall_mm : null);
  const year = rainfall.year !== undefined ? rainfall.year : (rainfall.rainfall_year !== undefined ? rainfall.rainfall_year : "N/A");
  const periodType = rainfall.period_type !== undefined ? rainfall.period_type : (rainfall.rainfall_period_type !== undefined ? rainfall.rainfall_period_type : "unknown");

  if (valRaw === null || valRaw === undefined) {
    return {
      label: "Rainfall",
      value: "N/A",
      period: "N/A"
    };
  }

  const value = `${valRaw.toFixed(1)} mm`;
  const type = (periodType || "unknown").toLowerCase().trim();

  if (type === "annual") {
    return {
      label: "Annual Rainfall",
      value: value,
      period: `${year}`
    };
  } else if (type === "monthly") {
    return {
      label: "Rainfall",
      value: value,
      period: `Monthly, ${year}`
    };
  } else {
    return {
      label: "Rainfall",
      value: value,
      period: `${year}`
    };
  }
};
