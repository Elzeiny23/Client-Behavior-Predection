import React, { useState, useEffect } from 'react';
import { LineChart, AreaChart, PieChart, BarChart, Line, Area, Pie, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer, Label } from 'recharts';

// Define constants from Python code
const STATES = ["Immediate Repurchase", "Loyal Customer", "Occasional Buyer", "Discount Buyer", "No Repurchase"];
const STATE_ABBR = ["IR", "LC", "OB", "DB", "NR"];
const COLORS = {
  "Immediate Repurchase": "#1f77b4",  // Blue
  "Loyal Customer": "#ff7f0e",        // Orange
  "Occasional Buyer": "#2ca02c",      // Green
  "Discount Buyer": "#d62728",        // Red
  "No Repurchase": "#9467bd",         // Purple
};

// Monthly revenue per customer segment from revenue_model.py
const MONTHLY_REVENUE = {
  "Immediate Repurchase": 1120 / 12, 
  "Loyal Customer": (165 * 6.5) / 12,
  "Occasional Buyer": 190 * 3.5 / 12,
  "Discount Buyer": 95 * 5 / 12,
  "No Repurchase": 0
};

// Transition matrices for different scenarios from transition_matrices.py
const SCENARIOS = {
  "Default": [
    [0.30, 0.40, 0.10, 0.15, 0.05],  // Immediate Repurchase
    [0.20, 0.50, 0.15, 0.10, 0.05],  // Loyal Customer
    [0.05, 0.20, 0.40, 0.25, 0.10],  // Occasional Buyer
    [0.10, 0.10, 0.20, 0.50, 0.10],  // Discount Buyer
    [0.01, 0.01, 0.01, 0.01, 0.96]   // No Repurchase
  ],
  "Economic Recession": [
    [0.20, 0.30, 0.15, 0.25, 0.10],
    [0.15, 0.40, 0.20, 0.20, 0.05],
    [0.05, 0.15, 0.35, 0.35, 0.10],
    [0.05, 0.05, 0.15, 0.65, 0.10],
    [0.01, 0.01, 0.01, 0.01, 0.96]
  ],
  "Strong Marketing Campaign": [
    [0.40, 0.45, 0.05, 0.05, 0.05],
    [0.30, 0.50, 0.10, 0.05, 0.05],
    [0.10, 0.30, 0.40, 0.15, 0.05],
    [0.05, 0.20, 0.20, 0.45, 0.10],
    [0.01, 0.01, 0.01, 0.01, 0.96]
  ],
  "New Competitor": [
    [0.25, 0.30, 0.20, 0.15, 0.10],
    [0.15, 0.40, 0.25, 0.10, 0.10],
    [0.05, 0.20, 0.35, 0.30, 0.10],
    [0.05, 0.10, 0.20, 0.55, 0.10],
    [0.01, 0.01, 0.01, 0.01, 0.96]
  ],
  "Price Increase": [
    [0.20, 0.30, 0.15, 0.25, 0.10],
    [0.10, 0.35, 0.20, 0.20, 0.15],
    [0.05, 0.15, 0.30, 0.40, 0.10],
    [0.05, 0.05, 0.15, 0.55, 0.20],
    [0.01, 0.01, 0.01, 0.01, 0.96]
  ]
};

// New customer distribution
const NEW_CUSTOMER_DISTRIBUTION = [0.20, 0.25, 0.30, 0.25, 0.0];

