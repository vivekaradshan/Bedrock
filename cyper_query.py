MERGE (c:Customer {id: 'P001'})
SET c.name = 'Priya Sharma',
    c.age = 32,
    c.occupation = 'Software Eng.',
    c.employment_status = 'Full-time',
    c.years_at_job = 7,
    c.marital_status = 'Single',
    c.dependents = 0,
    c.living_situation = 'Own Home',
    c.monthly_income_total = 120000.0,
    c.investment_risk_tolerance = 'Medium',
    c.credit_risk_tolerance = 'Low';

MERGE (c:Customer {id: 'P002'})
SET c.name = 'Raj Kumar',
    c.age = 40,
    c.occupation = 'Small Biz Owner',
    c.employment_status = 'Self-employed',
    c.years_at_job = 5,
    c.marital_status = 'Married',
    c.dependents = 2,
    c.living_situation = 'Own Home',
    c.monthly_income_total = 170000.0,
    c.investment_risk_tolerance = 'High',
    c.credit_risk_tolerance = 'Medium';

MERGE (c:Customer {id: 'P003'})
SET c.name = 'Sana Khan',
    c.age = 28,
    c.occupation = 'Customer Svc.',
    c.employment_status = 'Full-time',
    c.years_at_job = 2,
    c.marital_status = 'Single',
    c.dependents = 0,
    c.living_situation = 'Rent',
    c.monthly_income_total = 45000.0,
    c.investment_risk_tolerance = 'Low',
    c.credit_risk_tolerance = 'High';

// Application APL01 for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (app:Application {id: 'APL01'})
SET app.type = 'Personal Loan',
    app.requested_amount = 250000.0,
    app.term_months = 36,
    app.purpose_of_loan_card = 'Home Renovation',
    app.application_date = '2025-05-20'
MERGE (c)-[:APPLIED_FOR]->(app);

// Application APL02 for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (app:Application {id: 'APL02'})
SET app.type = 'Car Loan',
    app.requested_amount = 800000.0,
    app.term_months = 60,
    app.purpose_of_loan_card = 'New Car Purchase',
    app.application_date = '2025-05-22'
MERGE (c)-[:APPLIED_FOR]->(app);

// Application APL03 for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (app:Application {id: 'APL03'})
SET app.type = 'Credit Card',
    app.requested_amount = 100000.0,
    app.purpose_of_loan_card = 'General Spending',
    app.application_date = '2025-05-21'
MERGE (c)-[:APPLIED_FOR]->(app);

// Accounts for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (acc1:FinancialAccount {id: 'ACC01'}) SET acc1.type = 'Checking', acc1.balance = 25000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc1);
MERGE (acc2:FinancialAccount {id: 'ACC02'}) SET acc2.type = 'Savings', acc2.balance = 120000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc2);
MERGE (acc3:FinancialAccount {id: 'ACC03'}) SET acc3.type = 'Investment', acc3.balance = 500000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc3);

// Accounts for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (acc4:FinancialAccount {id: 'ACC04'}) SET acc4.type = 'Checking', acc4.balance = 35000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc4);
MERGE (acc5:FinancialAccount {id: 'ACC05'}) SET acc5.type = 'Savings', acc5.balance = 80000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc5);
MERGE (acc6:FinancialAccount {id: 'ACC06'}) SET acc6.type = 'Investment', acc6.balance = 750000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc6);

// Accounts for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (acc7:FinancialAccount {id: 'ACC07'}) SET acc7.type = 'Checking', acc7.balance = 15000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc7);
MERGE (acc8:FinancialAccount {id: 'ACC08'}) SET acc8.type = 'Savings', acc8.balance = 5000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc8);

// Accounts for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (acc1:FinancialAccount {id: 'ACC01'}) SET acc1.type = 'Checking', acc1.balance = 25000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc1);
MERGE (acc2:FinancialAccount {id: 'ACC02'}) SET acc2.type = 'Savings', acc2.balance = 120000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc2);
MERGE (acc3:FinancialAccount {id: 'ACC03'}) SET acc3.type = 'Investment', acc3.balance = 500000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc3);

// Accounts for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (acc4:FinancialAccount {id: 'ACC04'}) SET acc4.type = 'Checking', acc4.balance = 35000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc4);
MERGE (acc5:FinancialAccount {id: 'ACC05'}) SET acc5.type = 'Savings', acc5.balance = 80000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc5);
MERGE (acc6:FinancialAccount {id: 'ACC06'}) SET acc6.type = 'Investment', acc6.balance = 750000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc6);

// Accounts for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (acc7:FinancialAccount {id: 'ACC07'}) SET acc7.type = 'Checking', acc7.balance = 15000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc7);
MERGE (acc8:FinancialAccount {id: 'ACC08'}) SET acc8.type = 'Savings', acc8.balance = 5000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc8);

