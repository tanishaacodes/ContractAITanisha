# Testing the Refactored Frontend

## ✅ What Was Changed

**GlobalRiskDashboard** was refactored to use shared components. Here's what changed:

### Before (Old Code - 393 lines)
```javascript
const [searchParams, setSearchParams] = useSearchParams();
const contractId = searchParams.get('contractId') || '';
const [loading, setLoading] = useState(true);
const [data, setData] = useState(null);
const [error, setError] = useState('');

const handleContractSelect = (id) => { ... }
const loadDashboardData = async () => { ... }

if (loading) return <div>...40 lines of loading UI...</div>;
if (error) return <div>...30 lines of error UI...</div>;
```

### After (New Code - 320 lines, 18% reduction)
```javascript
const { contractId, handleContractSelect } = useContractSelector();
const { loading, data, error, refetch } = useEnterpriseData(...);

if (loading) return <LoadingScreen message="..." />;
if (error) return <ErrorScreen error={error} onRetry={refetch} />;
```

## 🧪 How to Test

### 1. Start the Frontend

```bash
cd c:/Users/Admin/Desktop/contractbuild/frontend
npm run dev
```

The app should start on `http://localhost:5173`

### 2. Navigate to Global Risk Dashboard

Open your browser and go to:
```
http://localhost:5173/enterprise/risk-dashboard
```

Or however you access the GlobalRiskDashboard in your app.

### 3. Test Loading State

**What to check:**
- ✅ You should see a centered loading spinner with cyan color
- ✅ Text should say "Loading Enterprise Risk Intelligence..."
- ✅ Background should be dark gradient (slate-900 to slate-800)

**Expected behavior:**
- Loading screen appears for 1-3 seconds while data fetches
- Same look and feel as before

### 4. Test Error State

**How to test:**
1. Stop the Django backend (if running)
2. Refresh the page
3. You should see error screen

**What to check:**
- ✅ Red warning triangle icon appears
- ✅ Title says "Error Loading Dashboard"
- ✅ Error message is displayed
- ✅ "Retry" button is present and clickable
- ✅ Clicking "Retry" attempts to reload data

### 5. Test Normal Operation

**Start backend again:**
```bash
cd c:/Users/Admin/Desktop/contractbuild/backend
python manage.py runserver
```

**What to check:**
- ✅ Dashboard loads successfully with all data
- ✅ All charts and metrics display correctly
- ✅ Contract selector dropdown works
- ✅ Real-time commodity prices show
- ✅ Quick links navigate correctly

### 6. Test Contract Selection

**What to check:**
- ✅ Click contract selector dropdown
- ✅ Select a contract from the list
- ✅ URL updates with `?contractId=xxx`
- ✅ Dashboard reloads with contract-specific data
- ✅ Subtitle changes to "Contract-Specific Analysis"
- ✅ All metrics update correctly

**Test URL directly:**
```
http://localhost:5173/enterprise/risk-dashboard?contractId=123
```
- ✅ Should load with that contract pre-selected

### 7. Test Navigation

**From dashboard, click quick link modules:**
- ✅ Contract Knowledge Graph
- ✅ Supply Chain Risk
- ✅ Geo-Political Risk
- ✅ Commodity Forecast
- ✅ Monte Carlo VaR
- ✅ Portfolio VaR
- ✅ Insurance Policies

**What to check:**
- ✅ Each module loads without errors
- ✅ If a contractId was selected, it carries over to the new page
- ✅ Browser back button works correctly

## 🔍 Verify No Breaking Changes

### Compare Behavior

The refactored page should behave **EXACTLY THE SAME** as before:

1. **Loading time** - Same speed
2. **Error handling** - Same error messages
3. **Data display** - Identical charts and metrics
4. **Interactions** - All buttons/dropdowns work
5. **Navigation** - All links function properly
6. **URL params** - Contract selection via URL still works

### Check Console

Open browser DevTools (F12) and check:

```bash
# Should see NO errors
✅ No red errors in Console tab
✅ No failed network requests in Network tab
✅ Components render without warnings
```

If you see errors like:
```
Cannot find module '../../hooks/useContractSelector'
```

