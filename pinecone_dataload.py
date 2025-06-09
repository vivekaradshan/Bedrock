import os
import pandas as pd
from pinecone import Pinecone, Index, ServerlessSpec, PodSpec
import boto3 # Import boto3 for AWS Bedrock
import json # For handling JSON payloads for Bedrock
from tqdm import tqdm # For progress bar
import time # For sleep during index deletion

# --- 1. Pinecone Configuration ---
# IMPORTANT: Replace with your actual Pinecone API Key and Environment
# You can get these from your Pinecone dashboard: app.pinecone.io
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") # Ensure you set this environment variable
PINECONE_ENVIRONMENT = "us-east-1" # e.g., "gcp-starter" or "us-east-1"
INDEX_NAME = "smart-saving-unstruct" # Name for your Pinecone index
DIMENSION = 1024 # This is the dimension of the 'all-MiniLM-L6-v2' model embeddings
METRIC = "cosine" # Similarity metric: 'cosine', 'euclidean', or 'dotproduct'

# --- 2. AWS Bedrock Configuration ---
# IMPORTANT: Configure your AWS credentials.
# boto3 will automatically look for credentials in environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# or in ~/.aws/credentials. Ensure your AWS region is also configured.
AWS_REGION = "us-east-1" # Or your desired AWS region where Bedrock is available
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# --- 3. Initialize Pinecone ---
try:
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    print(f"Successfully initialized Pinecone client.")
except Exception as e:
    print(f"Error initializing Pinecone: {e}")
    print("Please ensure your PINECONE_API_KEY and PINECONE_ENVIRONMENT are correct.")
    exit()

# --- 4. Drop and Recreate Pinecone Index ---
# This ensures a clean slate every time the script is run.
# if INDEX_NAME in pc.list_indexes():
# print(f"Index '{INDEX_NAME}' already exists. Deleting it for recreation...")
# try:
#     pc.delete_index(INDEX_NAME)
#     print(f"Index '{INDEX_NAME}' deleted successfully.")
#     time.sleep(30)  # Wait a few seconds to ensure deletion is processed
# except Exception as e:
#     print(f"Error deleting Pinecone index '{INDEX_NAME}': {e}")
#     # If deletion fails (e.g., due to permissions or a transient issue), exit or handle appropriately
#     exit()

print(f"Creating Pinecone index '{INDEX_NAME}' with dimension {DIMENSION}...")
try:
    # Using ServerlessSpec for older pinecone-client versions that require 'spec' argument.
    # Assumes your Pinecone environment is an AWS region for serverless.
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
    )
    print(f"Index '{INDEX_NAME}' created successfully.")
except Exception as e:
    # This block should ideally not be hit if delete_index was successful,
    # but kept for robustness against very rare timing issues or if
    # another process created it right after deletion.
    if "already exists" in str(e).lower() or "(409)" in str(e):
        print(f"Index '{INDEX_NAME}' already exists (encountered 409 Conflict during creation attempt).")
    else:
        print(f"Error creating Pinecone index: {e}")
        exit()

# Connect to the index
index = pc.Index(INDEX_NAME)

# --- 5. Initialize AWS Bedrock Client ---
try:
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION
    )
    print(f"Successfully initialized AWS Bedrock client in region {AWS_REGION}.")
except Exception as e:
    print(f"Error initializing AWS Bedrock client: {e}")
    print("Please ensure your AWS credentials and region are correctly configured.")
    exit()

# --- Embedding Function using Bedrock ---
def get_embedding(text):
    """Generates an embedding for the given text using AWS Bedrock Titan Embed Text v2."""
    if not text:
        return []
    
    body = json.dumps({"inputText": text})
    
    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=EMBEDDING_MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        embedding = response_body["embedding"]
        return embedding
    except Exception as e:
        print(f"Error invoking Bedrock model for text: '{text[:50]}...': {e}")
        return None # Return None to indicate failure

