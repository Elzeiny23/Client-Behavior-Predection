import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

from transition_matrices import STATES, STATE_ABBR, NEW_CUSTOMER_DISTRIBUTION, get_transition_matrix, get_steady_state
from revenue_model import calculate_revenue

class CustomerMarkovModel:
    """
    A class to model customer behavior using Discrete-Time Markov Chains (DTMC).
    """
    
    def __init__(self, 
                 initial_customers: int = 10000,
                 new_customers_per_month: int = 800,
                 scenario: str = "Default"):
        """
        Initialize the Markov model with customer data and scenario.
        
        Args:
            initial_customers: Total number of customers at start
            new_customers_per_month: Number of new customers added each month
            scenario: Which business scenario to use
        """
        self.initial_customers = initial_customers
        self.new_customers_per_month = new_customers_per_month
        self.scenario = scenario
        
        # Set transition matrix based on scenario
        self.transition_matrix = get_transition_matrix(scenario)
        
        # Calculate steady state distribution (excluding No Repurchase)
        self.steady_state = get_steady_state(self.transition_matrix)
        
        # Initial distribution with 25% in each active segment
        self.initial_distribution = np.array([0.25, 0.25, 0.25, 0.25, 0.0])
        
        # New customer distribution
        self.new_customer_distribution = NEW_CUSTOMER_DISTRIBUTION
    
    def simulate(self, months: int = 12) -> pd.DataFrame:
        """
        Simulate customer behavior over specified months.
        
        Args:
            months: Number of months to simulate
            
        Returns:
            DataFrame with customer counts, revenue, and churn metrics for each month
        """
        # Initialize results storage
        results = []
        
        # Initial customer distribution
        customer_counts = self.initial_distribution * self.initial_customers
        customer_counts = customer_counts.astype(int)
        
        # Total customers at start
        total_customers = np.sum(customer_counts)
        
        # Calculate initial monthly revenue
        monthly_revenue = calculate_revenue(customer_counts, STATES)
        
        # Store initial state
        results.append({
            'Month': 0,
            'Total Customers': total_customers,
            'Monthly Revenue': monthly_revenue,
            'Churn Rate': 0.0,
            **{state: count for state, count in zip(STATES, customer_counts)},
            **{f'{abbr}': count for abbr, count in zip(STATE_ABBR, customer_counts)}
        })
        
        # Run simulation for specified months
        for month in range(1, months + 1):
            # Apply transition matrix to current distribution
            new_counts = np.zeros_like(customer_counts, dtype=float)  # Use float for calculations
            
            for i in range(len(STATES)):
                for j in range(len(STATES)):
                    new_counts[j] += customer_counts[i] * self.transition_matrix[i, j]
            
            # Add new customers
            new_customers = self.new_customers_per_month * self.new_customer_distribution
            new_counts += new_customers
            
            # Convert to integers AFTER all calculations are done/Rounded to nearest customer
            customer_counts = np.round(new_counts).astype(int)
            
            # Total customers now
            total_customers = np.sum(customer_counts)
            
            # Calculate monthly revenue
            monthly_revenue = calculate_revenue(customer_counts, STATES)
            
            # Calculate customers who moved to NR this month (true monthly churn)
            previous_nr = results[-1]["No Repurchase"]
            new_nr_customers = customer_counts[4] - previous_nr
            active_customers_before = sum(results[-1][STATE_ABBR[i]] for i in range(4))
            churn_rate = (new_nr_customers / active_customers_before * 100 
                         if active_customers_before > 0 else 0)
            
            # Store results
            results.append({
                'Month': month,
                'Total Customers': total_customers,
                'Monthly Revenue': monthly_revenue,
                'Churn Rate': churn_rate,
                **{state: count for state, count in zip(STATES, customer_counts)},
                **{f'{abbr}': count for abbr, count in zip(STATE_ABBR, customer_counts)}
            })
        
        return pd.DataFrame(results)