# 🎯 How to Access Bid Management Features

## 📍 Where to Find It

### Method 1: From Tender Dashboard
1. Go to any tender: `http://localhost:3002/tenders/:id`
2. Click the **purple "Bid Management"** button in the top-right corner
3. You'll be taken to: `/tenders/:id/bid-management`

### Method 2: Direct URL
Navigate directly to: `http://localhost:3002/tenders/{TENDER_ID}/bid-management`

---

## 🚀 First Time Setup

### Step 1: Setup Backend (One-time)

```bash
cd backend

# 1. Update settings.py - Add to INSTALLED_APPS:
#    'apps.bid_actions',

# 2. Update urls.py - Add to urlpatterns:
#    path('api/bid-actions/', include('apps.bid_actions.urls')),

# 3. Run migrations
python manage.py makemigrations bid_actions
python manage.py migrate

# 4. Seed departments
python manage.py seed_departments

# 5. Start server
python manage.py runserver 8002
```

### Step 2: Generate Actions (First Time)

1. Open a tender
2. Click **"Bid Management"** button
3. Click the **blue "Generate Actions"** button in the header
4. Wait for actions to be generated (5-10 seconds)
5. Button will turn green showing "Backend Active"

---

## 🎨 Dashboard Features

### Tab 1: 📊 Overview
- **Bid Readiness Index** - Overall completion percentage
- **KPI Cards** - Total actions, win probability, financial exposure, critical items
- **Department Breakdown** - Visual cards showing progress per department

### Tab 2: 🏗 Action Items
- **Filter Actions** by:
  - Department (Civil, Mechanical, Electrical, MEP, Legal, Finance, etc.)
  - Priority (Critical, High, Medium, Low)
  - Status (Pending, In Progress, Review, Completed, Blocked)
- **Click status badge** to cycle through statuses
- **View details** - Risk score, financial exposure per item

### Tab 3: 📈 Analytics
- Win probability charts by scenario
- Risk heatmap by department
- Financial exposure breakdown
- Bid readiness checklist

### Tab 4: ⚡ Risk Cascade
- Cross-department risk propagation
- Shows how Civil delays → Mechanical → Electrical → Finance
- Predicted delay impact per department
- Risk amplification summary table

### Tab 5: 🕸 Dependency Graph
- Visual network graph showing action dependencies
- Node size = task count
- Edges show risk propagation paths
- Click nodes to see details

### Tab 6: ℹ️ How It Works
- Architecture explanation
- Feature documentation
- Department reference guide

### Tab 7: 🏛 Portfolio
- Multi-tender portfolio view
- Aggregated statistics across all tenders
- Value vs. readiness scatter plot
- Department risk heatmap

---

## 🔄 Using Backend vs Frontend Mode

### Frontend Mode (Default)
- Generates actions locally in browser
- Data lost on page refresh
- No database persistence
- **Good for:** Quick demos, testing

### Backend Mode (Recommended)
- Click **"Generate Actions"** button
- Actions stored in MySQL database
- Persists across sessions
- Status updates saved to backend
- Full analytics available
- **Good for:** Production use

### How to Switch
1. **Enable Backend**: Click "Generate Actions" button
2. **Regenerate**: Click again to regenerate all actions
3. Status updates will automatically sync to backend

---

## 🧪 Testing the Features

### Test Action Generation
```bash
# Test API directly
curl -X POST http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/generate-actions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Dashboard Data
```bash
curl http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/dashboard/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Action Items
```bash
curl http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/actions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 What Gets Generated

From a typical tender with BOQ, risks, and negotiations:

### Action Categories:
1. **BOQ Actions** - One per work item
   - Priority based on estimated cost
   - Financial exposure tracking
   - Department auto-classified

2. **Risk Actions** - One per identified risk
   - Priority from risk severity
   - Mitigation tasks
   - Department by risk type

3. **Negotiation Actions** - One per negotiation point
   - Priority by acceptance probability
   - Finance department
   - Counter-proposal tasks

4. **Eligibility Actions** - Based on tender requirements
   - Turnover certificates (Finance)
   - Similar work experience (Procurement)
   - Certifications (QA/QC)

5. **Standard Actions** - Common bid prep tasks
   - Schedule baseline (Planning)
   - Long lead items (Procurement)
   - HSE method statements (HSE)
   - Contract review (Legal)
   - Technical review (Civil)

### Expected Count:
- Small tender (₹10 Cr): ~20-30 actions
- Medium tender (₹50 Cr): ~50-80 actions
- Large tender (₹100+ Cr): ~100-150 actions

---

## 🎯 Key Workflows

### Daily Bid Preparation
1. Open Bid Management dashboard
2. Review **critical pending** items (red badges)
3. Update action statuses by clicking badges
4. Check **readiness index** - aim for 80%+
5. Review **risk cascade** for downstream impacts

### Executive Review
1. Go to **Analytics** tab
2. Review bid readiness score
3. Check department completion rates
4. Analyze financial exposure
5. Review win probability trends

### Cross-Department Coordination
1. Use **Dependency Graph** to see relationships
2. Check **Risk Cascade** for impact analysis
3. Filter actions by department
4. Assign tasks to team members

### Portfolio Management
1. Go to **Portfolio** tab
2. View all tenders at once
3. Compare readiness scores
4. Identify high-risk departments
5. Optimize resource allocation

---

## 🔧 Troubleshooting

### "Generate Actions" button doesn't work
- Check backend is running on port 8002
- Check you ran migrations: `python manage.py migrate`
- Check departments are seeded: `python manage.py seed_departments`
- Check browser console for errors

### No actions showing
- Click "Generate Actions" button first
- Wait 5-10 seconds for generation
- Check backend logs for errors
- Verify tender has BOQ/risks data

### Status updates not saving
- Make sure backend mode is enabled (button shows "Backend Active")
- Check authentication token is valid
- Check network tab for API errors

---

## 📱 Quick Access Checklist

✅ Backend setup complete (migrations + seed)
✅ Backend server running on port 8002
✅ Frontend server running on port 3002
✅ Tender has been analyzed (has BOQ/risks)
✅ Clicked "Generate Actions" in Bid Management
✅ Button shows "Backend Active" (green)

**You're ready to use all features!** 🎉

---

## 🆘 Need Help?

- Backend API docs: `backend/SETUP_INSTRUCTIONS.md`
- Implementation details: `IMPLEMENTATION_COMPLETE.md`
- Check Django admin: `http://localhost:8002/admin/bid_actions/`