Then the import path is wrong. Verify the file structure:
```
frontend/src/
├── hooks/
│   ├── useContractSelector.js ✓
│   └── useEnterpriseData.js ✓
└── components/
    └── shared/
        ├── LoadingScreen.jsx ✓
        └── ErrorScreen.jsx ✓
```

## 🎯 Side-by-Side Comparison

Open two browser tabs:

1. **Original (if you kept backup):**
   - Any other enterprise page that hasn't been refactored yet
   - Compare loading/error states

2. **Refactored:**
   - GlobalRiskDashboard
   - Should look identical but use less code

## 📊 Performance Check

### Before
```javascript
// Multiple useState hooks
// Separate useEffect for each data fetch
// Manual loading/error handling
```

### After
```javascript
// Centralized state management
// Single useEffect in custom hook
// Reusable components with memoization
```

**Expected:** Same or slightly better performance due to code optimization.

## ✨ Testing Other Pages

Want to test the pattern on another page? Here's a quick template:

### Step 1: Pick a page
Example: `SupplyChainRiskDashboard.jsx`

### Step 2: Add imports
```javascript
import { useContractSelector } from '../../hooks/useContractSelector';
import { useEnterpriseData } from '../../hooks/useEnterpriseData';
import LoadingScreen from '../../components/shared/LoadingScreen';
import ErrorScreen from '../../components/shared/ErrorScreen';
```

### Step 3: Replace old pattern
```javascript
// OLD
const [searchParams, setSearchParams] = useSearchParams();
const contractId = searchParams.get('contractId') || '';
const [loading, setLoading] = useState(true);
// ... etc

// NEW
const { contractId, handleContractSelect } = useContractSelector();
const { loading, data, error, refetch } = useEnterpriseData(
  () => fetchMyData(contractId),
  [contractId]
);

if (loading) return <LoadingScreen message="Loading..." />;
if (error) return <ErrorScreen error={error} onRetry={refetch} />;
```

### Step 4: Test the same way
Follow steps 1-7 above for the new page.

## 🐛 Common Issues & Fixes

### Issue 1: "Cannot find module" error
**Fix:** Check file paths match exactly:
```javascript
// ✅ Correct
import { useContractSelector } from '../../hooks/useContractSelector';

// ❌ Wrong
import { useContractSelector } from '../hooks/useContractSelector';
```

### Issue 2: Blank screen on load
**Fix:** Check browser console for errors. Likely missing import or wrong prop name.

### Issue 3: Contract selector not working
**Fix:** Verify prop name is `onSelectContract` not `onSelect`:
```javascript
// ✅ Correct
<ContractSelector onSelectContract={handleContractSelect} />

// ❌ Wrong
<ContractSelector onSelect={handleContractSelect} />
```

### Issue 4: Data not loading
**Fix:** Check the data fetch function returns the data correctly:
```javascript
// ✅ Correct
const { data } = useEnterpriseData(
  async () => {
    const result = await api.getData();
    return result; // Must return!
  },
  [contractId]
);

// ❌ Wrong
const { data } = useEnterpriseData(
  async () => {
    await api.getData(); // Missing return!
  },
  [contractId]
);
```

## 📝 Verification Checklist

After refactoring any page:

- [ ] Page loads without console errors
- [ ] Loading state displays correctly
- [ ] Error state displays correctly
- [ ] Data fetches and displays correctly
- [ ] Contract selector works
- [ ] URL params work (contractId)
- [ ] Navigation works
- [ ] Browser back/forward work
- [ ] Refresh page works
- [ ] All interactive elements work
- [ ] No visual regressions (looks the same)
- [ ] No performance regressions (same speed)

## 🚀 Next Steps

Once GlobalRiskDashboard is verified working:

1. ✅ Test thoroughly (follow this guide)
2. ✅ Verify no breaking changes
3. ✅ Apply pattern to other pages one by one
4. ✅ Test each page after migration
5. ✅ Keep old code commented out until all tests pass
6. ✅ Remove old code once all pages migrated

## 📞 Need Help?

If something doesn't work:

1. Check browser console for errors
2. Verify all import paths are correct
3. Ensure all files were created in correct locations
4. Compare with the refactored example
5. Test in clean browser session (clear cache)

The refactored code should work identically to the original - if it doesn't, there's likely a small syntax issue or import path problem that's easy to fix!
