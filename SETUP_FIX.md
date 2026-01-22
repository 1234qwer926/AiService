# SETUP Stage Advancement Fix

## Problem
The Agent Monica 007 was not advancing from the SETUP stage to the RCPA stage after the user provided their information. The conversation flow was stuck in an infinite loop asking for the same information.

## Root Cause
In `monica_service.py`, the `_extract_setup_fields()` method (line 129) was only checking for the division name **"nucleus"**, but the user said **"stimulus division"**. 

Since the `division` field was never being set, the `_should_advance()` method's condition was never satisfied:

```python
def _should_advance(self, session: MonicaSession) -> bool:
    stage = session.current_stage
    
    if stage == "SETUP":
        return (
            session.user_name
            and session.user_role
            and session.headquarter
            and session.division  # ❌ This was always None!
        )
```

## Solution
Updated the `_extract_setup_fields()` method in [`monica_service.py`](file:///home/kalyan/Desktop/SalesRepAgent/monica_service.py) to:

1. **Added "stimulus" detection** - Now recognizes both "Nucleus" and "Stimulus" divisions
2. **Improved extraction logic** - More flexible pattern matching for all fields (name, role, HQ, division)
3. **Better name extraction** - Can now extract names from phrases like "this is pavan" or "i am pavan"

### Key Changes

```python
# Extract division - FIXED to include "stimulus"
if not session.division:
    if "nucleus" in t:
        session.division = "Nucleus"
    elif "stimulus" in t:  # ✅ NEW: Now detects "stimulus"
        session.division = "Stimulus"
    elif "division" in t:
        # Try to extract division name
        words = t.split()
        for i, word in enumerate(words):
            if word == "division" and i > 0:
                session.division = words[i - 1].capitalize()
                break
```

## Verification
Ran automated test with the exact user input:
- **Input**: "this is pavan iam working in hq india and in stimulus division and my role is bm"
- **Result**: ✅ SUCCESS! Agent now correctly:
  1. Extracts all fields (name: Pavan, role: BM, HQ: India, division: Stimulus)
  2. Advances from SETUP to RCPA stage
  3. Transitions to the chemist persona

## Testing
You can test the fix yourself:
```bash
python3 test_setup_fix.py
```

Or test manually in the UI:
1. Start a new session
2. Say: "this is pavan iam working in hq india and in stimulus division and my role is bm"
3. Confirm with: "yeah"
4. The agent should now advance to RCPA stage and act as a chemist

## Files Modified
- [`monica_service.py`](file:///home/kalyan/Desktop/SalesRepAgent/monica_service.py#L117-L167) - Fixed `_extract_setup_fields()` method

## Additional Improvements
The enhanced extraction logic now handles:
- Multiple division names (Nucleus, Stimulus, or custom)
- Flexible name extraction from various phrase patterns
- Better role detection (BM/PL)
- More robust HQ location extraction
