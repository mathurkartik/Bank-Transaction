import pandas as pd
import numpy as np
from faker import Faker
import os
from datetime import datetime, timedelta
import logging
import time
import argparse

# Setup logging with performance optimizations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable logging for Faker to improve performance
logging.getLogger('faker').setLevel(logging.WARNING)

fake = Faker()

class KaggleDataIntegrator:
    def __init__(self):
        self.kaggle_prefix = "KAGGLE_"
        self.synthetic_prefix = "SYNTH_"
        self._cache = {}  # Simple cache for repetitive operations
        
    def load_and_clean_kaggle_data(self, kaggle_path, nrows=None):
        """
        Optimized load and clean of Kaggle Bank Transactions dataset with random chunk sampling
        """
        start_time = time.time()
        logger.info(f"Loading Kaggle dataset from: {kaggle_path}")
        
        try:
            skip_offset = 0
            if nrows is not None and nrows > 0:
                # Randomly sample offset chunk to ensure data variety across runs
                import random
                max_possible_skip = max(0, 1000000 - nrows - 100)
                skip_offset = random.randint(0, max_possible_skip)
                logger.info(f"🎲 Random Kaggle Chunk Sampling: skipping first {skip_offset:,} rows for dataset variety.")

            # Load with optimized parameters and random chunk skip
            skip_func = (lambda x: x > 0 and x < skip_offset) if skip_offset > 0 else None
            
            kaggle_df = pd.read_csv(
                kaggle_path, 
                dtype={
                    'CustomerID': 'string',
                    'CustGender': 'string',
                    'CustLocation': 'string',
                    'TransactionID': 'string'
                },
                nrows=nrows,
                skiprows=skip_func,
                low_memory=False
            )
            
            initial_shape = kaggle_df.shape
            logger.info(f"Original Kaggle data shape: {initial_shape}")
            
            # Use vectorized operations instead of iterrows
            cleaned_data = self._vectorized_clean_data(kaggle_df)
            
            load_time = time.time() - start_time
            logger.info(f"Data loaded and cleaned in {load_time:.2f}s: {len(cleaned_data)} records")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error loading Kaggle dataset: {e}")
            raise
    
    def _vectorized_clean_data(self, kaggle_df):
        """Optimized vectorized data cleaning"""
        # Create a copy with optimized dtypes
        df = kaggle_df.copy()
        
        # Vectorized date parsing
        df['parsed_date'] = self._vectorized_parse_dates(df.get('TransactionDate', ''))
        df['parsed_dob'] = self._vectorized_parse_dob(df.get('CustomerDOB', ''))
        
        # Vectorized numeric conversions
        df['account_balance'] = self._vectorized_float_conversion(df.get('CustAccountBalance', 0))
        df['transaction_amount'] = self._vectorized_float_conversion(df.get('TransactionAmount (INR)', 0))
        
        # Vectorized text cleaning
        df['cleaned_gender'] = self._vectorized_clean_gender(df.get('CustGender', ''))
        df['cleaned_city'] = self._vectorized_clean_city(df.get('CustLocation', ''))
        
        # Calculate age vectorized
        df['age'] = self._vectorized_calculate_age(df['parsed_dob'])
        
        # Build final dataframe
        cleaned_df = pd.DataFrame({
            'customer_id': self.kaggle_prefix + df.get('CustomerID', '').fillna('UNKNOWN'),
            'original_customer_id': df.get('CustomerID', ''),
            'gender': df['cleaned_gender'],
            'city': df['cleaned_city'],
            'account_balance': df['account_balance'],
            'transaction_amount': df['transaction_amount'],
            'transaction_date': df['parsed_date'],
            'transaction_id': df.get('TransactionID', ''),
            'transaction_time': df.get('TransactionTime', ''),
            'date_of_birth': df['parsed_dob'],
            'age': df['age'],
            'data_source': 'kaggle_original'
        })
        
        # Replace any remaining NaN ages with random values
        age_mask = cleaned_df['age'].isna()
        if age_mask.any():
            cleaned_df.loc[age_mask, 'age'] = np.random.randint(25, 65, size=age_mask.sum())
        
        return cleaned_df
    
    def _vectorized_parse_dates(self, date_series):
        """Vectorized date parsing"""
        def parse_single_date(date_str):
            try:
                if pd.isna(date_str) or date_str == '':
                    return fake.date_between(start_date='-2y', end_date='today')
                
                parts = str(date_str).split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    return datetime(int(year), int(month), int(day)).date()
                return fake.date_between(start_date='-2y', end_date='today')
            except Exception:
                return fake.date_between(start_date='-2y', end_date='today')
        
        return date_series.apply(parse_single_date)
    
    def _vectorized_parse_dob(self, dob_series):
        """Vectorized DOB parsing"""
        def parse_single_dob(dob_str):
            try:
                if pd.isna(dob_str) or dob_str == '' or dob_str == 'nan' or '1800' in str(dob_str):
                    return None
                
                parts = str(dob_str).split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = '19' + year if int(year) > 50 else '20' + year
                    dob = datetime(int(year), int(month), int(day))
                    if dob.year > 1900 and dob < datetime.now():
                        return dob
                return None
            except Exception:
                return None
        
        return dob_series.apply(parse_single_dob)
    
    def _vectorized_float_conversion(self, value_series):
        """Vectorized float conversion"""
        return pd.to_numeric(value_series, errors='coerce').fillna(0.0)
    
    def _vectorized_clean_gender(self, gender_series):
        """Vectorized gender cleaning"""
        def clean_single_gender(gender):
            if pd.isna(gender) or gender == '':
                return np.random.choice(['M', 'F'])
            return str(gender).upper()[0]
        
        return gender_series.apply(clean_single_gender)
    
    def _vectorized_clean_city(self, city_series):
        """Vectorized city cleaning"""
        def clean_single_city(city):
            if pd.isna(city) or city == '':
                return fake.city()
            return str(city).title()
        
        return city_series.apply(clean_single_city)
    
    def _vectorized_calculate_age(self, dob_series):
        """Vectorized age calculation"""
        def calculate_single_age(dob):
            if pd.isna(dob):
                return np.random.randint(25, 65)
            today = datetime.now()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        return dob_series.apply(calculate_single_age)
    
    def _data_quality_report(self, df):
        """Optimized data quality report with minimal logging"""
        logger.info("📊 DATA QUALITY REPORT:")
        logger.info(f"   Total records: {len(df)}")
        
        # Batch missing values calculation
        missing_info = []
        for col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                missing_info.append(f"     {col}: {missing} missing ({missing/len(df)*100:.1f}%)")
        
        if missing_info:
            logger.info("   Missing values per column:")
            for info in missing_info:
                logger.info(info)
        
        # Customer distribution (single calculation)
        unique_customers = df['customer_id'].nunique()
        logger.info(f"   Unique customers: {unique_customers}")
        logger.info(f"   Avg transactions per customer: {len(df)/unique_customers:.1f}")
        
        # Balance statistics (single pass)
        if 'account_balance' in df.columns:
            balance_stats = {
                'min': df['account_balance'].min(),
                'max': df['account_balance'].max(),
                'mean': df['account_balance'].mean(),
                'median': df['account_balance'].median()
            }
            logger.info(f"   Account balance stats:")
            logger.info(f"     Min: ₹{balance_stats['min']:.2f}")
            logger.info(f"     Max: ₹{balance_stats['max']:.2f}")
            logger.info(f"     Mean: ₹{balance_stats['mean']:.2f}")
            logger.info(f"     Median: ₹{balance_stats['median']:.2f}")

    def generate_synthetic_financial_data(self, kaggle_customers):
        """
        Optimized synthetic financial data generation (fully vectorized)
        """
        start_time = time.time()
        logger.info("Generating synthetic financial extensions...")
        
        kaggle_customer_ids = kaggle_customers['customer_id'].unique()
        
        # Generate all datasets in optimized vectorized manner
        extended_transactions = self._generate_extended_transactions(kaggle_customers)
        revenue_data = self._generate_revenue_data(kaggle_customer_ids)
        cost_data = self._generate_cost_data()
        loan_data = self._generate_loan_data(kaggle_customer_ids)
        branch_data = self._generate_branch_data()
        customer_profiles = self._create_customer_profiles(kaggle_customers)
        
        gen_time = time.time() - start_time
        logger.info(f"Synthetic data generated in {gen_time:.2f}s")
        
        return {
            'customers': customer_profiles,
            'transactions': extended_transactions,
            'revenue': revenue_data,
            'costs': cost_data,
            'loans': loan_data,
            'branches': branch_data
        }
    
    def _generate_extended_transactions(self, kaggle_customers):
        """Optimized transaction generation using vectorized operations"""
        n_rows = len(kaggle_customers)
        logger.info(f"Vectorizing transaction generation for {n_rows} original rows...")
        
        # Vectorized split/extract for account_id
        cust_suffixes = kaggle_customers['customer_id'].str.split('_').str[1].fillna(kaggle_customers['customer_id'])
        account_id = 'ACC_' + cust_suffixes
        
        amount = kaggle_customers['transaction_amount'].abs()
        txn_type = np.where(kaggle_customers['transaction_amount'] > 0, 'DEPOSIT', 'PURCHASE')
        
        # Categorize
        small_cats = ['GROCERIES', 'COFFEE', 'TRANSPORT', 'UTILITIES']
        med_cats = ['SHOPPING', 'DINING', 'ENTERTAINMENT', 'SERVICES']
        large_cats = ['ELECTRONICS', 'TRAVEL', 'HOME_IMPROVEMENT', 'EDUCATION']
        
        cats_small = np.random.choice(small_cats, size=n_rows)
        cats_med = np.random.choice(med_cats, size=n_rows)
        cats_large = np.random.choice(large_cats, size=n_rows)
        category = np.where(amount < 500, cats_small,
                   np.where(amount < 5000, cats_med, cats_large))
        
        # Pre-generate merchants using Faker to avoid slow row-by-row Faker calls
        companies = [fake.company() for _ in range(1000)]
        merchant = np.where(txn_type == 'PURCHASE', np.random.choice(companies, size=n_rows), 'BANK_CREDIT')
        
        # Map cities to branches
        city_branch_map = {
            'MUMBAI': 'BR_001', 'DELHI': 'BR_002', 'BANGALORE': 'BR_003',
            'CHENNAI': 'BR_004', 'KOLKATA': 'BR_005', 'HYDERABAD': 'BR_006',
            'PUNE': 'BR_007', 'AHMEDABAD': 'BR_008', 'JAIPUR': 'BR_009'
        }
        city_upper = kaggle_customers['city'].str.upper().fillna('')
        branch_id = city_upper.map(city_branch_map)
        
        missing_mask = branch_id.isna()
        if missing_mask.any():
            random_branches = [f"BR_{i:03d}" for i in range(10, 51)]
            branch_id[missing_mask] = np.random.choice(random_branches, size=missing_mask.sum())
            
        original_txns = pd.DataFrame({
            'transaction_id': kaggle_customers['transaction_id'],
            'customer_id': kaggle_customers['customer_id'],
            'account_id': account_id,
            'amount': amount,
            'transaction_type': txn_type,
            'category': category,
            'merchant': merchant,
            'timestamp': kaggle_customers['transaction_date'],
            'branch_id': branch_id,
            'currency': 'INR',
            'data_source': 'kaggle_original'
        })
        
        # Generate additional transactions for a 20% sample of unique customers (scalable & fast)
        unique_custs = kaggle_customers.drop_duplicates(subset=['customer_id']).copy()
        sample_custs = unique_custs.sample(frac=0.2).copy()
        
        # Generate a random number of additional transactions per sample customer (between 2 and 6)
        n_repeats = np.random.randint(2, 7, size=len(sample_custs))
        additional_df = sample_custs.loc[sample_custs.index.repeat(n_repeats)].copy()
        n_add = len(additional_df)
        
        # Account suffixes
        add_suffixes = additional_df['customer_id'].str.split('_').str[1].fillna(additional_df['customer_id'])
        additional_df['account_id'] = 'ACC_' + add_suffixes
        
        # Vectorized realistic transaction amount
        balance = additional_df['account_balance']
        base_amount = np.where(balance <= 0, 100, np.minimum(balance * 0.05, 5000))
        add_amount = np.random.lognormal(np.log(base_amount), 0.8)
        additional_df['amount'] = np.round(np.minimum(add_amount, 20000), 2)
        
        additional_df['transaction_type'] = np.random.choice(
            ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT', 'PURCHASE'],
            size=n_add,
            p=[0.1, 0.2, 0.1, 0.3, 0.3]
        )
        
        # Categories for additional
        add_cats_small = np.random.choice(small_cats, size=n_add)
        add_cats_med = np.random.choice(med_cats, size=n_add)
        add_cats_large = np.random.choice(large_cats, size=n_add)
        additional_df['category'] = np.where(additional_df['amount'] < 500, add_cats_small,
                                    np.where(additional_df['amount'] < 5000, add_cats_med, add_cats_large))
        
        # Merchants for additional
        additional_df['merchant'] = np.where(
            additional_df['transaction_type'].isin(['PURCHASE', 'PAYMENT']),
            np.random.choice(companies, size=n_add),
            'BANK'
        )
        
        # Date offset within 180 days before or after original transaction date
        offsets = np.random.randint(-180, 180, size=n_add)
        additional_df['timestamp'] = (pd.to_datetime(additional_df['transaction_date']) + pd.to_timedelta(offsets, unit='D')).dt.date
        
        # Map branch for additional
        add_city_upper = additional_df['city'].str.upper().fillna('')
        add_branch_id = add_city_upper.map(city_branch_map)
        add_missing_mask = add_branch_id.isna()
        if add_missing_mask.any():
            random_branches = [f"BR_{i:03d}" for i in range(10, 51)]
            add_branch_id[add_missing_mask] = np.random.choice(random_branches, size=add_missing_mask.sum())
        additional_df['branch_id'] = add_branch_id
        
        # Unique IDs
        additional_df['transaction_id'] = [f"TX_SYNTH_{i:08d}" for i in range(1, n_add + 1)]
        additional_df['currency'] = 'INR'
        additional_df['data_source'] = 'synthetic_extension'
        
        cols_to_keep = [
            'transaction_id', 'customer_id', 'account_id', 'amount', 'transaction_type', 
            'category', 'merchant', 'timestamp', 'branch_id', 'currency', 'data_source'
        ]
        
        return pd.concat([original_txns, additional_df[cols_to_keep]], ignore_index=True)
    
    def _generate_revenue_data(self, customer_ids):
        """Optimized revenue data generation (vectorized)"""
        # Generate revenue data for a 40% sample of customers
        sample_cust_ids = np.random.choice(customer_ids, size=int(len(customer_ids) * 0.4), replace=False)
        rev_df = pd.DataFrame({'customer_id': sample_cust_ids})
        
        n_repeats = np.random.randint(2, 6, size=len(rev_df))
        rev_df = rev_df.loc[rev_df.index.repeat(n_repeats)].reset_index(drop=True)
        n_rev = len(rev_df)
        
        rev_df['revenue_type'] = np.random.choice(
            ['ACCOUNT_MAINTENANCE_FEE', 'TRANSACTION_FEE', 'INTEREST_INCOME', 'LATE_FEE'],
            size=n_rev,
            p=[0.4, 0.3, 0.2, 0.1]
        )
        
        amt_maintenance = np.random.uniform(100, 300, size=n_rev)
        amt_txn = np.random.uniform(5, 25, size=n_rev)
        amt_interest = np.random.uniform(50, 500, size=n_rev)
        amt_late = np.random.uniform(100, 500, size=n_rev)
        
        rev_df['amount'] = np.where(rev_df['revenue_type'] == 'ACCOUNT_MAINTENANCE_FEE', amt_maintenance,
                           np.where(rev_df['revenue_type'] == 'TRANSACTION_FEE', amt_txn,
                           np.where(rev_df['revenue_type'] == 'INTEREST_INCOME', amt_interest, amt_late)))
        rev_df['amount'] = np.round(rev_df['amount'], 2)
        
        offsets = np.random.randint(0, 365, size=n_rev)
        today = pd.to_datetime('today')
        rev_df['event_date'] = (today - pd.to_timedelta(offsets, unit='D')).date
        
        rev_df['revenue_id'] = [f"REV_{i:07d}" for i in range(1, n_rev + 1)]
        cust_suffixes = rev_df['customer_id'].str.split('_').str[1].fillna(rev_df['customer_id'])
        rev_df['account_id'] = 'ACC_' + cust_suffixes
        
        random_branches = [f"BR_{i:03d}" for i in range(1, 51)]
        rev_df['branch_id'] = np.random.choice(random_branches, size=n_rev)
        rev_df['description'] = rev_df['revenue_type'].str.replace('_', ' ').str.title()
        
        cols_to_keep = [
            'revenue_id', 'customer_id', 'account_id', 'revenue_type', 'amount', 
            'event_date', 'branch_id', 'description'
        ]
        return rev_df[cols_to_keep]
    
    def _generate_cost_data(self):
        """Optimized cost data generation"""
        cost_data = []
        branches = [f'BR_{i:03d}' for i in range(1, 51)]
        cost_categories = ['STAFF_SALARIES', 'TECHNOLOGY', 'FACILITIES', 'MARKETING', 'COMPLIANCE']
        
        for i, branch in enumerate(branches):
            for j in range(np.random.randint(10, 30)):
                category = np.random.choice(cost_categories)
                amount = self._generate_cost_amount(category)
                
                cost_data.append({
                    'cost_id': f"COST_{i:03d}_{j:03d}",
                    'branch_id': branch,
                    'cost_category': category,
                    'amount': amount,
                    'cost_date': fake.date_between(start_date='-1y', end_date='today'),
                    'description': f"{category.replace('_', ' ').title()}",
                    'region': np.random.choice(['NORTH', 'SOUTH', 'EAST', 'WEST'])
                })
        
        return pd.DataFrame(cost_data)
    
    def _generate_cost_amount(self, category, branch_id="BR_001"):
        """Generate realistic cost amounts scaled by branch tier/location"""
        base_amounts = {
            'STAFF_SALARIES': 20000,
            'TECHNOLOGY': 10000,
            'FACILITIES': 15000,
            'MARKETING': 5000,
            'COMPLIANCE': 8000
        }
        
        # Metro branches (BR_001 - BR_009) have higher operating expenses
        metro_multiplier = 1.8 if branch_id in [f"BR_{i:03d}" for i in range(1, 10)] else 1.0
        base = base_amounts.get(category, 5000) * metro_multiplier
        amount = np.random.lognormal(np.log(base), 0.4)
        return round(amount, 2)
    
    def _generate_loan_data(self, customer_ids):
        """Optimized loan data generation (vectorized & credit-score correlated)"""
        # Generate loans for a 20% sample of customers
        customers_with_loans = np.random.choice(
            customer_ids, 
            size=int(len(customer_ids) * 0.2), 
            replace=False
        )
        loan_df = pd.DataFrame({'customer_id': customers_with_loans})
        n_loans = len(loan_df)
        
        loan_df['loan_amount'] = np.round(np.random.uniform(100000, 2000000, size=n_loans), 2)
        loan_df['outstanding_balance'] = np.round(loan_df['loan_amount'] * np.random.uniform(0.2, 0.8, size=n_loans), 2)
        loan_df['loan_id'] = [f"LOAN_{i:06d}" for i in range(1, n_loans + 1)]
        
        # Interest rate correlated with credit score (higher score = lower interest rate)
        credit_scores = np.random.randint(350, 800, size=n_loans)
        base_interest = 0.16 - ((credit_scores - 350) / 450.0) * 0.07  # 9% to 16% range
        noise = np.random.normal(0, 0.005, size=n_loans)
        loan_df['interest_rate'] = np.round(np.clip(base_interest + noise, 0.085, 0.18), 4)
        
        loan_df['loan_type'] = np.random.choice(
            ['HOME_LOAN', 'PERSONAL_LOAN', 'CAR_LOAN', 'EDUCATION_LOAN'], 
            size=n_loans
        )
        
        offsets = np.random.randint(30, 365 * 3, size=n_loans)
        today = pd.to_datetime('today')
        loan_df['start_date'] = (today - pd.to_timedelta(offsets, unit='D')).date
        loan_df['term_months'] = np.random.choice([12, 24, 36, 60, 84], size=n_loans)
        loan_df['status'] = np.random.choice(['ACTIVE', 'CLOSED'], size=n_loans, p=[0.85, 0.15])
        
        random_branches = [f"BR_{i:03d}" for i in range(1, 51)]
        loan_df['branch_id'] = np.random.choice(random_branches, size=n_loans)
        
        cols_to_keep = [
            'loan_id', 'customer_id', 'loan_amount', 'outstanding_balance', 
            'interest_rate', 'loan_type', 'start_date', 'term_months', 'status', 'branch_id'
        ]
        return loan_df[cols_to_keep]
    
    def _generate_branch_data(self):
        """Optimized branch data generation with monthly expansion (+2 new branches/month)"""
        branch_data = []
        indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 
            'Chennai', 'Kolkata', 'Surat', 'Pune', 'Jaipur',
            'Lucknow', 'Kanpur', 'Nagpur', 'Patna', 'Indore',
            'Bhopal', 'Vadodara', 'Coimbatore', 'Ludhiana', 'Agra',
            'Nashik', 'Ranchi', 'Faridabad', 'Meerut', 'Rajkot',
            'Kochi', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad'
        ]
        regions = ['NORTH', 'SOUTH', 'EAST', 'WEST']
        
        # Base 50 branches + monthly expansion (+2 branches per month over past 6 months = 62 total)
        total_branches = 62
        today = datetime.now().date()
        
        for i in range(1, total_branches + 1):
            if i <= len(indian_cities):
                city = indian_cities[i-1]
                region = regions[(i-1) % 4]
            else:
                city = fake.city() + ', India'
                region = np.random.choice(regions)
            
            # Opening dates: Branches 1-50 opened 1-15 yrs ago. Expansion branches 51-62 opened 1-6 months ago (+2/month)
            if i <= 50:
                open_date = fake.date_between(start_date='-15y', end_date='-1y')
            else:
                months_ago = (i - 50) // 2 + 1
                open_date = today - timedelta(days=30 * months_ago)
            
            # Metro cost multiplier for top 9 cities
            metro_mult = 1.8 if i <= 9 else 1.0
            operating_cost = int(np.random.randint(500000, 2000000) * metro_mult)
            
            zones = ['Main Branch', 'North Branch', 'East Branch', 'West Branch', 'South Branch', 'Central Branch', 'IT Park Branch']
            zone = zones[((i-1) // len(indian_cities)) % len(zones)]
            branch_data.append({
                'branch_id': f"BR_{i:03d}",
                'branch_name': f"{city} {zone}",
                'city': city,
                'region': region,
                'country': 'India',
                'opening_date': open_date,
                'branch_manager': fake.name(),
                'staff_count': np.random.randint(8, 50),
                'monthly_operating_cost': operating_cost
            })
        
        return pd.DataFrame(branch_data)
    
    def _create_customer_profiles(self, kaggle_customers):
        """Optimized customer profile creation (vectorized)"""
        unique_custs = kaggle_customers.drop_duplicates(subset=['customer_id']).copy()
        n_cust = len(unique_custs)
        
        first_names = [fake.first_name() for _ in range(1000)]
        last_names = [fake.last_name() for _ in range(1000)]
        
        unique_custs['first_name'] = np.random.choice(first_names, size=n_cust)
        unique_custs['last_name'] = np.random.choice(last_names, size=n_cust)
        unique_custs['country'] = 'India'
        
        # Map segment based on account_balance
        balance = unique_custs['account_balance']
        segment = np.where(balance > 500000, 'PREMIUM',
                  np.where(balance > 100000, 'STANDARD', 'BASIC'))
        unique_custs['customer_segment'] = segment
        
        # Credit score
        unique_custs['credit_score'] = np.random.randint(350, 800, size=n_cust)
        
        # Estimate income
        base_income = np.where(segment == 'PREMIUM', np.maximum(balance * 1.5, 800000),
                      np.where(segment == 'STANDARD', np.maximum(balance * 2.0, 400000),
                                                     np.maximum(balance * 3.0, 200000)))
        unique_custs['annual_income'] = np.round(np.random.normal(base_income, base_income * 0.2)).astype(int)
        
        # Customer since (date - offset)
        offsets = np.random.randint(1, 8 * 365, size=n_cust)
        unique_custs['customer_since'] = (pd.to_datetime(unique_custs['transaction_date']) - pd.to_timedelta(offsets, unit='D')).dt.date
        unique_custs['data_source'] = 'kaggle_enhanced'
        
        cols_to_keep = [
            'customer_id', 'original_customer_id', 'first_name', 'last_name', 'age', 'gender', 'city', 'country',
            'account_balance', 'customer_segment', 'credit_score', 'annual_income', 'customer_since', 'data_source'
        ]
        
        return unique_custs[cols_to_keep]
    
    def _estimate_income(self, account_balance, segment):
        """Estimate annual income"""
        if segment == 'PREMIUM':
            base_income = max(account_balance * 1.5, 800000)
        elif segment == 'STANDARD':
            base_income = max(account_balance * 2, 400000)
        else:
            base_income = max(account_balance * 3, 200000)
        
        return round(np.random.normal(base_income, base_income * 0.2))
    
    def run_integration(self, kaggle_path, output_dir='data/processed', nrows=None):
        """
        Optimized main integration function
        """
        total_start = time.time()
        logger.info("Starting optimized Kaggle data integration...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Load and clean data
        kaggle_data = self.load_and_clean_kaggle_data(kaggle_path, nrows=nrows)
        self._data_quality_report(kaggle_data)
        
        if kaggle_data.empty:
            logger.error("No Kaggle data loaded. Please check the file path and format.")
            return
        
        # Generate synthetic data
        financial_data = self.generate_synthetic_financial_data(kaggle_data)
        
        # Save all datasets
        for name, df in financial_data.items():
            filepath = f"{output_dir}/{name}.csv"
            df.to_csv(filepath, index=False)
        
        # Generate summary
        self._generate_integration_summary(financial_data, output_dir)
        
        total_time = time.time() - total_start
        logger.info(f"🎉 Integration completed in {total_time:.2f}s!")
        
        return financial_data
    
    def _generate_integration_summary(self, datasets, output_dir):
        """Optimized integration summary"""
        summary_lines = [
            "KAGGLE BANK DATA INTEGRATION SUMMARY",
            "=====================================",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for name, df in datasets.items():
            summary_lines.extend([
                f"{name.upper()} DATASET:",
                f"  - Total Records: {len(df):,}",
                ""
            ])
        
        # Save summary
        summary_path = f"{output_dir}/kaggle_integration_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Kaggle bank data integration script")
    parser.add_argument("--full", action="store_true", help="Process the full dataset instead of a sample")
    parser.add_argument("--limit", type=int, default=10000, help="Number of rows to process (default: 10000)")
    args = parser.parse_args()

    integrator = KaggleDataIntegrator()
    
    KAGGLE_PATH = "data/raw/bank_transactions.csv"  
    OUTPUT_DIR = "data/processed"
    
    if not os.path.exists(KAGGLE_PATH):
        logger.warning(f"Kaggle file not found at {KAGGLE_PATH}")
        return
    
    limit = None if args.full else args.limit
    if not args.full:
        logger.info(f"Running in sample mode (limit: {limit} rows). Pass --full to run on the entire dataset.")
    
    try:
        integrated_data = integrator.run_integration(KAGGLE_PATH, OUTPUT_DIR, nrows=limit)
        
        if integrated_data:
            print("\n[SUCCESS] Integration Completed Successfully!")
            print("Generated Datasets:")
            for name, df in integrated_data.items():
                print(f"   - {name}: {len(df):,} records")
            print(f"\nOutput Directory: {OUTPUT_DIR}/")
            
    except Exception as e:
        logger.error(f"❌ Integration failed: {e}")
        raise

if __name__ == "__main__":
    main()