// Simulation function adapted from Python code
const simulateMarkovChain = (initialCustomers, newCustomersPerMonth, months, scenario, startMonth = 0, initialDistribution = null) => {
  const results = [];
  
  // Set initial distribution if not provided
  let customerCounts;
  if (initialDistribution) {
    customerCounts = [...initialDistribution];
  } else {
    customerCounts = [0.25, 0.25, 0.25, 0.25, 0.0].map(val => val * initialCustomers);
  }
  
  // Calculate initial monthly revenue
  const calculateRevenue = (counts) => {
    return counts.reduce((sum, count, index) => {
      return sum + count * MONTHLY_REVENUE[STATES[index]];
    }, 0);
  };
  
  // Add initial state
  const totalCustomers = customerCounts.reduce((a, b) => a + b, 0);
  const monthlyRevenue = calculateRevenue(customerCounts);
  
  results.push({
    Month: startMonth,
    TotalCustomers: totalCustomers,
    MonthlyRevenue: monthlyRevenue,
    ChurnRate: 0.0,
    ...STATES.reduce((obj, state, i) => {
      obj[state] = customerCounts[i];
      return obj;
    }, {}),
    ...STATE_ABBR.reduce((obj, abbr, i) => {
      obj[abbr] = customerCounts[i];
      return obj;
    }, {})
  });
  
  // Run simulation for specified months
  const transitionMatrix = SCENARIOS[scenario];
  
  for (let month = 1; month <= months; month++) {
    // Apply transition matrix to current distribution
    const newCounts = Array(customerCounts.length).fill(0);
    
    for (let i = 0; i < STATES.length; i++) {
      for (let j = 0; j < STATES.length; j++) {
        newCounts[j] += customerCounts[i] * transitionMatrix[i][j];
      }
    }
    
    // Add new customers
    NEW_CUSTOMER_DISTRIBUTION.forEach((dist, i) => {
      newCounts[i] += newCustomersPerMonth * dist;
    });
    
    // Round to nearest customer
    customerCounts = newCounts.map(count => Math.round(count));
    
    // Calculate total customers
    const totalCustomers = customerCounts.reduce((a, b) => a + b, 0);
    
    // Calculate monthly revenue
    const monthlyRevenue = calculateRevenue(customerCounts);
    
    // Calculate churn rate
    const previousNR = results[results.length - 1]["No Repurchase"];
    const newNRCustomers = customerCounts[4] - previousNR;
    const activeCustomersBefore = STATES.slice(0, 4).reduce((sum, state) => sum + results[results.length - 1][state], 0);
    const churnRate = activeCustomersBefore > 0 ? (newNRCustomers / activeCustomersBefore * 100) : 0;
    
    // Store results
    results.push({
      Month: startMonth + month,
      TotalCustomers: totalCustomers,
      MonthlyRevenue: monthlyRevenue,
      ChurnRate: churnRate,
      ...STATES.reduce((obj, state, i) => {
        obj[state] = customerCounts[i];
        return obj;
      }, {}),
      ...STATE_ABBR.reduce((obj, abbr, i) => {
        obj[abbr] = customerCounts[i];
        return obj;
      }, {})
    });
  }
  
  return results;
};

// Analyze changes (adapted from visualization.py)
const analyzeChanges = (results) => {
  // Extract initial and final values
  const initialCustomers = results[0].TotalCustomers;
  const finalCustomers = results[results.length - 1].TotalCustomers;
  const customerGrowth = ((finalCustomers - initialCustomers) / initialCustomers) * 100;
  
  const initialRevenue = results[0].MonthlyRevenue;
  const finalRevenue = results[results.length - 1].MonthlyRevenue;
  const revenueGrowth = ((finalRevenue / initialRevenue) - 1) * 100;
  
  // Segment shifts
  const segmentGrowth = {};
  for (let i = 0; i < 4; i++) { // Skip No Repurchase
    const abbr = STATE_ABBR[i];
    const state = STATES[i];
    const initial = results[0][state];
    const final = results[results.length - 1][state];
    if (initial > 0) {
      segmentGrowth[state] = ((final - initial) / initial) * 100;
    }
  }
  
  // Find fastest growing and shrinking segments
  let fastestGrowing = { name: "None", value: 0 };
  let fastestShrinking = { name: "None", value: 0 };
  
  Object.entries(segmentGrowth).forEach(([segment, growth]) => {
    if (growth > fastestGrowing.value) {
      fastestGrowing = { name: segment, value: growth };
    }
    if (growth < fastestShrinking.value) {
      fastestShrinking = { name: segment, value: growth };
    }
  });
  
  // Revenue per customer
  const initialRPC = initialRevenue / initialCustomers;
  const finalRPC = finalRevenue / finalCustomers;
  const rpcChange = ((finalRPC / initialRPC) - 1) * 100;
  
  // Churn analysis
  const finalChurn = results[results.length - 1].ChurnRate;
  const churnTrend = results[results.length - 1].ChurnRate - results[results.length - 2].ChurnRate;
  
  return {
    customerGrowth,
    revenueGrowth,
    rpcChange,
    fastestGrowing,
    fastestShrinking,
    finalChurn,
    churnTrend,
    annualChurnImpact: finalRevenue * (finalChurn / 100) * 12,
    initialCustomers,
    finalCustomers,
    initialRevenue,
    finalRevenue
  };
};

