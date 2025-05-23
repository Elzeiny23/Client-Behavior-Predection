import numpy as np
from typing import Dict, List, Union, Any

# Average monthly revenue per customer segment
MONTHLY_REVENUE = {
    "Immediate Repurchase": 1120 / 12, 
    "Loyal Customer": (165 * 6.5) / 12,  # $165 per purchase, avg 6.5 purchases per year (52 weeks ÷ 8 weeks)
    "Occasional Buyer": 190 * 3.5 / 12,  # $190 per purchase, avg 3.5 purchases per year (middle of 3-4 range)
    "Discount Buyer": 95 * 5 / 12,  # $95 per purchase, avg 5 purchases per year (middle of 4-6 range)
    "No Repurchase": 0
}

def calculate_revenue(customer_counts: np.ndarray, states: List[str]) -> float:
    """
    Calculate monthly revenue based on customer counts and average spend.
    
    Args:
        customer_counts: Array of customer counts by segment
        states: List of state names corresponding to customer_counts
        
    Returns:
        Total monthly revenue
    """
    revenue = sum(count * MONTHLY_REVENUE[state] 
                  for count, state in zip(customer_counts, states))
    return revenue