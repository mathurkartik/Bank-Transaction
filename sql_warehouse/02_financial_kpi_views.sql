-- Financial KPI Views for Dashboards - UPDATED for Kaggle data

-- Branch Performance View
CREATE OR REPLACE VIEW bank_dwh.vw_branch_performance AS
SELECT 
    branch_id,
    kpi_date,
    total_revenue,
    total_costs,
    net_income,
    cost_income_ratio,
    transaction_count,
    transaction_per_staff,
    CASE 
        WHEN cost_income_ratio < 0.5 THEN 'Excellent'
        WHEN cost_income_ratio < 0.6 THEN 'Good'
        WHEN cost_income_ratio < 0.7 THEN 'Fair'
        ELSE 'Needs Improvement'
    END AS efficiency_rating,
    CASE 
        WHEN transaction_per_staff > 100 THEN 'High Productivity'
        WHEN transaction_per_staff > 50 THEN 'Medium Productivity'
        ELSE 'Low Productivity'
    END AS productivity_rating
FROM bank_dwh.branch_performance;

-- Customer Profitability View
CREATE OR REPLACE VIEW bank_dwh.vw_customer_profitability AS
SELECT 
    customer_id,
    customer_segment,
    total_revenue,
    net_profit,
    profit_margin,
    CASE 
        WHEN profit_margin > 0.3 THEN 'High Value'
        WHEN profit_margin > 0.1 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS value_tier
FROM bank_dwh.customer_profitability;

-- Loan Portfolio View - NEW for Kaggle data
CREATE OR REPLACE VIEW bank_dwh.vw_loan_portfolio AS
SELECT 
    branch_id,
    total_loan_portfolio,
    total_outstanding,
    avg_interest_rate,
    active_loans,
    CASE 
        WHEN total_loan_portfolio > 0 THEN (total_outstanding / total_loan_portfolio)
        ELSE 0 
    END as utilization_rate,
    CASE 
        WHEN avg_interest_rate > 0.12 THEN 'High Rate'
        WHEN avg_interest_rate > 0.10 THEN 'Medium Rate'
        ELSE 'Low Rate'
    END AS rate_category
FROM bank_dwh.loan_portfolio;

-- Summary KPIs View
CREATE OR REPLACE VIEW bank_dwh.vw_summary_kpis AS
SELECT 
    kpi_date,
    COUNT(DISTINCT customer_id) as total_customers,
    SUM(total_revenue) as total_revenue,
    SUM(net_profit) as total_profit,
    AVG(profit_margin) as avg_profit_margin,
    (SELECT SUM(total_loan_portfolio) FROM bank_dwh.loan_portfolio) as total_loan_portfolio
FROM bank_dwh.customer_profitability
GROUP BY kpi_date;
