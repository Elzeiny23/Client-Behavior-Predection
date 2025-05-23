from flask import Flask, jsonify, request, send_from_directory
import pandas as pd
import numpy as np
from simulation import CustomerMarkovModel
from transition_matrices import SCENARIOS, STATES, STATE_ABBR, NEW_CUSTOMER_DISTRIBUTION
import json
import os
import shutil
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a Flask app
app = Flask(__name__, static_folder='static')

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """API endpoint to run a simulation"""
    data = request.json
    logger.debug(f"Received simulation request with data: {data}")
    
    # Extract parameters from request with validation
    try:
        initial_customers = int(data.get('initialCustomers', 10000))
        new_customers_per_month = int(data.get('newCustomersPerMonth', 800))
        months = int(data.get('months', 12))
        scenario = data.get('scenario', 'Default')
        
        if initial_customers <= 0 or new_customers_per_month < 0 or months <= 0:
            return jsonify({"error": "Invalid parameters: values must be positive"}), 400
        
        if scenario not in SCENARIOS:
            return jsonify({"error": f"Unknown scenario: {scenario}. Available scenarios: {list(SCENARIOS.keys())}"}), 400
    except ValueError:
        return jsonify({"error": "Invalid parameters: numeric values expected"}), 400
    
    # Create model and run simulation
    try:
        model = CustomerMarkovModel(
            initial_customers=initial_customers,
            new_customers_per_month=new_customers_per_month,
            scenario=scenario
        )
        
        results = model.simulate(months=months)
        
        # Convert the pandas DataFrame to a dictionary for JSON serialization
        results_dict = results.to_dict(orient='records')
        
        # Add JavaScript-friendly property names
        for record in results_dict:
            # Create underscore versions for JavaScript
            if 'Total Customers' in record:
                record['Total_Customers'] = record['Total Customers']
            if 'Monthly Revenue' in record:
                record['Monthly_Revenue'] = record['Monthly Revenue']
            if 'Churn Rate' in record:
                record['Churn_Rate'] = record['Churn Rate']
            
            # Add abbreviated state names
            for i, state in enumerate(STATES):
                if state in record:
                    record[STATE_ABBR[i]] = record[state]
            
            # Ensure all properties have both formats for compatibility
            for state in STATES:
                if state in record:
                    record[state.replace(' ', '_')] = record[state]
        
        logger.debug(f"Successfully generated simulation results with {len(results_dict)} records")
        return jsonify(results_dict)
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Simulation error: {str(e)}"}), 500