# --- 6. Unstructured Data Extraction (from the provided document) ---
# This data is directly extracted from your "unstructured_data_for_rag" immersive.
# In a real application, you'd load this from a database, files, or an API.
unstructured_data_records = [
    # --- Risk Analysis Agent Data ---
    {
        "Document ID": "JPMC_RN_001",
        "Source": "JPMC Banker Interview Notes",
        "Date": "2025-05-28",
        "Content": "Applicant (P001) seeking mortgage (L-JPMC-2025-001) for a primary residence in a growing suburban area of Dallas, TX. Confirmed stable employment at a Fortune 500 company for 10+ years. Expressed long-term commitment to the area. Discussed recent pay raise due to promotion. No discernible red flags or inconsistencies. Overall impression: strong, reliable borrower profile. Follow-up action: Verify employment & income via automated system.",
        "Metadata": {"customer_id": "P001", "application_id": "L-JPMC-2025-001", "banker_id": "B007", "sentiment": "positive", "risk_indicator": "low", "product_type": "mortgage", "location": "Dallas, TX"}
    },
    {
        "Document ID": "JPMC_RN_002",
        "Source": "JPMC Banker Interview Notes",
        "Date": "2025-06-03",
        "Content": "Applicant (P003) for new Chase Sapphire Preferred card. Admitted to recent unexpected medical expenses impacting cash flow. Mentioned having just moved to NYC for a new entry-level job and is adjusting to the higher cost of living. Expressed desire for a higher credit limit to consolidate existing small store card balances. Showed signs of stress regarding immediate financial flexibility. Needs careful review for potential debt cycle risk. Advised exploring credit counseling options.",
        "Metadata": {"customer_id": "P003", "application_id": "CC-JPMC-2025-003", "banker_id": "B012", "sentiment": "negative", "risk_indicator": "moderate_high", "red_flag_keywords": ["medical bills", "high cost of living", "debt consolidation", "new job"], "location": "NYC"}
    },
    {
        "Document ID": "JPMC_RN_003",
        "Source": "JPMC Banker Interview Notes",
        "Date": "2025-06-06",
        "Content": "Applicant (P004), a small business owner (restaurant supplies). Seeking $150K term loan for inventory expansion. Business revenue is strong year-over-year but cash reserves are tight due to recent equipment upgrades. Provided detailed projections and confirmed existing long-term contracts. Seems knowledgeable about market dynamics but needs capital infusion to capture growth. Risk factors: reliance on single large supplier, tight margins.",
        "Metadata": {"customer_id": "P004", "application_id": "SBL-JPMC-2025-004", "banker_id": "B005", "sentiment": "neutral-positive", "risk_indicator": "moderate", "product_type": "small_business_loan", "business_type": "restaurant_supplies"}
    },
    {
        "Document ID": "JPMC_RN_004",
        "Source": "JPMC Banker Interview Notes",
        "Date": "2025-06-07",
        "Content": "Applicant (P005), recent college graduate, first credit card. Starting entry-level position at tech firm. Limited credit history. Parents are JPMC high-net-worth clients, willing to be co-signers if needed. Applicant is keen to build credit responsibly. Low requested limit. Positive indicators: family banking relationship, secure first job. Needs cautious approval with potential for secured card or lower limit initially.",
        "Metadata": {"customer_id": "P005", "application_id": "CC-JPMC-2025-005", "banker_id": "B009", "sentiment": "positive", "risk_indicator": "low_history_moderate", "product_type": "credit_card", "customer_segment": "recent_grad"}
    },
    {
        "Document ID": "JPMC_EM_001",
        "Source": "Applicant Email",
        "Date": "2025-05-29",
        "Subject": "Follow-up on Mortgage Application - L-JPMC-2025-001 - Additional documentation",
        "Content": "Dear [Banker Name], Per your request, I've attached my last three years of tax returns and my current employment verification letter. I also included a copy of my recent bonus statement, which should further support my income stability. Thank you for your continued assistance with my home purchase.",
        "Metadata": {"customer_id": "P001", "application_id": "L-JPMC-2025-001", "document_type": "tax_returns", "income_support": "bonus"}
    },
    {
        "Document ID": "JPMC_EM_002",
        "Source": "Applicant Email",
        "Date": "2025-06-04",
        "Subject": "Regarding my Credit Card Application - CC-JPMC-2025-003 - Urgent",
        "Content": "Hi, I know my application might look challenging due to recent medical bills. My existing store card limits are maxed out, and I'm really struggling to manage minimum payments. I'm actively pursuing a second job at a local cafe, with interviews scheduled next week. I truly believe a new Chase card with a slightly higher limit would help me consolidate and simplify my payments. Please, any flexibility would be greatly appreciated.",
        "Metadata": {"customer_id": "P003", "application_id": "CC-JPMC-2025-003", "financial_distress": "true", "purpose": "debt_consolidation", "mitigation_attempt": "second_job"}
    },
    {
        "Document ID": "JPMC_EM_003",
        "Source": "Applicant Email",
        "Date": "2025-06-07",
        "Subject": "Follow-up on Small Business Loan Request - SBL-JPMC-2025-004 - Inventory Contract",
        "Content": "Hello, following our discussion, I've attached the signed contract with 'National Distributors' for Q3/Q4 bulk inventory. This solidifies the revenue projection I shared. Regarding the 'tight margins' mentioned, we've implemented new cost-saving measures on packaging, which should boost profitability by 1.5% next quarter. This loan is critical for capitalizing on upcoming holiday season demand.",
        "Metadata": {"customer_id": "P004", "application_id": "SBL-JPMC-2025-004", "business_update": "true", "mitigation_strategy": "cost_savings", "market_opportunity": "holiday_season"}
    },
    {
        "Document ID": "JPMC_POL_001",
        "Source": "JPMC Internal Risk Manual - Consumer Lending, Chapter 2: Credit Card Underwriting",
        "Date": "2024-11-15",
        "Content": "JPMorgan Chase's underwriting policy for new credit card applications emphasizes a holistic view of financial health. Applicants with a FICO score below 670 require escalated review. Specific attention must be paid to recent credit inquiries, debt-to-income ratio exceeding 40%, and patterns indicating reliance on new credit for debt consolidation. Geographical risk assessment is paramount, considering local economic indicators and employment rates in the applicant's primary residence area (e.g., impact of tech layoffs in California vs. stable manufacturing in Midwest).",
        "Metadata": {"policy_area": "consumer_lending", "product_type": "credit_card", "jpmc_specific": "true", "risk_threshold_FICO": 670, "risk_threshold_DTI": 0.40}
    },
    {
        "Document ID": "JPMC_POL_002",
        "Source": "JPMC Internal Risk Manual - Mortgage Lending, Appendix A: Economic Impact Adjustments",
        "Date": "2025-02-01",
        "Content": "Due to fluctuating interest rates and potential US economic slowdown in Q3 2025, mortgage underwriting criteria have been adjusted. For applicants with variable income, a conservative estimate based on the lowest quarterly earnings over the past 12 months should be used. For properties in areas with projected declines in home values (e.g., certain overheated markets in Florida/Arizona), LTV ratios will be capped at 75%. Stress testing for a 150-basis point interest rate increase is now mandatory for all new fixed-rate mortgage approvals. Documentation of property appraisal and local market reports required for such cases.",
        "Metadata": {"policy_area": "mortgage_lending", "economic_factor": "interest_rates, economic_slowdown", "us_economy_impact": "true", "LTV_cap": 0.75, "stress_test_bps": 150}
    },
    {
        "Document ID": "JPMC_POL_003",
        "Source": "JPMC Internal Risk Manual - Small Business Lending, Chapter 5: Industry Risk Profiles",
        "Date": "2024-10-01",
        "Content": "Small business loan applications are evaluated against industry-specific risk profiles. The restaurant supply sector, while generally stable, faces seasonality and vulnerability to food inflation. For loan amounts over $100K, a review of supplier concentration risk and diverse customer base is required. Businesses with less than 3 years operating history or inconsistent cash flow must provide enhanced collateral or a personal guarantee.",
        "Metadata": {"policy_area": "small_business_lending", "industry": "restaurant_supply", "risk_factors": ["seasonality", "inflation", "supplier_concentration"], "loan_threshold": 100000}
    },
    {
        "Document ID": "JPMC_POL_004",
        "Source": "JPMC Internal Fraud Prevention Guide, Section 3: Credit Application Fraud",
        "Date": "2025-01-20",
        "Content": "Common red flags for credit application fraud include: multiple recent applications across different banks, inconsistent personal information (address, employer) across documents, use of P.O. Box addresses, significant discrepancies between stated income and occupation, and refusal to provide additional verification documents. Any application flagged by the fraud detection system must be escalated to a dedicated fraud analyst team for manual review.",
        "Metadata": {"policy_area": "fraud_prevention", "fraud_type": "credit_application", "risk_indicators": ["multiple_applications", "inconsistent_info", "PO_Box", "income_discrepancy"]}
    },
    {
        "Document ID": "NEWS_JPMC_001",
        "Source": "Bloomberg News Report",
        "Date": "2025-06-05",
        "Headline": "US Economy Shows Mixed Signals: Persistent Inflation, Robust Job Growth",
        "Content": "Recent economic data for the United States indicates a bifurcated recovery. While non-farm payrolls continue to surprise on the upside, suggesting a strong labor market, core inflation remains stubbornly elevated, particularly in the services sector. The Federal Reserve's next move on interest rates is highly anticipated, with markets split between a pause and another 25-basis point hike. This mixed environment poses challenges for consumer lending institutions like JPMorgan Chase, balancing growth opportunities with default risks. Regional disparities in employment recovery are noted, especially in states reliant on manufacturing.",
        "Metadata": {"economy_focus": "US", "economic_indicator": "inflation, employment", "relevance_to_jpmc": "high", "fed_outlook": "uncertain", "regional_impact": "true"}
    },
    {
        "Document ID": "NEWS_JPMC_002",
        "Source": "Reuters - JPMC Q1 2025 Earnings Call Transcript Excerpt",
        "Date": "2025-04-12",
        "Content": "Jamie Dimon, CEO of JPMorgan Chase, stated during the Q1 2025 earnings call: 'Our consumer banking segment saw robust deposit growth, but credit card net charge-offs saw a slight uptick, aligning with broader industry trends. We are closely monitoring the subprime segment and proactively adjusting our risk models to reflect the evolving macroeconomic landscape in the US. Our investment banking pipeline remains strong, particularly in technology and healthcare sectors, despite a slower start to M&A activity in Q1.'",
        "Metadata": {"economy_focus": "US", "company": "JPMorgan Chase", "financial_performance": "earnings_call", "segment": "consumer_banking, credit_card, investment_banking", "risk_trend": "charge_offs", "sector_outlook": "tech, healthcare"}
    },
    {
        "Document ID": "NEWS_JPMC_003",
        "Source": "Wall Street Journal Report",
        "Date": "2025-05-20",
        "Headline": "US Restaurant Supply Chain Faces Increased Raw Material Costs",
        "Content": "Suppliers to the US restaurant industry are grappling with an unexpected surge in raw material costs, particularly for packaging and certain food commodities. This inflationary pressure is squeezing profit margins for distributors and could lead to increased demand for short-term working capital loans. Companies with long-term contracts and diversified client bases are better positioned, but smaller players may face liquidity challenges.",
        "Metadata": {"economy_focus": "US", "industry": "restaurant_supply", "economic_impact": "inflation", "business_loan_risk": "high"}
    },
    {
        "Document ID": "NEWS_JPMC_004",
        "Source": "FinCEN Advisory",
        "Date": "2025-06-01",
        "Headline": "FinCEN Issues Advisory on Emerging AI-Driven Financial Crime Risks",
        "Content": "The Financial Crimes Enforcement Network (FinCEN) has issued an advisory highlighting the growing threat of AI-driven financial crimes, including sophisticated identity theft and synthetic identity fraud targeting credit applications. Financial institutions, including major banks like JPMorgan Chase, are urged to enhance their fraud detection capabilities and report suspicious activity promptly. This could lead to increased scrutiny for new account openings and loan applications.",
        "Metadata": {"economy_focus": "US", "regulatory_body": "FinCEN", "risk_type": "financial_crime, fraud", "impact_on_banking": "operational_risk"}
    },
    # --- Saving Advisor Agent Data ---
    {
        "Document ID": "JPMC_ADVICE_001",
        "Source": "JPMorgan Chase Wealth Management Blog - Article",
        "Date": "2025-03-15",
        "Headline": "Navigating Volatility: Long-Term Saving Strategies for the US Market",
        "Content": "Even amidst US economic uncertainty, consistent, long-term saving remains paramount. For our clients, we emphasize diversifying across asset classes, leveraging tax-advantaged accounts like 401(k)s and IRAs, and regularly reviewing your financial plan. Consider dollar-cost averaging into equity markets to smooth out short-term fluctuations. Our advisors can help you identify JPMC investment products that align with your risk tolerance and time horizon.",
        "Metadata": {"topic": "long_term_saving", "economy_focus": "US", "jpmc_alignment": "high", "risk_level": "all", "strategy": "diversification, dollar_cost_averaging", "tax_advantaged": ["401k", "IRA"]}
    },
    {
        "Document ID": "JPMC_ADVICE_002",
        "Source": "J.P. Morgan Asset Management - Market Insights Report Excerpt",
        "Date": "2025-05-01",
        "Headline": "Mid-Year Outlook 2025: Opportunities in US Equities Amidst Inflation Concerns",
        "Content": "Our latest market insights suggest continued resilience in US corporate earnings, despite persistent inflation. While large-cap tech companies remain strong, we see emerging value in industrials and healthcare sectors. Investors should maintain a diversified portfolio but consider tactical overweight positions in sectors benefiting from structural growth trends. Bond yields are expected to remain attractive, offering income and diversification benefits. We recommend a staggered approach to new bond investments.",
        "Metadata": {"topic": "market_outlook", "economy_focus": "US", "asset_class_focus": ["equities", "bonds"], "sector_focus": ["industrials", "healthcare"], "jpmc_alignment": "true"}
    },
    {
        "Document ID": "JPMC_ADVICE_003",
        "Source": "JPMC Tax Planning Guide for Wealth Management Clients",
        "Date": "2025-02-10",
        "Headline": "Maximizing Tax Efficiency in Your Savings and Investments",
        "Content": "For US-based clients, tax-loss harvesting, contributing to Roth IRAs (if eligible), and utilizing 529 plans for education savings are key strategies. Consider the tax implications of capital gains and dividends when constructing your portfolio. JPMorgan Chase wealth advisors can help you structure your investments to minimize your tax burden while aligning with your financial goals.",
        "Metadata": {"topic": "tax_planning", "economy_focus": "US", "jpmc_alignment": "true", "strategy": ["tax_loss_harvesting", "Roth IRA", "529 plan"]}
    },
    {
        "Document ID": "JPMC_PROD_001",
        "Source": "Chase.com Product Page",
        "Date": "2025-01-01",
        "Product Name": "Chase Premier Savings Account",
        "Content": "The Chase Premier Savings Account offers competitive interest rates with tiered balances, rewarding higher deposits. Link it to your Chase checking account for seamless transfers. Features include FDIC insurance up to the maximum legal limit and access to Chase financial advisors for personalized planning. Ideal for mid-to-long term savings goals and building a substantial emergency fund. Available nationwide in the US, with easy online and mobile access.",
        "Metadata": {"product_type": "savings_account", "bank": "JPMorgan Chase", "interest_tiering": "true", "geography": "US", "features": ["FDIC_insured", "advisor_access", "online_access"]}
    },
    {
        "Document ID": "JPMC_PROD_002",
        "Source": "J.P. Morgan Asset Management - Fund Fact Sheet",
        "Date": "2025-05-01",
        "Product Name": "JPMorgan SmartRetirement Blend 2045 Fund",
        "Content": "A target-date fund designed for investors planning to retire around 2045. It invests in a diversified portfolio of underlying J.P. Morgan funds, gradually shifting from more aggressive equity-heavy allocations to more conservative fixed-income as the target date approaches. Aims for capital appreciation while managing risk for retirement income. Suitable for moderate-risk investors seeking a comprehensive, professionally managed retirement solution, specifically for US retirement accounts (e.g., 401k, IRA).",
        "Metadata": {"product_type": "mutual_fund", "fund_family": "J.P. Morgan", "target_date": "2045", "risk_level": "moderate", "investment_horizon": "long_term", "us_retirement_accounts": "true"}
    },
    {
        "Document ID": "JPMC_PROD_003",
        "Source": "J.P. Morgan Wealth Management - Services Overview",
        "Date": "2024-11-01",
        "Service Name": "Personalized Financial Planning & Advisory",
        "Content": "J.P. Morgan Wealth Management offers bespoke financial planning services for high-net-worth individuals and families. Our advisors assist with investment management, retirement planning, estate planning, and tax optimization strategies. We provide access to exclusive investment opportunities and research insights tailored to the US market. Minimum investable assets may apply.",
        "Metadata": {"service_type": "wealth_management", "bank": "J.P. Morgan", "client_segment": "high_net_worth", "services_offered": ["investment_management", "retirement_planning", "estate_planning", "tax_optimization"], "geography": "US"}
    },
    {
        "Document ID": "JPMC_TEST_001",
        "Source": "JPMC Customer Feedback Survey",
        "Date": "2025-04-20",
        "Customer ID": "P001",
        "Content": "My J.P. Morgan advisor was incredibly helpful in setting up my retirement plan. The online tools provided through Chase Mobile are fantastic for tracking my progress. I feel much more confident about my financial future thanks to their personalized advice and the SmartRetirement Fund recommendation. Living in the US, knowing my investments are aligned with the local market is a big plus.",
        "Metadata": {"customer_id": "P001", "sentiment": "positive", "feedback_type": "wealth_management_advice", "bank": "JPMorgan Chase", "product_mentioned": "SmartRetirement Fund"}
    },
    {
        "Document ID": "JPMC_TEST_002",
        "Source": "JPMC Client Review Portal",
        "Date": "2025-05-10",
        "Customer ID": "P002",
        "Content": "I've been with Chase Private Client for years, and their investment advice has been consistently solid. During the recent market dip, my advisor helped me rebalance my portfolio, and I've seen a good recovery. Their research on US small-cap opportunities was particularly valuable. The personalized service makes a real difference for a business owner like me.",
        "Metadata": {"customer_id": "P002", "sentiment": "positive", "feedback_type": "investment_advice", "bank": "JPMorgan Chase", "client_segment": "private_client", "market_condition": "dip_recovery"}
    },
    {
        "Document ID": "JPMC_TEST_003",
        "Source": "JPMC Customer Service Email (Complaint)",
        "Date": "2025-06-01",
        "Customer ID": "P003",
        "Content": "I'm frustrated with the fees on my savings account. I was expecting a higher interest rate based on online ads, but the minimum balance requirement makes it hard for me. As someone just starting out in NYC, every dollar counts. It feels like the products aren't tailored for people with lower balances. I need simpler, low-cost savings options.",
        "Metadata": {"customer_id": "P003", "sentiment": "negative", "feedback_type": "product_dissatisfaction", "bank": "JPMorgan Chase", "product_mentioned": "savings_account", "pain_point": "fees, minimum_balance", "location": "NYC"}
    }
]

