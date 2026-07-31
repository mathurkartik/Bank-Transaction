-- Initialize Bank Data Warehouse - UPDATED for Kaggle data

CREATE SCHEMA IF NOT EXISTS bank_dwh;

-- Customer Profitability Table
CREATE TABLE IF NOT EXISTS bank_dwh.customer_profitability (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_segment VARCHAR(50),
    total_revenue DECIMAL(15,2),
    estimated_costs DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    profit_margin DECIMAL(5,4),
    kpi_date DATE
);

-- Branch Performance Table
CREATE TABLE IF NOT EXISTS bank_dwh.branch_performance (
    branch_id VARCHAR(50) PRIMARY KEY,
    total_revenue DECIMAL(15,2),
    total_costs DECIMAL(15,2),
    net_income DECIMAL(15,2),
    cost_income_ratio DECIMAL(5,4),
    transaction_count INTEGER,
    transaction_per_staff DECIMAL(10,2),
    kpi_date DATE
);

-- Loan Portfolio Table - NEW for Kaggle data
CREATE TABLE IF NOT EXISTS bank_dwh.loan_portfolio (
    branch_id VARCHAR(50) PRIMARY KEY,
    total_loan_portfolio DECIMAL(15,2),
    total_outstanding DECIMAL(15,2),
    avg_interest_rate DECIMAL(5,4),
    active_loans INTEGER,
    kpi_date DATE
);
