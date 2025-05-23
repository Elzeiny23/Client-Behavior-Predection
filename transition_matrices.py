import numpy as np

# Define transition matrices for different business scenarios
SCENARIOS = {
    "Default": np.array([
        [0.30, 0.40, 0.10, 0.15, 0.05],  # Immediate Repurchase
        [0.20, 0.50, 0.15, 0.10, 0.05],  # Loyal Customer
        [0.05, 0.20, 0.40, 0.25, 0.10],  # Occasional Buyer
        [0.10, 0.10, 0.20, 0.50, 0.10],  # Discount Buyer
        [0.01, 0.01, 0.01, 0.01, 0.96]   # No Repurchase (absorbing state)
    ]),
    
    "Economic Recession": np.array([
        [0.20, 0.30, 0.15, 0.25, 0.10],
        [0.15, 0.35, 0.20, 0.20, 0.10],
        [0.05, 0.15, 0.30, 0.35, 0.15],
        [0.05, 0.05, 0.15, 0.65, 0.10],
        [0.01, 0.01, 0.01, 0.01, 0.96]
    ]),
    
    "Strong Marketing Campaign": np.array([
        [0.40, 0.45, 0.05, 0.05, 0.05],
        [0.30, 0.50, 0.10, 0.05, 0.05],
        [0.10, 0.30, 0.40, 0.15, 0.05],
        [0.05, 0.20, 0.20, 0.45, 0.10],
        [0.01, 0.01, 0.01, 0.01, 0.96]
    ]),
    
    "New Competitor": np.array([
        [0.25, 0.30, 0.20, 0.15, 0.10],
        [0.15, 0.40, 0.25, 0.10, 0.10],
        [0.05, 0.20, 0.35, 0.30, 0.10],
        [0.05, 0.10, 0.20, 0.55, 0.10],
        [0.01, 0.01, 0.01, 0.01, 0.96]
    ]),
    
    "Price Increase": np.array([
        [0.20, 0.30, 0.15, 0.25, 0.10],
        [0.10, 0.35, 0.20, 0.20, 0.15],
        [0.05, 0.15, 0.30, 0.40, 0.10],
        [0.05, 0.05, 0.15, 0.55, 0.20],
        [0.01, 0.01, 0.01, 0.01, 0.96]
    ])
}

# Customer states/segments
STATES = ["Immediate Repurchase", "Loyal Customer", "Occasional Buyer", 
          "Discount Buyer", "No Repurchase"]

# State abbreviations for display
STATE_ABBR = ["Immediate Repurchase", "Loyal Customer", "Occasional Buyer", "Discount Buyer", "No Repurchase"]

# New customer distribution (how new customers are distributed across segments)
# Based on KPMG's Retail Customer Acquisition Study mentioned in the document
NEW_CUSTOMER_DISTRIBUTION = np.array([0.20, 0.25, 0.30, 0.25, 0.0])

def get_transition_matrix(scenario: str) -> np.ndarray:
    """Get the transition matrix for a specific scenario"""
    if scenario in SCENARIOS:
        return SCENARIOS[scenario]
    else:
        raise ValueError(f"Unknown scenario: {scenario}. Available scenarios: {list(SCENARIOS.keys())}")

def get_steady_state(transition_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate the steady state distribution for the transition matrix.
    This only considers the non-absorbing states.
    
    Args:
        transition_matrix: The Markov chain transition matrix
        
    Returns:
        Array of steady state probabilities for the non-absorbing states
    """
    # Extract the sub-matrix for non-absorbing states
    sub_matrix = transition_matrix[:4, :4]
    
    # Find eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(sub_matrix.T)
    
    # Find the eigenvector corresponding to eigenvalue 1
    # (or the closest to 1 due to numerical precision)
    idx = np.argmin(np.abs(eigenvalues - 1))
    steady_state = np.real(eigenvectors[:, idx])
    
    # Normalize to make the sum 1
    steady_state = steady_state / np.sum(steady_state)
    
    return steady_state