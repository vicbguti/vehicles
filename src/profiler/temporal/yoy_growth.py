from typing import Dict, Any, List

def calculate_yoy_growth(counts: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Calculates year-over-year (YoY) growth rates from a dictionary of year -> count.
    """
    sorted_years = sorted(list(counts.keys()))
    yoy_metrics = []
    
    for i in range(1, len(sorted_years)):
        prev_year = sorted_years[i-1]
        curr_year = sorted_years[i]
        
        prev_count = counts[prev_year]
        curr_count = counts[curr_year]
        
        difference = curr_count - prev_count
        growth_rate = (difference / prev_count) * 100 if prev_count > 0 else 0.0
        
        yoy_metrics.append({
            "from_year": prev_year,
            "to_year": curr_year,
            "previous_count": prev_count,
            "current_count": curr_count,
            "absolute_change": difference,
            "growth_rate_percentage": round(growth_rate, 4)
        })
        
    return yoy_metrics