// Accounts for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (acc1:FinancialAccount {id: 'ACC01'}) SET acc1.type = 'Checking', acc1.balance = 25000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc1);
MERGE (acc2:FinancialAccount {id: 'ACC02'}) SET acc2.type = 'Savings', acc2.balance = 120000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc2);
MERGE (acc3:FinancialAccount {id: 'ACC03'}) SET acc3.type = 'Investment', acc3.balance = 500000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc3);

// Accounts for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (acc4:FinancialAccount {id: 'ACC04'}) SET acc4.type = 'Checking', acc4.balance = 35000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc4);
MERGE (acc5:FinancialAccount {id: 'ACC05'}) SET acc5.type = 'Savings', acc5.balance = 80000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc5);
MERGE (acc6:FinancialAccount {id: 'ACC06'}) SET acc6.type = 'Investment', acc6.balance = 750000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc6);

// Accounts for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (acc7:FinancialAccount {id: 'ACC07'}) SET acc7.type = 'Checking', acc7.balance = 15000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc7);
MERGE (acc8:FinancialAccount {id: 'ACC08'}) SET acc8.type = 'Savings', acc8.balance = 5000.0 MERGE (c)-[:HAS_ACCOUNT]->(acc8);

// Debts for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (deb1:Debt {id: 'DEB01'})
SET deb1.type = 'Home Loan',
    deb1.original_amount = 4500000.0,
    deb1.remaining_balance = 3000000.0,
    deb1.monthly_payment = 35000.0,
    deb1.interest_rate = 0.07, // 7.0%
    deb1.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb1);

// Debts for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (deb2:Debt {id: 'DEB02'})
SET deb2.type = 'Home Loan',
    deb2.original_amount = 6000000.0,
    deb2.remaining_balance = 4000000.0,
    deb2.monthly_payment = 45000.0,
    deb2.interest_rate = 0.068, // 6.8%
    deb2.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb2);
MERGE (deb3:Debt {id: 'DEB03'})
SET deb3.type = 'Credit Card (A)',
    deb3.original_amount = 200000.0,
    deb3.remaining_balance = 150000.0,
    deb3.monthly_payment = 5000.0,
    deb3.interest_rate = 0.16, // 16.0%
    deb3.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb3);

// Debts for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (deb4:Debt {id: 'DEB04'})
SET deb4.type = 'Personal Loan',
    deb4.original_amount = 80000.0,
    deb4.remaining_balance = 60000.0,
    deb4.monthly_payment = 3000.0,
    deb4.interest_rate = 0.12, // 12.0%
    deb4.payment_status_last_3_months = ['Current', '30-day late', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb4);
MERGE (deb5:Debt {id: 'DEB05'})
SET deb5.type = 'Credit Card (B)',
    deb5.original_amount = 50000.0,
    deb5.remaining_balance = 45000.0,
    deb5.monthly_payment = 9000.0,
    deb5.interest_rate = 0.22, // 22.0%
    deb5.payment_status_last_3_months = ['Current', 'Current', '30-day late']
MERGE (c)-[:OWES_DEBT]->(deb5);

// Credit Report for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (cr1:CreditReport {id: 'CR01'})
SET cr1.score = 810,
    cr1.last_updated_date = '2025-05-15',
    cr1.number_of_inquiries_l6m = 1,
    cr1.open_accounts = 5,
    cr1.oldest_credit_line_years = 10
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr1);

// Credit Report for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (cr2:CreditReport {id: 'CR02'})
SET cr2.score = 730,
    cr2.last_updated_date = '2025-05-18',
    cr2.number_of_inquiries_l6m = 3,
    cr2.open_accounts = 8,
    cr2.oldest_credit_line_years = 15
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr2);

// Credit Report for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (cr3:CreditReport {id: 'CR03'})
SET cr3.score = 620,
    cr3.last_updated_date = '2025-05-16',
    cr3.number_of_inquiries_l6m = 5,
    cr3.open_accounts = 7,
    cr3.oldest_credit_line_years = 4
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr3);

// Assets for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (ast1:Asset {id: 'AST01'})
SET ast1.type = 'Property', ast1.value = 8000000.0, ast1.description = 'Primary Residence'
MERGE (c)-[:OWNS_ASSET]->(ast1);

// Assets for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (ast2:Asset {id: 'AST02'})
SET ast2.type = 'Property', ast2.value = 10000000.0, ast2.description = 'Primary Residence'
MERGE (c)-[:OWNS_ASSET]->(ast2);
MERGE (ast3:Asset {id: 'AST03'})
SET ast3.type = 'Vehicle', ast3.value = 1500000.0, ast3.description = 'Car (Owned)'
MERGE (c)-[:OWNS_ASSET]->(ast3);

