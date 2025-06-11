// Application APL01 for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (app:Application {id: 'APL01'})
SET app.type = 'Personal Loan',
    app.requested_amount = 25000.0, // Adjusted for US personal loan range
    app.currency = 'USD',
    app.term_months = 36,
    app.purpose_of_loan_card = 'Home Renovation',
    app.application_date = '2025-05-20'
MERGE (c)-[:APPLIED_FOR]->(app);

// Application APL02 for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (app:Application {id: 'APL02'})
SET app.type = 'Car Loan',
    app.requested_amount = 45000.0, // Adjusted for US car loan range
    app.currency = 'USD',
    app.term_months = 60,
    app.purpose_of_loan_card = 'New Car Purchase',
    app.application_date = '2025-05-22'
MERGE (c)-[:APPLIED_FOR]->(app);

// Application APL03 for Jessica Williams (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (app:Application {id: 'APL03'})
SET app.type = 'Credit Card',
    app.requested_amount = 5000.0, // Adjusted for US credit card limit
    app.currency = 'USD',
    app.purpose_of_loan_card = 'General Spending',
    app.application_date = '2025-05-21'
MERGE (c)-[:APPLIED_FOR]->(app);



// Accounts for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (acc1:FinancialAccount {id: 'ACC01'}) SET acc1.type = 'Checking', acc1.balance = 2500.0, acc1.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc1);
MERGE (acc2:FinancialAccount {id: 'ACC02'}) SET acc2.type = 'Savings', acc2.balance = 12000.0, acc2.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc2);
MERGE (acc3:FinancialAccount {id: 'ACC03'}) SET acc3.type = 'Investment', acc3.balance = 50000.0, acc3.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc3);

// Accounts for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (acc4:FinancialAccount {id: 'ACC04'}) SET acc4.type = 'Checking', acc4.balance = 3500.0, acc4.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc4);
MERGE (acc5:FinancialAccount {id: 'ACC05'}) SET acc5.type = 'Savings', acc5.balance = 8000.0, acc5.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc5);
MERGE (acc6:FinancialAccount {id: 'ACC06'}) SET acc6.type = 'Investment', acc6.balance = 75000.0, acc6.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc6);

// Accounts for Jessica Williams (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (acc7:FinancialAccount {id: 'ACC07'}) SET acc7.type = 'Checking', acc7.balance = 1500.0, acc7.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc7);
MERGE (acc8:FinancialAccount {id: 'ACC08'}) SET acc8.type = 'Savings', acc8.balance = 500.0, acc8.currency = 'USD' MERGE (c)-[:HAS_ACCOUNT]->(acc8);



// Debts for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (deb1:Debt {id: 'DEB01'})
SET deb1.type = 'Home Loan',
    deb1.original_amount = 450000.0, // Adjusted for US home loan
    deb1.remaining_balance = 300000.0,
    deb1.monthly_payment = 2500.0,
    deb1.currency = 'USD',
    deb1.interest_rate = 0.07, // 7.0%
    deb1.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb1);

// Debts for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (deb2:Debt {id: 'DEB02'})
SET deb2.type = 'Home Loan',
    deb2.original_amount = 600000.0, // Adjusted for US home loan
    deb2.remaining_balance = 400000.0,
    deb2.monthly_payment = 3000.0,
    deb2.currency = 'USD',
    deb2.interest_rate = 0.068, // 6.8%
    deb2.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb2);
MERGE (deb3:Debt {id: 'DEB03'})
SET deb3.type = 'Credit Card (A)',
    deb3.original_amount = 15000.0, // Adjusted for US credit card
    deb3.remaining_balance = 10000.0,
    deb3.monthly_payment = 500.0,
    deb3.currency = 'USD',
    deb3.interest_rate = 0.16, // 16.0%
    deb3.payment_status_last_3_months = ['Current', 'Current', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb3);

// Debts for Jessica Williams (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (deb4:Debt {id: 'DEB04'})
SET deb4.type = 'Personal Loan',
    deb4.original_amount = 8000.0, // Adjusted for US personal loan
    deb4.remaining_balance = 6000.0,
    deb4.monthly_payment = 250.0,
    deb4.currency = 'USD',
    deb4.interest_rate = 0.12, // 12.0%
    deb4.payment_status_last_3_months = ['Current', '30-day late', 'Current']
MERGE (c)-[:OWES_DEBT]->(deb4);
MERGE (deb5:Debt {id: 'DEB05'})
SET deb5.type = 'Credit Card (B)',
    deb5.original_amount = 5000.0, // Adjusted for US credit card
    deb5.remaining_balance = 4500.0,
    deb5.monthly_payment = 200.0,
    deb5.currency = 'USD',
    deb5.interest_rate = 0.22, // 22.0%
    deb5.payment_status_last_3_months = ['Current', 'Current', '30-day late']
MERGE (c)-[:OWES_DEBT]->(deb5);



// Credit Report for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (cr1:CreditReport {id: 'CR01'})
SET cr1.score = 810,
    cr1.last_updated_date = '2025-05-15',
    cr1.number_of_inquiries_l6m = 1,
    cr1.open_accounts = 5,
    cr1.oldest_credit_line_years = 10
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr1);

