-- Schema & Enhanced Analytical Views for Machine Learning Risk & Real-Time Analytics

CREATE SCHEMA IF NOT EXISTS bank_dwh;

-- 1. Table for ML Loan Default Risk Analytics
CREATE TABLE IF NOT EXISTS bank_dwh.loan_risk_analytics (
    loan_id VARCHAR(50),
    customer_id VARCHAR(50),
    branch_id VARCHAR(50),
    loan_type VARCHAR(50),
    outstanding_balance NUMERIC(15, 2),
    interest_rate NUMERIC(5, 2),
    annual_income NUMERIC(15, 2),
    loan_to_income_ratio NUMERIC(5, 4),
    default_probability NUMERIC(5, 4),
    risk_rating VARCHAR(20),
    ml_evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. View for ML Loan Default Risk Distribution & Branch Exposure
CREATE OR REPLACE VIEW bank_dwh.vw_loan_risk_analytics AS
SELECT 
    lra.loan_id,
    lra.customer_id,
    lra.branch_id,
    lra.loan_type,
    lra.outstanding_balance,
    lra.interest_rate,
    lra.loan_to_income_ratio,
    lra.default_probability,
    lra.risk_rating,
    CASE 
        WHEN lra.risk_rating IN ('High', 'Critical') THEN 'Action Needed: Credit Review'
        WHEN lra.risk_rating = 'Moderate' THEN 'Monitor Performance'
        ELSE 'Healthy Credit'
    END AS risk_action_recommendation,
    lra.ml_evaluated_at
FROM bank_dwh.loan_risk_analytics lra;

-- 3. View for Real-Time Branch Throughput & Transaction Volume
CREATE OR REPLACE VIEW bank_dwh.vw_realtime_branch_tps AS
SELECT 
    bp.branch_id,
    bp.total_revenue,
    bp.total_costs,
    bp.net_income,
    bp.cost_income_ratio,
    bp.transaction_count,
    ROUND(CAST(bp.transaction_count AS NUMERIC) / 86400, 4) AS avg_transactions_per_second,
    bp.transaction_per_staff,
    bp.kpi_date
FROM bank_dwh.branch_performance bp;