// Goals for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (g1:SavingsGoal {id: 'G01'})
SET g1.name = 'Emergency Fund', g1.target_amount = 200000.0, g1.current_saved = 120000.0, g1.target_date = '2026-06-30'
MERGE (c)-[:HAS_GOAL]->(g1);

// Goal for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (g2:SavingsGoal {id: 'G02'})
SET g2.name = 'Retirement', g2.target_amount = 10000000.0, g2.current_saved = 750000.0, g2.target_date = '2055-12-31'
MERGE (c)-[:HAS_GOAL]->(g2);

// Goal for Sana Khan (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (g3:SavingsGoal {id: 'G03'})
SET g3.name = 'Emergency Fund', g3.target_amount = 50000.0, g3.current_saved = 5000.0, g3.target_date = '2026-06-30'
MERGE (c)-[:HAS_GOAL]->(g3);

// Portfolios for Priya Sharma (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (inv1:InvestmentPortfolio {id: 'INV01'})
SET inv1.name = 'Diversified', inv1.total_value = 500000.0, inv1.asset_mix = '60/30/10'
MERGE (c)-[:HAS_PORTFOLIO]->(inv1);

// Portfolio for Raj Kumar (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (inv2:InvestmentPortfolio {id: 'INV02'})
SET inv2.name = 'Growth', inv2.total_value = 750000.0, inv2.asset_mix = '80/10/10'
MERGE (c)-[:HAS_PORTFOLIO]->(inv2);

// UN001: Banker Interview Notes for Priya Sharma (P001)
MATCH (entity:Customer {id: 'P001'})
MERGE (ud1:UnstructuredData {id: 'UN001'})
SET ud1.type = 'Interview Notes',
    ud1.source = 'Banker',
    ud1.content = 'Applicant expressed strong interest in home renovation. Mentioned planning to use high-quality, durable materials. Seems very organized and financially disciplined, has a clear budget in mind for the renovation. No red flags regarding repayment intent. Confirmed her employer is stable with good growth prospects for her role.',
    ud1.capture_date = '2025-05-20'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud1);

// UN002: Applicant Email for Application APL01 (Priya Sharma's loan)
MATCH (entity:Application {id: 'APL01'})
MERGE (ud2:UnstructuredData {id: 'UN002'})
SET ud2.type = 'Email',
    ud2.source = 'Applicant',
    ud2.content = 'Dear [Banker Name], Just wanted to add that the renovation is primarily for essential repairs and upgrades to my existing property, aiming to increase its long-term value. I''ve attached a detailed breakdown of costs and contractor estimates for your review. Thanks, Priya Sharma.',
    ud2.capture_date = '2025-05-20'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud2);

// UN003: Banker Interview Notes for Raj Kumar (P002)
MATCH (entity:Customer {id: 'P002'})
MERGE (ud3:UnstructuredData {id: 'UN003'})
SET ud3.type = 'Interview Notes',
    ud3.source = 'Banker',
    ud3.content = 'Applicant''s business had a slight downturn last quarter due to seasonal demand, but expects recovery in Q3/Q4 based on signed contracts. Wants the new car primarily for business travel. Explained the higher credit card utilization as being for a recent large business expense that will be reimbursed next month. Seemed a bit stressed about the timing of the car purchase vs. business cash flow.',
    ud3.capture_date = '2025-05-22'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud3);

// UN004: External News for Raj Kumar (P002)
MATCH (entity:Customer {id: 'P002'})
MERGE (ud4:UnstructuredData {id: 'UN004'})
SET ud4.type = 'External News',
    ud4.source = 'Economic Report',
    ud4.content = 'NEWS ALERT: Q2-2025 Economic Report: IT Consulting Sector Faces Temporary Slowdown. Industry experts predict a rebound in Q3/Q4 as new government contracts are expected.',
    ud4.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud4);

// UN005: Banker Interview Notes for Sana Khan (P003)
MATCH (entity:Customer {id: 'P003'})
MERGE (ud5:UnstructuredData {id: 'UN005'})
SET ud5.type = 'Interview Notes',
    ud5.source = 'Banker',
    ud5.content = 'Applicant admitted to some difficulty managing credit card payments recently due to unexpected medical bills. Seemed hesitant when asked about future income stability. Mentioned she is looking for a second part-time job, but nothing confirmed yet. Seems to be relying on this new credit card to consolidate existing small debts.',
    ud5.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud5);

// UN006: Applicant Email for Application APL03 (Sana Khan's Credit Card)
MATCH (entity:Application {id: 'APL03'})
MERGE (ud6:UnstructuredData {id: 'UN006'})
SET ud6.type = 'Email',
    ud6.source = 'Applicant',
    ud6.content = 'Hi, I know my credit score isn''t great right now, but I really need this card. My current limits are too low to cover everything. I''m trying my best to get things under control. Please consider my application. Thanks, Sana.',
    ud6.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud6);