// Actual Dashboard Component
export default function CustomerRetentionDashboard() {
  // State variables
  const [initialParams, setInitialParams] = useState({
    initialCustomers: 10000,
    newCustomersPerMonth: 800,
    months: 12,
    scenario: "Default"
  });
  
  const [extensionParams, setExtensionParams] = useState({
    months: 3,
    scenario: "Default"
  });
  
  const [simResults, setSimResults] = useState([]);
  const [analysisData, setAnalysisData] = useState(null);
  const [showExtension, setShowExtension] = useState(false);
  const [scenarioBreakpoints, setScenarioBreakpoints] = useState([]);
  
  // Run initial simulation
  useEffect(() => {
    const results = simulateMarkovChain(
      initialParams.initialCustomers,
      initialParams.newCustomersPerMonth,
      initialParams.months,
      initialParams.scenario
    );
    setSimResults(results);
    setAnalysisData(analyzeChanges(results));
    setScenarioBreakpoints([{ month: 0, scenario: initialParams.scenario }]);
  }, [initialParams]);
  
  // Handle extending the simulation
  const extendSimulation = () => {
    if (simResults.length === 0) return;
    
    // Get the last data point from current simulation
    const lastResult = simResults[simResults.length - 1];
    const lastMonth = lastResult.Month;
    
    // Extract the final customer distribution
    const finalDistribution = STATES.map(state => lastResult[state]);
    
    // Run extended simulation
    const extendedResults = simulateMarkovChain(
      0, // Doesn't matter as we provide initial distribution
      initialParams.newCustomersPerMonth,
      extensionParams.months,
      extensionParams.scenario,
      lastMonth + 1,
      finalDistribution
    );
    
    // Remove the first point as it duplicates the last point of the original simulation
    extendedResults.shift();
    
    // Combine results
    const combinedResults = [...simResults, ...extendedResults];
    
    // Update scenario breakpoints
    setScenarioBreakpoints([
      ...scenarioBreakpoints,
      { month: lastMonth + 1, scenario: extensionParams.scenario }
    ]);
    
    // Update state
    setSimResults(combinedResults);
    setAnalysisData(analyzeChanges(combinedResults));
    setShowExtension(true);
  };
  
  // Reset to initial simulation
  const resetSimulation = () => {
    const results = simulateMarkovChain(
      initialParams.initialCustomers,
      initialParams.newCustomersPerMonth,
      initialParams.months,
      initialParams.scenario
    );
    setSimResults(results);
    setAnalysisData(analyzeChanges(results));
    setScenarioBreakpoints([{ month: 0, scenario: initialParams.scenario }]);
    setShowExtension(false);
  };
  
  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  // Format percent
  const formatPercent = (value) => {
    return `${value.toFixed(2)}%`;
  };
  
  if (simResults.length === 0) {
    return <div className="flex items-center justify-center h-screen">Loading simulation...</div>;
  }
  
  // Format data for charts
  const segmentData = simResults.map(result => ({
    Month: result.Month,
    "Immediate Repurchase": result["Immediate Repurchase"],
    "Loyal Customer": result["Loyal Customer"],
    "Occasional Buyer": result["Occasional Buyer"],
    "Discount Buyer": result["Discount Buyer"]
  }));
  
  const revenueData = simResults.map(result => ({
    Month: result.Month,
    MonthlyRevenue: result.MonthlyRevenue
  }));
  
  const churnData = simResults.map(result => ({
    Month: result.Month,
    ChurnRate: result.ChurnRate
  }));
  
  // Final distribution data for pie chart
  const finalData = STATES.slice(0, 5).map(state => ({
    name: state,
    value: simResults[simResults.length - 1][state]
  }));
  
  return (
    <div className="p-4 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-2xl font-bold mb-1">Customer Retention Analysis Dashboard</h1>
        <p className="text-gray-600 mb-4">Dynamic visualization of customer behavior using Markov chains</p>
        
        {/* Scenario Timeline */}
        <div className="mb-6 p-4 bg-gray-100 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Scenario Timeline</h2>
          <div className="flex items-center">
            {scenarioBreakpoints.map((breakpoint, index) => (
              <div key={index} className="flex items-center">
                <div className="flex flex-col items-center">
                  <span className="text-sm font-medium">Month {breakpoint.month}</span>
                  <div className="bg-blue-600 w-4 h-4 rounded-full"></div>
                  <span className="text-xs bg-blue-100 p-1 rounded mt-1">{breakpoint.scenario}</span>
                </div>
                {index < scenarioBreakpoints.length - 1 && (
                  <div className="h-0.5 bg-blue-400 w-16 md:w-32 mx-1"></div>
                )}
              </div>
            ))}
            {showExtension && (
              <>
                <div className="h-0.5 bg-blue-400 w-16 md:w-32 mx-1"></div>
                <div className="flex flex-col items-center">
                  <span className="text-sm font-medium">Month {simResults[simResults.length - 1].Month}</span>
                  <div className="bg-blue-600 w-4 h-4 rounded-full"></div>
                  <span className="text-xs">End</span>
                </div>
              </>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Initial Parameters */}
          <div className="bg-gray-100 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Initial Simulation Parameters</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Initial Customers:</label>
                <input 
                  type="number" 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={initialParams.initialCustomers}
                  onChange={(e) => setInitialParams({...initialParams, initialCustomers: parseInt(e.target.value) || 0})}
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">New Customers/Month:</label>
                <input 
                  type="number" 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={initialParams.newCustomersPerMonth}
                  onChange={(e) => setInitialParams({...initialParams, newCustomersPerMonth: parseInt(e.target.value) || 0})}
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Months to Simulate:</label>
                <input 
                  type="number" 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={initialParams.months}
                  onChange={(e) => setInitialParams({...initialParams, months: parseInt(e.target.value) || 1})}
                  min="1"
                  max="60"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Initial Scenario:</label>
                <select 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={initialParams.scenario}
                  onChange={(e) => setInitialParams({...initialParams, scenario: e.target.value})}
                >
                  {Object.keys(SCENARIOS).map(scenario => (
                    <option key={scenario} value={scenario}>{scenario}</option>
                  ))}
                </select>
              </div>
            </div>
            <button 
              onClick={resetSimulation}
              className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Run Initial Simulation
            </button>
          </div>
          
          {/* Extension Parameters */}
          <div className="bg-gray-100 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Extend Simulation</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Additional Months:</label>
                <input 
                  type="number" 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={extensionParams.months}
                  onChange={(e) => setExtensionParams({...extensionParams, months: parseInt(e.target.value) || 1})}
                  min="1"
                  max="60"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">New Scenario:</label>
                <select 
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" 
                  value={extensionParams.scenario}
                  onChange={(e) => setExtensionParams({...extensionParams, scenario: e.target.value})}
                >
                  {Object.keys(SCENARIOS).map(scenario => (
                    <option key={scenario} value={scenario}>{scenario}</option>
                  ))}
                </select>
              </div>
            </div>
            <button 
              onClick={extendSimulation}
              className="mt-4 w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              Extend Simulation with New Scenario
            </button>
          </div>
        </div>
        
        {/* KPI Summary Cards */}
        {analysisData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h3 className="text-sm font-medium text-blue-800">Total Customers</h3>
              <p className="text-2xl font-bold">{analysisData.finalCustomers.toLocaleString()}</p>
              <p className={`text-sm ${analysisData.customerGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analysisData.customerGrowth >= 0 ? '↑' : '↓'} {Math.abs(analysisData.customerGrowth).toFixed(2)}%
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h3 className="text-sm font-medium text-green-800">Monthly Revenue</h3>
              <p className="text-2xl font-bold">{formatCurrency(analysisData.finalRevenue)}</p>
              <p className={`text-sm ${analysisData.revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analysisData.revenueGrowth >= 0 ? '↑' : '↓'} {Math.abs(analysisData.revenueGrowth).toFixed(2)}%
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <h3 className="text-sm font-medium text-red-800">Churn Rate</h3>
              <p className="text-2xl font-bold">{formatPercent(analysisData.finalChurn)}</p>
              <p className={`text-sm ${analysisData.churnTrend <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analysisData.churnTrend <= 0 ? '↓' : '↑'} {formatPercent(Math.abs(analysisData.churnTrend))}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <h3 className="text-sm font-medium text-purple-800">Revenue at Risk (Annual)</h3>
              <p className="text-2xl font-bold">{formatCurrency(analysisData.annualChurnImpact)}</p>
              <p className="text-sm text-gray-600">Due to current churn</p>
            </div>
          </div>
        )}
        
        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Customer Segments Chart */}
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="text-lg font-semibold mb-2">Customer Segments Over Time</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={segmentData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="Month" />
                  <YAxis />
                  <Tooltip formatter={(value) => value.toLocaleString()} />
                  <Legend />
                  {/* Add vertical lines for scenario changes */}
                  {scenarioBreakpoints.slice(1).map((breakpoint, i) => (
                    <CartesianGrid key={i} verticalPoints={[breakpoint.month]} stroke="#666" strokeDasharray="3 3" />
                  ))}
                  <Area type="monotone" dataKey="Immediate Repurchase" stackId="1" stroke={COLORS["Immediate Repurchase"]} fill={COLORS["Immediate Repurchase"]} />
                  <Area type="monotone" dataKey="Loyal Customer" stackId="1" stroke={COLORS["Loyal Customer"]} fill={COLORS["Loyal Customer"]} />
                  <Area type="monotone" dataKey="Occasional Buyer" stackId="1" stroke={COLORS["Occasional Buyer"]} fill={COLORS["Occasional Buyer"]} />
                  <Area type="monotone" dataKey="Discount Buyer" stackId="1" stroke={COLORS["Discount Buyer"]} fill={COLORS["Discount Buyer"]} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Monthly Revenue Chart */}
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="text-lg font-semibold mb-2">Monthly Revenue</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="Month" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  {/* Add vertical lines for scenario changes */}
                  {scenarioBreakpoints.slice(1).map((breakpoint, i) => (
                    <CartesianGrid key={i} verticalPoints={[breakpoint.month]} stroke="#666" strokeDasharray="3 3" />
                  ))}
                  <Line type="monotone" dataKey="MonthlyRevenue" stroke="#2ca02c" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Churn Rate Chart */}
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="text-lg font-semibold mb-2">Churn Rate</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={churnData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="Month" />
                  <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} />
                  <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                  <Legend />
                  {/* Add vertical lines for scenario changes */}
                  {scenarioBreakpoints.slice(1).map((breakpoint, i) => (
                    <CartesianGrid key={i} verticalPoints={[breakpoint.month]} stroke="#666" strokeDasharray="3 3" />
                  ))}
                  <Line type="monotone" dataKey="ChurnRate" stroke="#d62728" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Final Distribution Pie Chart */}
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="text-lg font-semibold mb-2">Current Customer Distribution</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={finalData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  >
                    {finalData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => value.toLocaleString()} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        {/* Analysis & Insights Panel */}
        {analysisData && (
          <div className="bg-gray-50 p-4 rounded-lg border mb-6">
            <h2 className="text-lg font-semibold mb-2">Analysis & Insights</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-md font-medium mb-2">Overall Performance</h3>
                <ul className="space-y-2">
                  <li>
                    <span className="font-medium">Customer base:</span> 
                    <span className={`ml-2 ${analysisData.customerGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.customerGrowth >= 0 ? 'Growing' : 'Shrinking'} at {Math.abs(analysisData.customerGrowth).toFixed(1)}% over period
                    </span>
                  </li>
                  <li>
                    <span className="font-medium">Revenue trend:</span>
                    <span className={`ml-2 ${analysisData.revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.revenueGrowth >= 0 ? 'Positive' : 'Negative'} at {Math.abs(analysisData.revenueGrowth).toFixed(1)}%
                    </span>
                  </li>
                  <li>
                    <span className="font-medium">Revenue per customer:</span>
                    <span className={`ml-2 ${analysisData.rpcChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisData.rpcChange >= 0 ? 'Increased' : 'Decreased'} by {Math.abs(analysisData.rpcChange).toFixed(1)}%
                    </span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-md font-medium mb-2">Segment Shifts</h3>
                <ul className="space-y-2">
                  {analysisData.fastestGrowing.name !== "None" && (
                    <li>
                      <span className="font-medium">Fastest growing:</span>
                      <span className="ml-2 text-green-600">
                        {analysisData.fastestGrowing.name} (+{analysisData.fastestGrowing.value.toFixed(1)}%)
                      </span>
                    </li>
                  )}
                  {analysisData.fastestShrinking.name !== "None" && (
                    <li>
                      <span className="font-medium">Fastest declining:</span>
                      <span className="ml-2 text-red-600">
                        {analysisData.fastestShrinking.name} ({analysisData.fastestShrinking.value.toFixed(1)}%)
                      </span>
                    </li>
                  )}
                  <li>
                    <span className="font-medium">Churn rate:</span>
                    <span className="ml-2">
                      {formatPercent(analysisData.finalChurn)}
                      <span className={`ml-2 ${analysisData.churnTrend <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ({analysisData.churnTrend <= 0 ? 'Decelerating' : 'Accelerating'})
                      </span>
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* Data Table */}
        <div className="overflow-x-auto bg-white rounded-lg border">
          <h2 className="text-lg font-semibold p-4 border-b">Monthly Progression Data</h2>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Month</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IR</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LC</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OB</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DB</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NR</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Customers</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monthly Revenue</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Churn Rate</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {simResults.map((result, index) => {
                // Check if this month is a scenario change point
                const isScenarioChange = scenarioBreakpoints.some(bp => bp.month === result.Month && bp.month > 0);
                
                return (
                  <tr key={index} className={isScenarioChange ? "bg-blue-50" : ""}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {result.Month}
                      {isScenarioChange && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          New Scenario
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.IR).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.LC).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.OB).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.DB).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.NR).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(result.TotalCustomers).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatCurrency(result.MonthlyRevenue)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatPercent(result.ChurnRate)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}