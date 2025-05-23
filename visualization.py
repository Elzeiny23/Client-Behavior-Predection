import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.widgets import Button
from transition_matrices import STATE_ABBR, STATES, SCENARIOS
import os

# Professional color palette
COLORS = {
    "Immediate Repurchase": "#1f77b4",  # Blue
    "Loyal Customer": "#ff7f0e",        # Orange
    "Occasional Buyer": "#2ca02c",      # Green
    "Discount Buyer": "#d62728",        # Red
    "No Repurchase": "#9467bd",         # Purple
    "Background": "#f8f9fa",
    "Text": "#343a40",
    "Grid": "#dee2e6",
    "Highlight": "#20c997",
    "Warning": "#dc3545"
}

def analyze_changes(results):
    """
    Analyze key changes in customer behavior and performance metrics.
    
    Args:
        results: DataFrame from the simulate method
        
    Returns:
        Analysis text
    """
    # Calculate key metrics and changes
    initial_customers = results.iloc[0]['Total Customers']
    final_customers = results.iloc[-1]['Total Customers']
    customer_growth = (final_customers - initial_customers) / initial_customers * 100
    
    initial_revenue = results.iloc[0]['Monthly Revenue']
    final_revenue = results.iloc[-1]['Monthly Revenue']
    revenue_growth = (final_revenue / initial_revenue - 1) * 100
    
    # Segment shifts
    segment_growth = {}
    for abbr in STATE_ABBR:
        if abbr != "No Repurchase":  # Skip No Repurchase for this analysis
            initial = results.iloc[0][abbr]
            final = results.iloc[-1][abbr]
            if initial > 0:
                segment_growth[abbr] = (final - initial) / initial * 100
    
    # Find fastest growing and shrinking segments
    if segment_growth:
        fastest_growing = max(segment_growth.items(), key=lambda x: x[1])
        fastest_shrinking = min(segment_growth.items(), key=lambda x: x[1])
    else:
        fastest_growing = (None, 0)
        fastest_shrinking = (None, 0)
    
    # Revenue per customer
    initial_rpc = initial_revenue / initial_customers
    final_rpc = final_revenue / final_customers
    rpc_change = (final_rpc / initial_rpc - 1) * 100
    
    # Create analysis text
    analysis = (
        f"CHANGE ANALYSIS\n"
        f"{'=' * 30}\n\n"
        f"OVERALL PERFORMANCE:\n"
        f"• Customer base: {'Growing' if customer_growth > 0 else 'Shrinking'} at {abs(customer_growth):.1f}% over period\n"
        f"• Revenue trend: {'Positive' if revenue_growth > 0 else 'Negative'} at {abs(revenue_growth):.1f}%\n"
        f"• Revenue per customer: {'Increased' if rpc_change > 0 else 'Decreased'} by {abs(rpc_change):.1f}%\n\n"
        f"SEGMENT SHIFTS:\n"
    )
    
    if fastest_growing[0]:
        analysis += f"• Fastest growing: {fastest_growing[0]} (+{fastest_growing[1]:.1f}%)\n"
    if fastest_shrinking[0]:
        analysis += f"• Fastest declining: {fastest_shrinking[0]} ({fastest_shrinking[1]:.1f}%)\n"
    
    # Churn analysis
    final_churn = results.iloc[-1]['Churn Rate']
    churn_trend = results['Churn Rate'].iloc[-1] - results['Churn Rate'].iloc[-2]
    
    analysis += (
        f"\nCHURN ANALYSIS:\n"
        f"• Current churn rate: {final_churn:.1f}%\n"
        f"• Churn rate trend: {'Accelerating' if churn_trend > 0 else 'Decelerating'} "
        f"({abs(churn_trend):.2f}% change)\n"
        f"• Projected annual impact: ${(final_revenue * (final_churn/100) * 12):.2f} revenue at risk\n"
    )
    
    return analysis

