# Test Results Report

**Generated**: 2025-05-26 11:26:29  
**Suite**: complete_test_suite  
**Total Duration**: 1.34s  

---


## Test Suite Summary

| Metric | Value |
|--------|-------|
| **Test Suite** | complete_test_suite |
| **Start Time** | 2025-05-26 11:26:27 |
| **Duration** | 1.34s |
| **Total Tests** | 7 |
| **✅ Passed** | 0 |
| **❌ Failed** | 7 |
| **⚠️ Errors** | 0 |
| **⏭️ Skipped** | 0 |
| **Success Rate** | 0.0% |
| **Status** | ❌ FAILURES DETECTED |



## Detailed Test Results

| Test ID | Module | Status | Duration | Description | ArangoDB Results | Assertion Details |
|---------|--------|--------|----------|-------------|------------------|-------------------|
| `overall` | cli | ❌ FAIL | 0.203s | Overall test suite execution failed | No DB queries |  |
| `overall` | core | ❌ FAIL | 0.192s | Overall test suite execution failed | No DB queries |  |
| `overall` | mcp | ❌ FAIL | 0.190s | Overall test suite execution failed | No DB queries |  |
| `overall` | qa_generation | ❌ FAIL | 0.185s | Overall test suite execution failed | No DB queries |  |
| `overall` | visualization | ❌ FAIL | 0.189s | Overall test suite execution failed | No DB queries |  |
| `overall` | integration | ❌ FAIL | 0.190s | Overall test suite execution failed | No DB queries |  |
| `overall` | unit | ❌ FAIL | 0.189s | Overall test suite execution failed | No DB queries |  |



## 🗄️ ArangoDB Summary

No database queries executed in this test suite.



## ❌ Failure Details (7 failures)

### overall - test_suite_execution

**Module**: cli  
**Status**: FAIL  
**Duration**: 0.203s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/tests/arangodb/cli/pytest.ini
  rootdir: /home/graham/workspace/experiments/arangodb/tests/arangodb/cli


```

---

### overall - test_suite_execution

**Module**: core  
**Status**: FAIL  
**Duration**: 0.192s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: mcp  
**Status**: FAIL  
**Duration**: 0.190s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: qa_generation  
**Status**: FAIL  
**Duration**: 0.185s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: visualization  
**Status**: FAIL  
**Duration**: 0.189s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: integration  
**Status**: FAIL  
**Duration**: 0.190s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: unit  
**Status**: FAIL  
**Duration**: 0.189s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---



## 📊 Test Execution Timeline

| Test | Start Time | Duration | Status |
|------|------------|----------|--------|
| test_suite_execution | 11:26:27 | 0.203s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.192s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.190s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.185s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.189s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.190s | ❌ FAIL |
| test_suite_execution | 11:26:27 | 0.189s | ❌ FAIL |

---

**Report Generation**: Automated via ArangoDB Memory Bank Test Reporter  
**Compliance**: Task List Template Guide v2 Compatible  
**Non-Hallucinated Results**: All data sourced from actual test execution and ArangoDB queries  
