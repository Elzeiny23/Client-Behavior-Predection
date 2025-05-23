import pandas as pd
from transition_matrices import SCENARIOS, STATE_ABBR
from simulation import CustomerMarkovModel
from visualization import plot_results

def display_banner():
    """Display a banner for the program"""
    print("=" * 70)
    print("                 CUSTOMER RETENTION MARKOV MODEL                   ")
    print("=" * 70)
    print("This program simulates customer behavior using Markov chains.")
    print("It predicts customer segment transitions over time under different")
    print("business scenarios and calculates the impact on revenue.\n")

def main():
    """Main function to run the customer retention simulation"""
    display_banner()
    
    # Display available scenarios
    print("Available scenarios:")
    for i, scenario in enumerate(SCENARIOS.keys()):
        print(f"{i+1}. {scenario}")
    
    # Get user input for scenario
    try:
        scenario_idx = int(input("\nSelect scenario (1-5): ")) - 1
        scenario = list(SCENARIOS.keys())[scenario_idx]
    except (ValueError, IndexError):
        print("Invalid selection. Using default scenario.")
        scenario = "Default"
    
    # Get user input for simulation parameters
    try:
        print("\nEnter simulation parameters (or press Enter for defaults):")
        initial_customers_input = input("Initial customers [10000]: ")
        initial_customers = int(initial_customers_input) if initial_customers_input else 10000
        
        new_customers_input = input("New customers per month [800]: ")
        new_customers_per_month = int(new_customers_input) if new_customers_input else 800
        
        months_input = input("Number of months to simulate [12]: ")
        months = int(months_input) if months_input else 12
    except ValueError:
        print("Invalid input. Using default values.")
        initial_customers = 10000
        new_customers_per_month = 800
        months = 12
    
    # Create model and run simulation
    print(f"\nRunning simulation for scenario: {scenario}")
    print(f"Initial customers: {initial_customers}")
    print(f"New customers per month: {new_customers_per_month}")
    print(f"Simulation period: {months} months\n")
    
    model = CustomerMarkovModel(
        initial_customers=initial_customers,
        new_customers_per_month=new_customers_per_month,
        scenario=scenario
    )
    
    results = model.simulate(months=months)
    
    # Display summary results
    print("\nSUMMARY RESULTS:")
    print("-" * 70)
    print(f"Initial customers: {results.iloc[0]['Total Customers']}")
    print(f"Final customers: {results.iloc[-1]['Total Customers']}")
    print(f"Initial monthly revenue: ${results.iloc[0]['Monthly Revenue']:.2f}")
    print(f"Final monthly revenue: ${results.iloc[-1]['Monthly Revenue']:.2f}")
    revenue_growth = (results.iloc[-1]['Monthly Revenue'] / results.iloc[0]['Monthly Revenue'] - 1) * 100
    print(f"Revenue growth: {revenue_growth:.2f}%")
    print(f"Final churn rate: {results.iloc[-1]['Churn Rate']:.2f}%")
    
    # Display segment changes
    print("\nCUSTOMER SEGMENT CHANGES:")
    print("-" * 70)
    for abbr, state in zip(STATE_ABBR, ["Immediate Repurchasers", "Loyal Customers", 
                                         "Occasional Buyers", "Discount Buyers", 
                                         "No Repurchase"]):
        initial = results.iloc[0][abbr]
        final = results.iloc[-1][abbr]
        change = final - initial
        percent = (final / initial - 1) * 100 if initial > 0 else float('inf')
        
        if abbr != "No Repurchase":  # Skip percent change for No Repurchase (starts at 0)
            print(f"{state}: {initial:.0f} → {final:.0f} ({change:+.0f}, {percent:+.2f}%)")
        else:
            print(f"{state}: {initial:.0f} → {final:.0f} ({change:+.0f})")
    
    # Display monthly progression
    print("\nMONTHLY PROGRESSION:")
    print("-" * 70)
    display_columns = ['Month', 'Immediate Repurchase', 'Loyal Customer', 'Occasional Buyer', 'Discount Buyer', 'No Repurchase', 'Monthly Revenue', 'Churn Rate']
    
    # Format for better display
    pd.set_option('display.float_format', '${:.2f}'.format)
    formatted_results = results[display_columns].copy()
    formatted_results['Churn Rate'] = results['Churn Rate'].apply(lambda x: f"{x:.2f}%")
    print(formatted_results.to_string(index=False))
    
    # Save results to CSV
    try:
        csv_filename = f"customer_simulation_{scenario.replace(' ', '_')}.csv"
        results.to_csv(csv_filename, index=False)
        print(f"\nResults saved to {csv_filename}")
    except Exception as e:
        print(f"\nCould not save results to CSV: {e}")
    
    # Open visualization with interactive features
    print("\nOpening interactive visualization with analysis...")
    plot_results(results, scenario)

if __name__ == "__main__":
    main()