def export_results(results, scenario):
    """Export results to CSV and generate a report"""
    csv_filename = f"customer_simulation_{scenario.replace(' ', '_')}.csv"
    results.to_csv(csv_filename, index=False)
    
    # Create a simple text report
    report_filename = f"report_{scenario.replace(' ', '_')}.txt"
    with open(report_filename, 'w') as f:
        f.write(f"CUSTOMER RETENTION SIMULATION REPORT\n")
        f.write(f"Scenario: {scenario}\n")
        f.write(f"{'-' * 40}\n\n")
        
        # Write summary metrics
        initial_customers = results.iloc[0]['Total Customers']
        final_customers = results.iloc[-1]['Total Customers']
        initial_revenue = results.iloc[0]['Monthly Revenue']
        final_revenue = results.iloc[-1]['Monthly Revenue']
        revenue_growth = (final_revenue / initial_revenue - 1) * 100
        final_churn = results.iloc[-1]['Churn Rate']
        
        f.write(f"SUMMARY METRICS:\n")
        f.write(f"Initial customers: {initial_customers:,.0f}\n")
        f.write(f"Final customers: {final_customers:,.0f}\n")
        f.write(f"Initial monthly revenue: ${initial_revenue:,.2f}\n")
        f.write(f"Final monthly revenue: ${final_revenue:,.2f}\n")
        f.write(f"Revenue growth: {revenue_growth:+.2f}%\n")
        f.write(f"Final churn rate: {final_churn:.2f}%\n\n")
        
        # Write analysis
        f.write(analyze_changes(results))
    
    return csv_filename, report_filename

def compare_scenarios(current_scenario, results):
    """Compare current scenario with all other scenarios"""
    fig, ax = plt.figure(figsize=(12, 10)), plt.subplot(111)
    
    # Load and plot data from existing CSV files
    scenarios_found = []
    for scenario_name in SCENARIOS.keys():
        filename = f"customer_simulation_{scenario_name.replace(' ', '_')}.csv"
        if os.path.exists(filename) and scenario_name != current_scenario:
            try:
                df = pd.read_csv(filename)
                ax.plot(df['Month'], df['Monthly Revenue'], '--', alpha=0.7, 
                        label=f"{scenario_name}")
                scenarios_found.append(scenario_name)
            except Exception:
                pass
    
    # Plot current scenario with thicker line
    ax.plot(results['Month'], results['Monthly Revenue'], 'g-', linewidth=2.5, 
            label=f"{current_scenario} (Current)")
    
    ax.set_title('Revenue Comparison Across Scenarios', fontsize=14)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Monthly Revenue ($)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Format y-axis to show dollar amounts
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    plt.tight_layout()
    plt.show()

def calculate_new_customers(results):
    """
    Calculate new customers entering the system at each month.
    
    Args:
        results: DataFrame from the simulate method
    
    Returns:
        Series with new customers by month
    """
    new_customers = []
    
    # Month 0 has initial distribution of customers
    new_customers.append(results.iloc[0]['Total Customers'])
    
    # For subsequent months, calculate how many new customers entered
    for i in range(1, len(results)):
        # Get difference in 'No Repurchase' to account for churn
        nr_diff = results.iloc[i]['No Repurchase'] - results.iloc[i-1]['No Repurchase']
        
        # Calculate new customers: total increase plus customers lost to churn
        total_diff = results.iloc[i]['Total Customers'] - results.iloc[i-1]['Total Customers']
        new_in_this_month = total_diff + nr_diff
        new_customers.append(new_in_this_month)
    
    return pd.Series(new_customers)

