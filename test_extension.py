import pandas as pd
import numpy as np
from simulation import CustomerMarkovModel
from transition_matrices import SCENARIOS, STATES, STATE_ABBR
import json

# This is a minimal script to test the extension functionality 
# before integrating it into the Flask app

def test_extension():
    """Test the extension functionality independently of Flask"""
    print("Testing extension functionality...")
    
    # 1. Run initial simulation
    print("\nStep 1: Running initial simulation with Default scenario")
    initial_customers = 10000
    new_customers_per_month = 800
    months = 12
    scenario = "Default"
    
    model = CustomerMarkovModel(
        initial_customers=initial_customers,
        new_customers_per_month=new_customers_per_month,
        scenario=scenario
    )
    
    results = model.simulate(months=months)
    
    # Print summary of initial simulation
    print(f"Initial simulation complete:")
    print(f"  Initial customers: {results.iloc[0]['Total Customers']}")
    print(f"  Final customers: {results.iloc[-1]['Total Customers']}")
    print(f"  Initial revenue: ${results.iloc[0]['Monthly Revenue']:.2f}")
    print(f"  Final revenue: ${results.iloc[-1]['Monthly Revenue']:.2f}")
    
    # 2. Extract last state for extension
    print("\nStep 2: Extracting final state for extension")
    last_result = results.iloc[-1]
    last_month = last_result["Month"]
    
    # Extract customer counts for each segment
    customer_counts = []
    for state in STATES:
        count = last_result[state]
        customer_counts.append(count)
        print(f"  {state}: {count:.1f}")
    
    # 3. Set up extension
    print("\nStep 3: Setting up extension with New Competitor scenario")
    extension_months = 3
    extension_scenario = "New Competitor"
    
    # Create new model for extension
    extension_model = CustomerMarkovModel(
        initial_customers=1,  # Will be overridden
        new_customers_per_month=new_customers_per_month,
        scenario=extension_scenario
    )
    
    # Set initial distribution manually
    total_customers = sum(customer_counts)
    if total_customers > 0:
        initial_distribution = [count / total_customers for count in customer_counts]
        print(f"  Setting initial distribution: {[f'{d:.4f}' for d in initial_distribution]}")
        extension_model.initial_distribution = initial_distribution
    
    # 4. Run extension simulation
    print("\nStep 4: Running extension simulation")
    extension_results = extension_model.simulate(months=extension_months+1)  # +1 for offset
    
    # Adjust month numbers
    for i in range(len(extension_results)):
        extension_results.at[i, 'Month'] = last_month + i
    
    # Remove first row to avoid duplication
    extension_results = extension_results.iloc[1:]
    
    # Print summary of extension
    print(f"Extension simulation complete:")
    print(f"  Extended for {extension_months} months with {extension_scenario} scenario")
    print(f"  Initial customers: {extension_results.iloc[0]['Total Customers']}")
    print(f"  Final customers: {extension_results.iloc[-1]['Total Customers']}")
    print(f"  Initial revenue: ${extension_results.iloc[0]['Monthly Revenue']:.2f}")
    print(f"  Final revenue: ${extension_results.iloc[-1]['Monthly Revenue']:.2f}")
    
    # 5. Combine results
    print("\nStep 5: Combining results")
    combined_results = pd.concat([results, extension_results])
    
    print(f"Combined simulation has {len(combined_results)} data points from Month 0 to Month {combined_results.iloc[-1]['Month']}")
    print(f"  Final customers: {combined_results.iloc[-1]['Total Customers']}")
    print(f"  Final revenue: ${combined_results.iloc[-1]['Monthly Revenue']:.2f}")
    
    return combined_results

if __name__ == "__main__":
    combined_results = test_extension()
    
    # Save to CSV for verification
    combined_results.to_csv("test_extension_results.csv", index=False)
    print("\nResults saved to test_extension_results.csv")