import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker
import json

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

class TelcoDataGenerator:
    def __init__(self, num_customers=5000):
        self.num_customers = num_customers
        
    def generate_customer_demographics(self):
        """Generate customer demographic data"""
        customers = []
        
        for i in range(self.num_customers):
            customer = {
                'customer_id': f"CUST_{i+1:06d}",
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.email(),
                'phone_number': fake.phone_number(),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'gender': random.choice(['Male', 'Female', 'Other']),
                'address': fake.address(),
                'city': fake.city(),
                'state': fake.state(),
                'zip_code': fake.zipcode(),
                'country': 'USA',
                'account_creation_date': fake.date_between(start_date='-5y', end_date='today'),
                'customer_segment': random.choice(['Individual', 'Small Business', 'Enterprise']),
                'account_status': random.choices(['Active', 'Suspended', 'Cancelled'], 
                                               weights=[85, 10, 5])[0],
                'preferred_contact_method': random.choice(['Email', 'Phone', 'SMS', 'App']),
                'credit_score': random.randint(300, 850),
                'annual_income': random.randint(25000, 200000)
            }
            customers.append(customer)
            
        return pd.DataFrame(customers)
    
    def generate_service_plans(self):
        """Generate available service plans"""
        plans = [
            {'plan_id': 'PLAN_001', 'plan_name': 'Basic Mobile', 'service_type': 'Mobile', 'monthly_fee': 35.99, 'data_gb': 5, 'minutes': 500, 'texts': 'Unlimited'},
            {'plan_id': 'PLAN_002', 'plan_name': 'Premium Mobile', 'service_type': 'Mobile', 'monthly_fee': 55.99, 'data_gb': 25, 'minutes': 'Unlimited', 'texts': 'Unlimited'},
            {'plan_id': 'PLAN_003', 'plan_name': 'Ultimate Mobile', 'service_type': 'Mobile', 'monthly_fee': 85.99, 'data_gb': 'Unlimited', 'minutes': 'Unlimited', 'texts': 'Unlimited'},
            {'plan_id': 'PLAN_004', 'plan_name': 'Home Internet Basic', 'service_type': 'Internet', 'monthly_fee': 49.99, 'speed_mbps': 100, 'data_limit': 'Unlimited'},
            {'plan_id': 'PLAN_005', 'plan_name': 'Home Internet Pro', 'service_type': 'Internet', 'monthly_fee': 69.99, 'speed_mbps': 300, 'data_limit': 'Unlimited'},
            {'plan_id': 'PLAN_006', 'plan_name': 'Home Internet Gigabit', 'service_type': 'Internet', 'monthly_fee': 99.99, 'speed_mbps': 1000, 'data_limit': 'Unlimited'},
            {'plan_id': 'PLAN_007', 'plan_name': 'Basic TV', 'service_type': 'TV', 'monthly_fee': 39.99, 'channels': 100, 'hd_channels': 50},
            {'plan_id': 'PLAN_008', 'plan_name': 'Premium TV', 'service_type': 'TV', 'monthly_fee': 79.99, 'channels': 250, 'hd_channels': 150},
            {'plan_id': 'PLAN_009', 'plan_name': 'Business Mobile', 'service_type': 'Mobile', 'monthly_fee': 45.99, 'data_gb': 20, 'minutes': 'Unlimited', 'texts': 'Unlimited'},
            {'plan_id': 'PLAN_010', 'plan_name': 'Business Internet', 'service_type': 'Internet', 'monthly_fee': 129.99, 'speed_mbps': 500, 'data_limit': 'Unlimited'}
        ]
        return pd.DataFrame(plans)
    
    def generate_customer_services(self, customers_df, plans_df):
        """Generate customer service subscriptions"""
        services = []
        
        for _, customer in customers_df.iterrows():
            # Each customer has 1-4 services
            num_services = random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10])[0]
            
            # Enterprise customers more likely to have business plans
            if customer['customer_segment'] == 'Enterprise':
                available_plans = plans_df[plans_df['plan_name'].str.contains('Business|Premium|Ultimate|Pro|Gigabit')]
            elif customer['customer_segment'] == 'Small Business':
                available_plans = plans_df[~plans_df['plan_name'].str.contains('Basic')]
            else:
                available_plans = plans_df
            
            selected_plans = available_plans.sample(min(num_services, len(available_plans)))
            
            for _, plan in selected_plans.iterrows():
                service_start = fake.date_between(
                    start_date=customer['account_creation_date'], 
                    end_date='today'
                )
                
                service = {
                    'customer_id': customer['customer_id'],
                    'service_id': f"SVC_{len(services)+1:08d}",
                    'plan_id': plan['plan_id'],
                    'plan_name': plan['plan_name'],
                    'service_type': plan['service_type'],
                    'monthly_fee': plan['monthly_fee'],
                    'service_start_date': service_start,
                    'service_status': random.choices(['Active', 'Suspended', 'Cancelled'], 
                                                   weights=[85, 8, 7])[0],
                    'auto_pay': random.choice([True, False]),
                    'contract_length': random.choice([12, 24, 0]),  # 0 for month-to-month
                    'early_termination_fee': random.uniform(0, 200) if random.random() < 0.3 else 0
                }
                services.append(service)
        
        return pd.DataFrame(services)
    
    def generate_usage_data(self, services_df):
        """Generate monthly usage data for each service"""
        usage_data = []
        
        for _, service in services_df.iterrows():
            if service['service_status'] == 'Active':
                # Generate 12 months of usage data
                for month_offset in range(12):
                    usage_date = datetime.now() - timedelta(days=30 * month_offset)
                    
                    if service['service_type'] == 'Mobile':
                        data_used = max(0, np.random.normal(15, 8))  # GB
                        minutes_used = max(0, int(np.random.normal(800, 400)))
                        texts_sent = max(0, int(np.random.normal(1500, 800)))
                        
                        usage = {
                            'customer_id': service['customer_id'],
                            'service_id': service['service_id'],
                            'usage_month': usage_date.strftime('%Y-%m'),
                            'data_used_gb': round(data_used, 2),
                            'minutes_used': minutes_used,
                            'texts_sent': texts_sent,
                            'overage_charges': max(0, (data_used - 25) * 10) if data_used > 25 else 0
                        }
                    
                    elif service['service_type'] == 'Internet':
                        data_used = max(0, np.random.normal(400, 200))  # GB
                        usage = {
                            'customer_id': service['customer_id'],
                            'service_id': service['service_id'],
                            'usage_month': usage_date.strftime('%Y-%m'),
                            'data_used_gb': round(data_used, 2),
                            'peak_speed_mbps': np.random.normal(0.8, 0.1) * service['monthly_fee'] * 10,  # Rough correlation
                            'uptime_percentage': max(95, np.random.normal(99.2, 1.5))
                        }
                    
                    elif service['service_type'] == 'TV':
                        usage = {
                            'customer_id': service['customer_id'],
                            'service_id': service['service_id'],
                            'usage_month': usage_date.strftime('%Y-%m'),
                            'hours_watched': max(0, int(np.random.normal(120, 60))),
                            'channels_watched': max(1, int(np.random.normal(15, 8))),
                            'ppv_purchases': random.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0] * 4.99
                        }
                    
                    usage_data.append(usage)
        
        return pd.DataFrame(usage_data)
    
    def generate_billing_data(self, services_df):
        """Generate billing and payment history"""
        billing_data = []
        
        for _, service in services_df.iterrows():
            # Generate 12 months of billing
            for month_offset in range(12):
                bill_date = datetime.now() - timedelta(days=30 * month_offset)
                due_date = bill_date + timedelta(days=15)
                
                base_amount = service['monthly_fee']
                taxes = base_amount * 0.08
                fees = random.uniform(2, 8)
                total_amount = base_amount + taxes + fees
                
                # Add some overage charges occasionally
                if random.random() < 0.15:
                    total_amount += random.uniform(10, 50)
                
                payment_status = random.choices(['Paid', 'Late', 'Unpaid'], weights=[85, 10, 5])[0]
                payment_date = None
                if payment_status == 'Paid':
                    payment_date = due_date + timedelta(days=random.randint(-5, 5))
                elif payment_status == 'Late':
                    payment_date = due_date + timedelta(days=random.randint(1, 15))
                
                billing = {
                    'customer_id': service['customer_id'],
                    'service_id': service['service_id'],
                    'bill_date': bill_date,
                    'due_date': due_date,
                    'amount_due': round(total_amount, 2),
                    'amount_paid': round(total_amount, 2) if payment_status in ['Paid', 'Late'] else 0,
                    'payment_date': payment_date,
                    'payment_method': random.choice(['Credit Card', 'Bank Transfer', 'Check', 'Auto Pay']),
                    'payment_status': payment_status,
                    'late_fee': 25.0 if payment_status == 'Late' else 0.0
                }
                billing_data.append(billing)
        
        return pd.DataFrame(billing_data)
    
    def generate_support_tickets(self, customers_df):
        """Generate customer support interaction history"""
        tickets = []
        
        # Some customers have support tickets
        customers_with_tickets = customers_df.sample(frac=0.4)
        
        for _, customer in customers_with_tickets.iterrows():
            num_tickets = random.choices([1, 2, 3, 4, 5], weights=[50, 30, 15, 4, 1])[0]
            
            for _ in range(num_tickets):
                ticket_date = fake.date_between(
                    start_date=customer['account_creation_date'],
                    end_date='today'
                )
                
                issue_types = ['Billing', 'Technical Support', 'Service Change', 'Complaint', 'Sales Inquiry']
                issue_type = random.choice(issue_types)
                
                # Resolution time varies by issue type
                resolution_hours = {
                    'Billing': random.uniform(1, 24),
                    'Technical Support': random.uniform(2, 72),
                    'Service Change': random.uniform(0.5, 8),
                    'Complaint': random.uniform(4, 48),
                    'Sales Inquiry': random.uniform(0.5, 4)
                }
                
                ticket = {
                    'customer_id': customer['customer_id'],
                    'ticket_id': f"TKT_{len(tickets)+1:08d}",
                    'creation_date': ticket_date,
                    'issue_type': issue_type,
                    'priority': random.choices(['Low', 'Medium', 'High', 'Critical'], 
                                             weights=[40, 35, 20, 5])[0],
                    'status': random.choices(['Closed', 'Open', 'In Progress'], 
                                           weights=[80, 10, 10])[0],
                    'resolution_time_hours': resolution_hours[issue_type],
                    'satisfaction_rating': random.choices([1, 2, 3, 4, 5], 
                                                        weights=[5, 10, 20, 35, 30])[0],
                    'channel': random.choice(['Phone', 'Email', 'Chat', 'In Store', 'App']),
                    'agent_id': f"AGT_{random.randint(1, 50):03d}"
                }
                tickets.append(ticket)
        
        return pd.DataFrame(tickets)
    
    def generate_nps_surveys(self, customers_df):
        """Generate Net Promoter Score survey data"""
        surveys = []
        
        # Random subset of customers receive NPS surveys
        surveyed_customers = customers_df.sample(frac=0.3)
        
        for _, customer in surveyed_customers.iterrows():
            # Multiple surveys over time
            num_surveys = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            
            for _ in range(num_surveys):
                survey_date = fake.date_between(
                    start_date=customer['account_creation_date'],
                    end_date='today'
                )
                
                # NPS score 0-10
                nps_score = random.choices(range(11), weights=[3, 2, 3, 4, 5, 8, 12, 15, 18, 20, 10])[0]
                
                survey = {
                    'customer_id': customer['customer_id'],
                    'survey_id': f"NPS_{len(surveys)+1:08d}",
                    'survey_date': survey_date,
                    'nps_score': nps_score,
                    'category': 'Promoter' if nps_score >= 9 else 'Passive' if nps_score >= 7 else 'Detractor',
                    'feedback': fake.sentence(nb_words=random.randint(10, 30)) if random.random() < 0.6 else None
                }
                surveys.append(survey)
        
        return pd.DataFrame(surveys)
    
    def calculate_customer_metrics(self, customers_df, services_df, billing_df, tickets_df, nps_df):
        """Calculate key customer metrics for sales insights"""
        metrics = []
        
        for _, customer in customers_df.iterrows():
            customer_id = customer['customer_id']
            
            # Service metrics
            customer_services = services_df[services_df['customer_id'] == customer_id]
            active_services = customer_services[customer_services['service_status'] == 'Active']
            
            # Revenue metrics
            customer_billing = billing_df[billing_df['customer_id'] == customer_id]
            monthly_revenue = customer_billing.groupby('bill_date')['amount_due'].sum().mean()
            total_revenue = customer_billing['amount_paid'].sum()
            
            # Support metrics
            customer_tickets = tickets_df[tickets_df['customer_id'] == customer_id]
            avg_resolution_time = customer_tickets['resolution_time_hours'].mean() if len(customer_tickets) > 0 else 0
            avg_satisfaction = customer_tickets['satisfaction_rating'].mean() if len(customer_tickets) > 0 else 5
            
            # NPS metrics
            customer_nps = nps_df[nps_df['customer_id'] == customer_id]
            latest_nps = customer_nps.loc[customer_nps['survey_date'].idxmax()]['nps_score'] if len(customer_nps) > 0 else None
            
            # Calculate churn risk score (0-100)
            risk_factors = 0
            if len(customer_tickets) > 3: risk_factors += 20
            if avg_satisfaction < 3: risk_factors += 25
            if latest_nps and latest_nps <= 6: risk_factors += 30
            if customer_billing['payment_status'].str.contains('Late|Unpaid').sum() > 2: risk_factors += 25
            
            churn_risk = min(100, risk_factors)
            
            # Calculate upsell score
            upsell_score = 0
            if len(active_services) < 3: upsell_score += 30
            if monthly_revenue < 100: upsell_score += 20
            if avg_satisfaction >= 4: upsell_score += 25
            if latest_nps and latest_nps >= 8: upsell_score += 25
            
            customer_metric = {
                'customer_id': customer_id,
                'total_services': len(customer_services),
                'active_services': len(active_services),
                'monthly_revenue': round(monthly_revenue, 2) if not pd.isna(monthly_revenue) else 0,
                'total_lifetime_value': round(total_revenue, 2),
                'tenure_months': (datetime.now().date() - customer['account_creation_date']).days // 30,
                'support_tickets_count': len(customer_tickets),
                'avg_resolution_time_hours': round(avg_resolution_time, 1),
                'avg_satisfaction_rating': round(avg_satisfaction, 1),
                'latest_nps_score': latest_nps,
                'churn_risk_score': churn_risk,
                'upsell_score': min(100, upsell_score),
                'last_interaction_date': customer_tickets['creation_date'].max() if len(customer_tickets) > 0 else None
            }
            metrics.append(customer_metric)
        
        return pd.DataFrame(metrics)
    
    def generate_all_data(self):
        """Generate all customer data tables"""
        print("Generating customer demographics...")
        customers_df = self.generate_customer_demographics()
        
        print("Generating service plans...")
        plans_df = self.generate_service_plans()
        
        print("Generating customer services...")
        services_df = self.generate_customer_services(customers_df, plans_df)
        
        print("Generating usage data...")
        usage_df = self.generate_usage_data(services_df)
        
        print("Generating billing data...")
        billing_df = self.generate_billing_data(services_df)
        
        print("Generating support tickets...")
        tickets_df = self.generate_support_tickets(customers_df)
        
        print("Generating NPS surveys...")
        nps_df = self.generate_nps_surveys(customers_df)
        
        print("Calculating customer metrics...")
        metrics_df = self.calculate_customer_metrics(customers_df, services_df, billing_df, tickets_df, nps_df)
        
        return {
            'customers': customers_df,
            'plans': plans_df,
            'services': services_df,
            'usage': usage_df,
            'billing': billing_df,
            'support_tickets': tickets_df,
            'nps_surveys': nps_df,
            'customer_metrics': metrics_df
        }

if __name__ == "__main__":
    generator = TelcoDataGenerator(num_customers=1000)
    data = generator.generate_all_data()
    
    # Save to CSV files
    for table_name, df in data.items():
        df.to_csv(f"data/{table_name}.csv", index=False)
        print(f"Saved {table_name}.csv with {len(df)} rows")