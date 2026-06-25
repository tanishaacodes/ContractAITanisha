# Real Vendor Bid Data Import Guide

## ✅ Demo Data Cleared

All demo/test data has been removed. You're now ready to import **real vendor bids**.

---

## 📋 THREE WAYS TO IMPORT REAL DATA

### **Method 1: Via Dashboard UI (Easiest)** ⭐

1. **Start servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python manage.py runserver 8002

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. **Navigate to:**
   ```
   http://localhost:5173/tenders/38/buyer
   ```
   (Replace `38` with your actual tender ID)

3. **Click "Submit Bid" tab**

4. **Add vendors and submit bids manually**

---

### **Method 2: Import from CSV (Recommended for Bulk)** 📊

1. **Edit the CSV template:** [real_bids_template.csv](real_bids_template.csv)

   ```csv
   vendor_name,registration_number,financial_rating,past_performance_score,round_number,total_price,technical_score,commercial_score,legal_risk_score,delay_probability,deviation_score,notes
   ABC Construction Ltd,REG-2024-001,0.85,0.78,1,5500000000,85.5,78.2,0.25,0.15,0.18,Initial bid
   ```

   **Column Guide:**
   - `vendor_name` - Full company name
   - `registration_number` - Company registration/GST number
   - `financial_rating` - 0.0 to 1.0 (e.g., 0.85 = 85%)
   - `past_performance_score` - 0.0 to 1.0
   - `round_number` - 1, 2, 3, etc.
   - `total_price` - Total bid amount in rupees (e.g., 5500000000 = ₹550 Cr)
   - `technical_score` - 0 to 100
   - `commercial_score` - 0 to 100
   - `legal_risk_score` - 0.0 to 1.0 (higher = more risky)
   - `delay_probability` - 0.0 to 1.0 (0.15 = 15% chance of delay)
   - `deviation_score` - 0.0 to 1.0 (contract deviation from tender)
   - `notes` - Any additional comments

2. **Run import script:**
   ```bash
   cd backend
   python import_from_csv.py 38 your_real_bids.csv
   ```

3. **View results:**
   ```
   http://localhost:5173/tenders/38/buyer
   ```

---

### **Method 3: Python Script (Advanced)** 🐍

1. **Edit:** [import_real_bids.py](import_real_bids.py)

2. **Customize the data arrays** (vendors, bids, clauses)

3. **Run:**
   ```bash
   cd backend
   python import_real_bids.py
   ```

---

## 📊 DATA GUIDELINES

### **Vendor Information:**
- **Financial Rating:** Based on credit score, cash flow, balance sheet strength
  - `0.9-1.0` = Excellent (AAA rated)
  - `0.7-0.9` = Good (AA/A rated)
  - `0.5-0.7` = Fair (BBB rated)
  - `<0.5` = Risky (BB or lower)

- **Past Performance Score:** Based on historical project delivery
  - `0.9-1.0` = Excellent track record
  - `0.7-0.9` = Good delivery history
  - `0.5-0.7` = Mixed performance
  - `<0.5` = Poor track record

### **Bid Information:**
- **Technical Score:** Evaluated based on:
  - Team qualifications
  - Equipment availability
  - Project methodology
  - Safety record
  - Technical compliance

- **Commercial Score:** Evaluated based on:
  - Price competitiveness
  - Payment terms
  - Warranty/guarantees
  - Commercial compliance
  - Value engineering

- **Legal Risk Score:** Based on:
  - Contract deviation severity
  - Non-compliant clauses
  - Liability limitations
  - Unfavorable terms
  - Higher = More risky

- **Delay Probability:** AI-predicted likelihood of project delays
  - Based on vendor history
  - Project complexity
  - Resource availability
  - Market conditions

---

## 🎯 TYPICAL WORKFLOW

### **Single Round Bidding:**
1. Import all vendors with their Round 1 bids
2. Review dashboard → Winner Recommendation tab
3. Make award decision

### **Multi-Round Bidding (BAFO):**
1. Import Round 1 bids
2. Review competitive positioning
3. Shortlist vendors
4. Request BAFO (Best and Final Offer)
5. Import Round 2 bids
6. Compare bid evolution
7. Detect collusion patterns
8. Make final award decision

---

## 📁 EXAMPLE: Real Project Data

**Project:** Metro Station Construction Contract
**Estimated Value:** ₹500 Crores
**Timeline:** 24 months

```csv
vendor_name,registration_number,financial_rating,past_performance_score,round_number,total_price,technical_score,commercial_score,legal_risk_score,delay_probability,deviation_score,notes
Larsen & Toubro Ltd,L&T-MUM-001,0.95,0.92,1,5250000000,92.5,88.0,0.08,0.05,0.03,Premium bidder - metro experience
Shapoorji Pallonji,SP-MUM-002,0.88,0.85,1,4980000000,89.0,85.5,0.12,0.08,0.08,Competitive pricing
NCC Limited,NCC-HYD-003,0.82,0.78,1,4750000000,85.5,82.0,0.18,0.12,0.15,Lowest L1 bidder
Afcons Infrastructure,AFC-MUM-004,0.85,0.81,1,5100000000,87.0,84.0,0.15,0.10,0.12,Mid-range bid
```

---

## 🔄 UPDATE EXISTING BIDS

To update a bid:
1. Keep same `vendor_name` and `round_number`
2. Change other values
3. Re-run import script
4. The system will **update** instead of creating duplicates

---

## 🗑️ CLEAR DATA (Start Fresh)

```bash
mysql -u root -p1111 contractai_db -e "DELETE FROM buyer_vendor_clause; DELETE FROM buyer_vendor_bid; DELETE FROM buyer_vendor;"
```

---

## 📞 SUPPORT

- **Dashboard:** http://localhost:5173/tenders/{TENDER_ID}/buyer
- **API Docs:** http://localhost:8002/api/tenders/swagger/
- **Backend:** Django admin at http://localhost:8002/admin/

---

## 🚀 NEXT STEPS

After importing real data:

1. ✅ View **Competitive Positioning** - See price gaps
2. ✅ Check **Bid Evolution** - Track round-to-round changes
3. ✅ Get **AI Winner Recommendation** - Multi-factor ranking
4. ✅ Run **Collusion Detection** - Identify suspicious patterns
5. ✅ Review **Legal Heatmap** - Clause-level risk analysis
6. ✅ Make **Award Decision** based on data-driven insights

Your buyer-side procurement intelligence platform is ready! 🎯
