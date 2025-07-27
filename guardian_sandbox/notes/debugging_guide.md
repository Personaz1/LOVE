# ΔΣ Guardian - Debugging Guide

## System Diagnostics Tools

Guardian now has access to powerful debugging tools to help diagnose and fix system issues.

### Available Tools

#### 1. System Health Check
```tool_code
diagnose_system_health()
```
**What it does:**
- Checks all critical files for corruption
- Verifies API key configuration
- Validates sandbox directory
- Reports current model status

**Use when:**
- Users report system problems
- You need to verify everything is working
- After system changes or updates

#### 2. Error Summary
```tool_code
get_error_summary()
```
**What it does:**
- Shows recent model quota errors
- Lists system file issues
- Reports configuration problems
- Tracks error patterns over time

**Use when:**
- Users mention errors or problems
- You need to understand what's going wrong
- Before making system changes

#### 3. System Logs
```tool_code
get_system_logs(50)
```
**What it does:**
- Retrieves recent server logs
- Shows model switching events
- Displays error messages
- Includes recent model notes

**Use when:**
- Debugging specific issues
- Understanding system behavior
- Tracking user interactions

### Example Usage Scenarios

#### Scenario 1: User Reports "Something's Not Working"
```tool_code
diagnose_system_health()
```
Then check the results and explain what's working and what might need attention.

#### Scenario 2: API Quota Issues
```tool_code
get_error_summary()
```
This will show if models are hitting quota limits and which ones are available.

#### Scenario 3: Debugging Chat Problems
```tool_code
get_system_logs(20)
```
Check recent logs to see what happened during the problematic interaction.

### Best Practices

1. **Always check system health first** when users report issues
2. **Use error summary** to understand what's going wrong
3. **Check logs** for specific error details
4. **Explain findings** to users in simple terms
5. **Suggest solutions** based on what you find

### Remember

- These tools are for helping users, not just for show
- Always explain what you're checking and why
- Be proactive about system health
- Use the information to provide better support

---

*Created by ΔΣ Guardian for Meranda and Stepan*
*Date: 2025-07-27* 