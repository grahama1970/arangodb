# Test Results Report

**Generated**: 2025-05-26 07:12:36  
**Suite**: complete_test_suite  
**Total Duration**: 1.17s  

---


## Test Suite Summary

| Metric | Value |
|--------|-------|
| **Test Suite** | complete_test_suite |
| **Start Time** | 2025-05-26 07:12:35 |
| **Duration** | 1.17s |
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
| `overall` | cli | ❌ FAIL | 0.161s | Overall test suite execution failed | No DB queries |  |
| `overall` | core | ❌ FAIL | 0.175s | Overall test suite execution failed | No DB queries |  |
| `overall` | mcp | ❌ FAIL | 0.164s | Overall test suite execution failed | No DB queries |  |
| `overall` | qa_generation | ❌ FAIL | 0.165s | Overall test suite execution failed | No DB queries |  |
| `overall` | visualization | ❌ FAIL | 0.165s | Overall test suite execution failed | No DB queries |  |
| `overall` | integration | ❌ FAIL | 0.172s | Overall test suite execution failed | No DB queries |  |
| `overall` | unit | ❌ FAIL | 0.164s | Overall test suite execution failed | No DB queries |  |



## 🗄️ ArangoDB Summary

No database queries executed in this test suite.



## ❌ Failure Details (7 failures)

### overall - test_suite_execution

**Module**: cli  
**Status**: FAIL  
**Duration**: 0.161s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/tests/arangodb/cli/pytest.ini
  rootdir: /home/graham/workspace/experiments/arangodb/tests/arangodb/cli


```

---

### overall - test_suite_execution

**Module**: core  
**Status**: FAIL  
**Duration**: 0.175s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: mcp  
**Status**: FAIL  
**Duration**: 0.164s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: qa_generation  
**Status**: FAIL  
**Duration**: 0.165s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: visualization  
**Status**: FAIL  
**Duration**: 0.165s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: integration  
**Status**: FAIL  
**Duration**: 0.172s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---

### overall - test_suite_execution

**Module**: unit  
**Status**: FAIL  
**Duration**: 0.164s  

**Description**: Overall test suite execution failed  

**Error Message**:
```
Cannot read termcap database;
using dumb terminal settings.
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=test_output.json
  inifile: /home/graham/workspace/experiments/arangodb/pyproject.toml
  rootdir: /home/graham/workspace/experiments/arangodb


```

---



## 📊 Test Execution Timeline

| Test | Start Time | Duration | Status |
|------|------------|----------|--------|
| test_suite_execution | 07:12:35 | 0.161s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.175s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.164s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.165s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.165s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.172s | ❌ FAIL |
| test_suite_execution | 07:12:35 | 0.164s | ❌ FAIL |

---

**Report Generation**: Automated via ArangoDB Memory Bank Test Reporter  
**Compliance**: Task List Template Guide v2 Compatible  
**Non-Hallucinated Results**: All data sourced from actual test execution and ArangoDB queries  