@app.route('/api/extend', methods=['POST'])
def extend():
    """API endpoint to extend an existing simulation with a new scenario"""
    data = request.json
    logger.debug(f"Received extension request with data: {data}")
    
    # Extract parameters from request
    try:
        new_customers_per_month = int(data.get('newCustomersPerMonth', 800))
        months = int(data.get('months', 3))
        scenario = data.get('scenario', 'Default')
        previous_results = data.get('previousResults', [])
        
        logger.debug(f"Extension parameters: months={months}, scenario={scenario}, new_customers={new_customers_per_month}")
        logger.debug(f"Previous results count: {len(previous_results)}")
        
        if not previous_results:
            return jsonify({"error": "No previous results provided"}), 400
            
        if new_customers_per_month < 0 or months <= 0:
            return jsonify({"error": "Invalid parameters: values must be positive"}), 400
            
        if scenario not in SCENARIOS:
            return jsonify({"error": f"Unknown scenario: {scenario}. Available scenarios: {list(SCENARIOS.keys())}"}), 400
    except ValueError:
        return jsonify({"error": "Invalid parameters: numeric values expected"}), 400
    
    try:
        # Get the last data point from previous results
        last_result = previous_results[-1]
        logger.debug(f"Last result data keys: {list(last_result.keys())}")
        
        # Extract customer counts - first detect which key format is used
        customer_counts = np.zeros(len(STATES))
        
        # Check which format the data is in (spaces, underscores, or abbreviations)
        format_used = None
        if 'Immediate Repurchase' in last_result:
            format_used = 'spaces'
        elif 'Immediate_Repurchase' in last_result:
            format_used = 'underscores'
        elif 'IR' in last_result:
            format_used = 'abbreviations'
        
        logger.debug(f"Detected format in last result: {format_used}")
        
        # Extract values based on the format detected
        for i, state in enumerate(STATES):
            value = None
            
            if format_used == 'spaces' and state in last_result:
                value = last_result[state]
            elif format_used == 'underscores' and state.replace(' ', '_') in last_result:
                value = last_result[state.replace(' ', '_')]
            elif format_used == 'abbreviations' and STATE_ABBR[i] in last_result:
                value = last_result[STATE_ABBR[i]]
            
            # Convert to float if found
            if value is not None:
                try:
                    if isinstance(value, (int, float)):
                        customer_counts[i] = float(value)
                    else:
                        # Handle string values with commas
                        customer_counts[i] = float(str(value).replace(',', ''))
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {state} value to float: {value}")
                    customer_counts[i] = 0
            else:
                logger.warning(f"Could not find value for {state}, using 0")
        
        logger.debug(f"Extracted customer counts: {customer_counts}")
        
        # Get the last month
        last_month = None
        if 'Month' in last_result:
            try:
                last_month = int(float(last_result['Month']))
            except (ValueError, TypeError):
                logger.warning(f"Could not convert Month to int: {last_result['Month']}")
        
        if last_month is None:
            # If Month not found or conversion failed, try to find the maximum month in previous results
            try:
                months_list = [int(float(r.get('Month', 0))) for r in previous_results if 'Month' in r]
                last_month = max(months_list) if months_list else 0
            except:
                logger.warning("Could not determine last month, defaulting to 0")
                last_month = 0
        
        logger.debug(f"Last month: {last_month}")
        
        # Calculate total customers
        total_customers = int(np.sum(customer_counts))
        logger.debug(f"Total customers from last result: {total_customers}")
        
        # Calculate initial distribution
        if total_customers > 0:
            initial_distribution = customer_counts / total_customers
        else:
            # Default distribution if no customers
            initial_distribution = np.array([0.25, 0.25, 0.25, 0.25, 0.0])
        
        logger.debug(f"Initial distribution: {initial_distribution}")
        
        # Let's add a special debug print to ensure we're properly using new_customers_per_month
        logger.debug(f"DEBUG: new_customers_per_month = {new_customers_per_month}")
        
        # Create a new model, making sure to use the correct new_customers_per_month value
        model = CustomerMarkovModel(
            initial_customers=total_customers,
            new_customers_per_month=new_customers_per_month,  # This should correctly pass through
            scenario=scenario
        )
        
        # Verify the model has the right values
        logger.debug(f"Created model with new_customers_per_month={model.new_customers_per_month}")
        
        # Set the initial distribution
        model.initial_distribution = initial_distribution
        
        # Run the simulation for the desired months
        extension_results = model.simulate(months=months) 
        
        # Verify the simulation is using the right new customer value - let's check the results
        logger.debug(f"For month 1, new customers should be ~{new_customers_per_month}")
        
        # Update month numbers to continue from last result
        for i in range(len(extension_results)):
            extension_results.at[i, 'Month'] = last_month + i
        
        # Calculate the actual new customers added by month
        if len(extension_results) > 1:
            month0_customers = extension_results.iloc[0]['Total Customers']
            month1_customers = extension_results.iloc[1]['Total Customers']
            month0_nr = extension_results.iloc[0]['No Repurchase'] 
            month1_nr = extension_results.iloc[1]['No Repurchase']
            
            # New customers = total increase + customers lost to churn
            customer_increase = month1_customers - month0_customers
            new_nr_customers = month1_nr - month0_nr
            actual_new_customers = customer_increase + new_nr_customers
            
            logger.debug(f"Actual new customers in month 1: {actual_new_customers}")
            logger.debug(f"Customer increase: {customer_increase}, New No Repurchase: {new_nr_customers}")
        
        # Inspect the transition matrix to ensure it's correct
        logger.debug(f"Using transition matrix for scenario '{scenario}':")
        for row in SCENARIOS[scenario]:
            logger.debug(f"  {row}")
        
        # Remove first month to avoid duplication
        extension_results = extension_results.iloc[1:]
        logger.debug(f"Extension results: {len(extension_results)} months of data")
        
        # Convert to dictionary for JSON
        results_dict = extension_results.to_dict(orient='records')
        
        # Add JavaScript-friendly property names
        for record in results_dict:
            # Create underscore versions for JavaScript
            if 'Total Customers' in record:
                record['Total_Customers'] = record['Total Customers']
            if 'Monthly Revenue' in record:
                record['Monthly_Revenue'] = record['Monthly Revenue']
            if 'Churn Rate' in record:
                record['Churn_Rate'] = record['Churn Rate']
            
            # Add abbreviated state names
            for i, state in enumerate(STATES):
                if state in record:
                    record[STATE_ABBR[i]] = record[state]
            
            # Ensure all properties have both formats for compatibility
            for state in STATES:
                if state in record:
                    record[state.replace(' ', '_')] = record[state]
        
        # Print first and last result for debugging
        if results_dict:
            logger.debug(f"First month in extension: Month {results_dict[0]['Month']}, " +
                        f"Total Customers: {results_dict[0]['Total Customers']}, " +
                        f"Revenue: ${results_dict[0]['Monthly Revenue']:.2f}")
            logger.debug(f"Last month in extension: Month {results_dict[-1]['Month']}, " +
                        f"Total Customers: {results_dict[-1]['Total Customers']}, " +
                        f"Revenue: ${results_dict[-1]['Monthly Revenue']:.2f}")
        
        return jsonify(results_dict)
    except Exception as e:
        logger.error(f"Extension error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Extension error: {str(e)}"}), 500

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Return the available scenarios"""
    return jsonify(list(SCENARIOS.keys()))

@app.route('/', methods=['GET'])
def index():
    """Serve the React app"""
    return app.send_static_file('index.html')

# Catch-all route to handle the React router
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    try:
        return app.send_static_file(path)
    except:
        return app.send_static_file('index.html')

def setup_static_directory():
    """Set up the static directory with the index.html file"""
    # Make sure the static folder exists
    os.makedirs('static', exist_ok=True)
    
    # Check if index.html exists in the project directory
    if os.path.exists('index.html'):
        # Copy it to the static directory
        shutil.copy('index.html', 'static/index.html')
        print("Copied index.html to static folder")
    else:
        print("Warning: index.html not found in project directory")

def check_simulation_module():
    """Check if the simulation module is working as expected for new customers"""
    print("Running a test simulation to verify new customer logic...")
    try:
        # Test with 0 new customers
        print("Test with 0 new customers per month:")
        model_zero = CustomerMarkovModel(
            initial_customers=1000,
            new_customers_per_month=0,
            scenario="Default"
        )
        results_zero = model_zero.simulate(months=2)
        print(f"  Month 0: {results_zero.iloc[0]['Total Customers']}")
        print(f"  Month 1: {results_zero.iloc[1]['Total Customers']}")
        
        # Test with 800 new customers
        print("Test with 800 new customers per month:")
        model_800 = CustomerMarkovModel(
            initial_customers=1000,
            new_customers_per_month=800,
            scenario="Default"
        )
        results_800 = model_800.simulate(months=2)
        print(f"  Month 0: {results_800.iloc[0]['Total Customers']}")
        print(f"  Month 1: {results_800.iloc[1]['Total Customers']}")
        
        customer_diff = results_800.iloc[1]['Total Customers'] - results_zero.iloc[1]['Total Customers']
        print(f"  Difference after 1 month: {customer_diff}")
        
        if abs(customer_diff - 800) < 10:  # Allow small rounding differences
            print("✅ Simulation module correctly handles new customers per month")
            return True
        else:
            print("❌ Simulation module doesn't appear to handle new customers correctly")
            print(f"Expected difference of ~800, got {customer_diff}")
            return False
    except Exception as e:
        print(f"❌ Error during test simulation: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Setup static directory
    setup_static_directory()
    
    # Run a test to check if the simulation module handles new customers correctly
    check_simulation_module()
    
    print("\nClient behavior dashboard")
    print("Open your browser at http://localhost:5000")
    
    # Enable detailed error messages in the browser
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(debug=True, port=5000)