// Credit Report for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (cr2:CreditReport {id: 'CR02'})
SET cr2.score = 730,
    cr2.last_updated_date = '2025-05-18',
    cr2.number_of_inquiries_l6m = 3,
    cr2.open_accounts = 8,
    cr2.oldest_credit_line_years = 15
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr2);

// Credit Report for Jessica Williams (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (cr3:CreditReport {id: 'CR03'})
SET cr3.score = 620,
    cr3.last_updated_date = '2025-05-16',
    cr3.number_of_inquiries_l6m = 5,
    cr3.open_accounts = 7,
    cr3.oldest_credit_line_years = 4
MERGE (c)-[:HAS_CREDIT_REPORT]->(cr3);



// Assets for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (ast1:Asset {id: 'AST01'})
SET ast1.type = 'Property', ast1.value = 800000.0, ast1.currency = 'USD', ast1.description = 'Primary Residence' // Adjusted for US property value
MERGE (c)-[:OWNS_ASSET]->(ast1);

// Assets for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (ast2:Asset {id: 'AST02'})
SET ast2.type = 'Property', ast2.value = 1000000.0, ast2.currency = 'USD', ast2.description = 'Primary Residence' // Adjusted for US property value
MERGE (c)-[:OWNS_ASSET]->(ast2);
MERGE (ast3:Asset {id: 'AST03'})
SET ast3.type = 'Vehicle', ast3.value = 35000.0, ast3.currency = 'USD', ast3.description = 'Car (Owned)' // Adjusted for US vehicle value
MERGE (c)-[:OWNS_ASSET]->(ast3);



// Goals for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P011'}) // Assuming P011 is Sarah, if not, adjust ID
MERGE (g1:SavingsGoal {id: 'G01'})
SET g1.name = 'Emergency Fund', g1.target_amount = 20000.0, g1.current_saved = 12000.0, g1.currency = 'USD', g1.target_date = '2026-06-30'
MERGE (c)-[:HAS_GOAL]->(g1);

// Goal for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (g2:SavingsGoal {id: 'G02'})
SET g2.name = 'Retirement', g2.target_amount = 1000000.0, g2.current_saved = 75000.0, g2.currency = 'USD', g2.target_date = '2055-12-31'
MERGE (c)-[:HAS_GOAL]->(g2);

// Goal for Jessica Williams (P003)
MATCH (c:Customer {id: 'P003'})
MERGE (g3:SavingsGoal {id: 'G03'})
SET g3.name = 'Emergency Fund', g3.target_amount = 5000.0, g3.current_saved = 500.0, g3.currency = 'USD', g3.target_date = '2026-06-30'
MERGE (c)-[:HAS_GOAL]->(g3);



// Portfolios for Sarah Johnson (P001)
MATCH (c:Customer {id: 'P001'})
MERGE (inv1:InvestmentPortfolio {id: 'INV01'})
SET inv1.name = 'Diversified', inv1.total_value = 50000.0, inv1.currency = 'USD', inv1.asset_mix = '60/30/10'
MERGE (c)-[:HAS_PORTFOLIO]->(inv1);

// Portfolio for David Miller (P002)
MATCH (c:Customer {id: 'P002'})
MERGE (inv2:InvestmentPortfolio {id: 'INV02'})
SET inv2.name = 'Growth', inv2.total_value = 75000.0, inv2.currency = 'USD', inv2.asset_mix = '80/10/10'
MERGE (c)-[:HAS_PORTFOLIO]->(inv2);



// UN001: Banker Interview Notes for Sarah Johnson (P001)
MATCH (entity:Customer {id: 'P001'})
MERGE (ud1:UnstructuredData {id: 'UN001'})
SET ud1.type = 'Interview Notes',
    ud1.source = 'Banker',
    ud1.capture_date = '2025-05-20'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud1);

// UN002: Applicant Email for Application APL01 (Sarah Johnson's loan)
MATCH (entity:Application {id: 'APL01'})
MERGE (ud2:UnstructuredData {id: 'UN002'})
SET ud2.type = 'Email',
    ud2.source = 'Applicant',
    ud2.capture_date = '2025-05-20'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud2);

// UN003: Banker Interview Notes for David Miller (P002)
MATCH (entity:Customer {id: 'P002'})
MERGE (ud3:UnstructuredData {id: 'UN003'})
SET ud3.type = 'Interview Notes',
    ud3.source = 'Banker',
    ud3.capture_date = '2025-05-22'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud3);

// UN004: External News for David Miller (P002)
MATCH (entity:Customer {id: 'P002'})
MERGE (ud4:UnstructuredData {id: 'UN004'})
SET ud4.type = 'External News',
    ud4.source = 'Economic Report',
    ud4.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud4);

// UN005: Banker Interview Notes for Jessica Williams (P003)
MATCH (entity:Customer {id: 'P003'})
MERGE (ud5:UnstructuredData {id: 'UN005'})
SET ud5.type = 'Interview Notes',
    ud5.source = 'Banker',
    ud5.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud5);

// UN006: Applicant Email for Application APL03 (Jessica Williams's Credit Card)
MATCH (entity:Application {id: 'APL03'})
MERGE (ud6:UnstructuredData {id: 'UN006'})
SET ud6.type = 'Email',
    ud6.source = 'Applicant',
    ud6.capture_date = '2025-05-21'
MERGE (entity)-[:HAS_UNSTRUCTURED_DATA]->(ud6);