def plot_results(results, scenario="Default"):
    """
    Plot simulation results with improved layout, embedded text summaries,
    analysis panel, and interactive buttons.
    
    Args:
        results: DataFrame from the simulate method
        scenario: The business scenario name
    """
    # Calculate new customers for each month
    new_customers = calculate_new_customers(results)
    
    # Create a larger figure with a specific layout
    fig = plt.figure(figsize=(16, 14), facecolor=COLORS["Background"])  # Decreased height since recommendations removed
    
    # Set up a grid with specific row and column heights
    grid = plt.GridSpec(5, 6, height_ratios=[1, 1, 1, 1, 0.2], hspace=0.6, wspace=0.8)
    
    # 1. Plot customer segment sizes over time (excluding No Repurchase)
    ax1 = fig.add_subplot(grid[0:2, 0:3])
    # Only include the first 4 segments (exclude "No Repurchase")
    for state, color in zip(STATE_ABBR[:4], [COLORS[state] for state in STATE_ABBR[:4]]):
        ax1.plot(results['Month'], results[state], label=state, linewidth=2, color=color)
    ax1.set_title('Customer Segment Sizes', fontsize=14)
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Number of Customers', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2. Plot monthly revenue
    ax2 = fig.add_subplot(grid[0, 3:6])
    ax2.plot(results['Month'], results['Monthly Revenue'], 'g-', linewidth=2.5)
    ax2.set_title('Monthly Revenue', fontsize=14)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Revenue ($)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    # Format y-axis to show dollar amounts
    ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # 3. Plot churn rate
    ax3 = fig.add_subplot(grid[1, 3:6])
    ax3.plot(results['Month'], results['Churn Rate'], 'r-', linewidth=2.5)
    ax3.set_title('Churn Rate', fontsize=14)
    ax3.set_xlabel('Month', fontsize=12)
    ax3.set_ylabel('Churn Rate (%)', fontsize=12)
    ax3.grid(True, alpha=0.3)
    # Format y-axis to show percentages
    ax3.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # 4. Pie chart of final customer distribution
    ax4 = fig.add_subplot(grid[2, 0:2])
    final_distribution = results.iloc[-1][STATE_ABBR]
    wedges, texts, autotexts = ax4.pie(
        final_distribution, 
        labels=STATE_ABBR, 
        autopct='%1.1f%%',
        colors=[COLORS[state] for state in STATE_ABBR],
        startangle=90
    )
    ax4.set_title(f'Final Customer Distribution', fontsize=14)
    # Make percentage labels more readable
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_weight('bold')
    
    # 5. Add summary text
    ax5 = fig.add_subplot(grid[2, 2:4])
    ax5.axis('off')  # Hide axes for text box
    
    # Calculate key metrics for summary
    initial_customers = results.iloc[0]['Total Customers']
    final_customers = results.iloc[-1]['Total Customers']
    initial_revenue = results.iloc[0]['Monthly Revenue']
    final_revenue = results.iloc[-1]['Monthly Revenue']
    revenue_growth = (final_revenue / initial_revenue - 1) * 100
    final_churn = results.iloc[-1]['Churn Rate']
    
    # Prepare segment changes text
    segment_changes = []
    for abbr, state in zip(STATE_ABBR, ["Immediate Repurchasers", "Loyal Customers", 
                                        "Occasional Buyers", "Discount Buyers", 
                                        "No Repurchase"]):
        initial = results.iloc[0][abbr]
        final = results.iloc[-1][abbr]
        change = final - initial
        if abbr != "No Repurchase" and initial > 0:  # Skip percent for NR that starts at 0
            percent = (final / initial - 1) * 100
            segment_changes.append(f"{state}: {initial:.0f} → {final:.0f} ({change:+.0f}, {percent:+.1f}%)")
        else:
            segment_changes.append(f"{state}: {initial:.0f} → {final:.0f} ({change:+.0f})")
    
    # Create summary text
    summary_text = (
        f"SIMULATION SUMMARY\n"
        f"{'=' * 20}\n\n"
        f"OVERALL METRICS:\n"
        f"• Initial customers: {initial_customers:,.0f}\n"
        f"• Final customers: {final_customers:,.0f} ({(final_customers-initial_customers)/initial_customers*100:+.1f}%)\n"
        f"• Initial monthly revenue: ${initial_revenue:,.2f}\n"
        f"• Final monthly revenue: ${final_revenue:,.2f}\n"
        f"• Revenue growth: {revenue_growth:+.2f}%\n"
        f"• Final churn rate: {final_churn:.2f}%"
    )
    
    ax5.text(0, 1, summary_text, fontsize=11, va='top', family='monospace')
    
    # 6. Add analysis of changes panel
    ax6 = fig.add_subplot(grid[2, 4:6])
    ax6.axis('off')  # Hide axes for text box
    
    # Generate analysis
    analysis_text = analyze_changes(results)
    ax6.text(0, 1, analysis_text, fontsize=10, va='top', family='monospace')
    
    # 7. Add milestone table with specific months (0, 1, 3, 6, 9, 12)
    ax7 = fig.add_subplot(grid[3, 0:6])
    ax7.axis('off')  # Hide axes
    
    # Create a table of milestone data
    milestone_months = [0, 1, 3, 6, 9, 12]
    milestone_data = []
    
    # Only include milestone months within the simulation range
    milestone_months = [m for m in milestone_months if m <= results['Month'].max()]
    
    # Extract data for each milestone month
    column_labels = ['Month', 'IR', 'LC', 'OB', 'DB', 'NR', 'New Customers', 
                     'Total Customers', 'Monthly Revenue', 'Churn Rate']
    
    for month in milestone_months:
        row_data = []
        month_data = results[results['Month'] == month].iloc[0]
        
        # Add basic data
        row_data.append(int(month))  # Month
        for state_abbr in ["Immediate Repurchase", "Loyal Customer", "Occasional Buyer", 
                         "Discount Buyer", "No Repurchase"]:
            row_data.append(f"{month_data[state_abbr]:.0f}")
        
        # Add New Customers
        idx = int(month)  # Convert month to index
        if idx < len(new_customers):
            row_data.append(f"{new_customers[idx]:.0f}")
        else:
            row_data.append("N/A")
        
        # Add Total Customers
        row_data.append(f"{month_data['Total Customers']:.0f}")
        
        # Add Monthly Revenue formatted as $
        row_data.append(f"${month_data['Monthly Revenue']:,.2f}")
        
        # Add Churn Rate formatted as %
        row_data.append(f"{month_data['Churn Rate']:.2f}%")
        
        milestone_data.append(row_data)
    
    # Create table
    table = ax7.table(
        cellText=milestone_data,
        colLabels=column_labels,
        loc='center',
        cellLoc='center',
        colColours=['#f8f9fa'] * len(column_labels)
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)  # Adjust table size
    
    # Add title for the table
    ax7.set_title('Customer Segment Milestone Table', fontsize=14, pad=20)
    
    # 8. Add bottom buttons 
    export_btn_ax = fig.add_subplot(grid[4, 0:1])
    compare_btn_ax = fig.add_subplot(grid[4, 1:2])
    reset_btn_ax = fig.add_subplot(grid[4, 2:3])
    run_new_btn_ax = fig.add_subplot(grid[4, 3:4])
    
    export_btn = Button(export_btn_ax, 'Export Results', color='lightblue', hovercolor='skyblue')
    compare_btn = Button(compare_btn_ax, 'Compare Scenarios', color='lightgreen', hovercolor='limegreen')
    reset_btn = Button(reset_btn_ax, 'Reset Simulation', color='salmon', hovercolor='tomato')
    run_new_btn = Button(run_new_btn_ax, 'Run New Scenario', color='plum', hovercolor='orchid')
    
    # Add functionality to buttons
    def export_callback(event):
        csv_file, report_file = export_results(results, scenario)
        plt.figtext(0.5, 0.01, f"Exported to {csv_file} and {report_file}", 
                   ha="center", fontsize=10, bbox={"facecolor":"yellow", "alpha":0.5, "pad":5})
        fig.canvas.draw_idle()
    
    def compare_callback(event):
        compare_scenarios(scenario, results)
    
    def reset_callback(event):
        plt.close()
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "Simulation Reset. Please run the simulation again.", 
                ha='center', va='center', fontsize=14)
        plt.axis('off')
        plt.show()
    
    def run_new_callback(event):
        plt.close()
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "Ready to run a new scenario. Please select options.", 
                ha='center', va='center', fontsize=14)
        plt.axis('off')
        plt.show()
    
    export_btn.on_clicked(export_callback)
    compare_btn.on_clicked(compare_callback)
    reset_btn.on_clicked(reset_callback)
    run_new_btn.on_clicked(run_new_callback)
    
    # Add main title
    plt.suptitle(f"Customer Retention Analysis: {scenario} Scenario", fontsize=16, y=0.98)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.show()