# --- 7. Prepare Data for Upsert ---
# Create a list of dictionaries, where each dictionary is a vector.
# Pinecone requires vectors in the format: (id, vector_list, metadata_dict)
vectors_to_upsert = []
for record in tqdm(unstructured_data_records, desc="Generating embeddings"):
    doc_id = record["Document ID"]
    content = record["Content"]
    
    # Generate embedding using Bedrock
    embedding = get_embedding(content)
    if embedding is None:
        print(f"Skipping document {doc_id} due to embedding error.")
        continue

    # Prepare metadata - ensure it's JSON serializable
    metadata = record.get("Metadata", {})
    # Add other top-level fields to metadata for better filtering/context
    metadata["document_id"] = record["Document ID"]
    metadata["source"] = record["Source"]
    metadata["date"] = record["Date"]
    if "Headline" in record: # Add headline if present
        metadata["headline"] = record["Headline"]
    if "Subject" in record: # Add subject if present
        metadata["subject"] = record["Subject"] 
    metadata["original_content"] = content # Store original content for retrieval

    vectors_to_upsert.append((doc_id, embedding, metadata))

print(f"Prepared {len(vectors_to_upsert)} vectors for upsert.")

# --- 8. Upsert Vectors to Pinecone ---
BATCH_SIZE = 100 # Adjust batch size based on your Pinecone tier limits and network conditions

if vectors_to_upsert:
    try:
        for i in tqdm(range(0, len(vectors_to_upsert), BATCH_SIZE), desc="Upserting to Pinecone"):
            batch = vectors_to_upsert[i : i + BATCH_SIZE]
            index.upsert(vectors=batch)
        print(f"Successfully upserted {len(vectors_to_upsert)} vectors to Pinecone index '{INDEX_NAME}'.")
    except Exception as e:
        print(f"Error during upsert to Pinecone: {e}")
else:
    print("No vectors to upsert.")


