# Product Requirements Document (PRD)
# Internal Testing Platform

---

## 1. Document Information

| Field | Value |
|-------|-------|
| **Document Title** | Internal Testing Platform - PRD |
| **Version** | 1.0 |
| **Date** | January 3, 2026 |
| **Status** | Final |
| **Owner** | Testing Platform Team |
| **Approvals** | Pending |

---

## 2. Executive Summary

### 2.1 Project Overview

The **Internal Testing Platform** is a configuration-driven API sanity testing framework designed to validate insurance policy purchase flows across multiple environments (DEV/QA vs Staging). The platform automates end-to-end testing of insurance products by simulating the complete purchase journey - from application submission to policy verification in both Admin and Customer portals.

### 2.2 Business Problem

- Manual testing of insurance APIs across multiple environments is time-consuming and error-prone
- No automated way to compare API responses between DEV/QA and Staging environments
- Testing coverage varies across different product categories, products, and plans
- Lack of real-time visibility into test execution status
- No automated reporting or insights generation for test results

### 2.3 Solution

A web-based testing platform that:
- Configures and executes automated API tests for all insurance product combinations
- Compares Target (DEV/QA) vs Staging environment responses intelligently
- Provides real-time execution visibility through tab-based UI
- Generates AI-powered reports using Hugging Face LLM
- Stores test results for audit and historical analysis

### 2.4 Key Differentiators

- **Configuration-Driven**: Add new products/plans via config file without code changes
- **Sequential Execution**: Ensures predictable, debuggable test runs
- **Intelligent Comparison**: Focuses on business-critical fields, ignores timestamps/metadata
- **Session-Based Architecture**: Isolated test runs with complete audit trail
- **AI-Powered Reports**: Automated insights and recommendations using LLM

---

## 3. Product Vision & Goals

### 3.1 Vision Statement

"To provide a scalable, automated testing platform that ensures insurance API consistency and correctness across development environments through intelligent comparison and AI-powered insights."

### 3.2 Primary Objectives

1. **Automate API Testing**: Eliminate manual testing of insurance purchase flows
2. **Environment Consistency**: Ensure DEV/QA behavior matches Staging
3. **Full Coverage**: Test all Category → Product → Plan combinations
4. **Real-Time Visibility**: Provide instant feedback on test execution
5. **Intelligent Reporting**: Generate actionable insights using AI

### 3.3 Success Metrics

- **Time Savings**: Reduce testing time by 80% compared to manual testing
- **Coverage**: 100% of product combinations tested automatically
- **Bug Detection**: Catch API inconsistencies before production deployment
- **Usability**: Complete test setup and execution in < 5 minutes
- **Reliability**: 95%+ successful test executions

---

## 4. Business Logic / Flow

### 4.1 Insurance Product Hierarchy

```
Insurance Products
├── Categories
│   ├── MV4 (Car)
│   │   └── Products (Brand)
│   │       ├── TOKIO_MARINE
│   │       │   └── Plans
│   │       │       ├── COMPREHENSIVE
│   │       │       └── TOTAL_LOSS
│   │       └── SOMPO
│   │           └── Plans
│   │               ├── COMPREHENSIVE
│   │               └── THIRD_PARTY
│   ├── MV2 (Motorcycle)
│   ├── PET
│   ├── PA (Personal Accident)
│   └── TRAVEL
│       ├── SOMPO
│       │   └── Plans
│       │       ├── TRAVEL_COMPREHENSIVE
│       │       └── TRAVEL_BASIC
│       └── ZURICH
│           └── Plans
│               ├── TRAVEL_PREMIUM
│               └── TRAVEL_STANDARD
```

**Key Identifiers:**
- `category`: MV4, MV2, PET, PA, TRAVEL
- `product_id`: TOKIO_MARINE, SOMPO, ZURICH
- `plan_id`: COMPREHENSIVE, TOTAL_LOSS, etc.

**Critical Combination:** `category + product_id + plan_id` is used throughout the system for API calls and business logic.

### 4.2 Purchase Flow APIs (7 Steps per Combination)

| Step | API Name | Purpose | Response Data |
|------|----------|---------|---------------|
| 1 | **Application Submit** | Submit insurance application | `application_id`, status, premium |
| 2 | **Apply Coupon** | Apply voucher (if applicable) | `discount_applied`, `new_amount` |
| 3 | **Payment Checkout** | Process payment | `payment_id`, `transaction_ref`, status |
| 4 | **Admin Policy List** | Get policies from Admin Portal | `policy_ids[]` |
| 5 | **Admin Policy Details** | Get policy details from Admin | `policy_number`, premium, coverage, status |
| 6 | **Customer Policy List** | Get policies from Customer Portal | `policy_ids[]` |
| 7 | **Customer Policy Details** | Get policy details from Customer | `start_date`, `end_date`, benefits |

### 4.3 Execution Flow

```
User starts session
    ↓
User selects category(ies) (one OR all)
    ↓
User provides auth tokens (optional)
    ↓
For each Category → Product → Plan combination:
    For each environment (DEV, QA, STAGING):
        Execute 7 APIs (skip Admin/Customer APIs if no token)
        Store results
    ↓
    Compare Target vs Staging responses
    Generate tab report
    ↓ (sequential - one at a time)
Next combination
    ↓
All combinations complete
    ↓
Generate execution report
    ↓
Mark session as complete
```

### 4.4 Comparison Strategy

**Compared Environments:**
- Target: DEV or QA
- Reference: STAGING

**Comparison Rules:**
- Do NOT store response schemas
- Ignore: timestamps, `created_at`, `updated_at`, environment-specific metadata
- Focus on: policy-related data, business-critical fields
- Use `deepdiff` library for intelligent comparison

**Severity Levels:**
- **Critical**: `policy_number`, `policy_id`, `premium`, `coverage`, `status`
- **Warning**: Type changes, added/removed fields
- **Info**: Other value changes

---

## 5. Functional Requirements

### 5.1 Session Management

| Requirement | Description | Priority |
|-------------|-------------|----------|
| SM-1 | User must create a session with a user name | P0 |
| SM-2 | Session ID generated as `sess_YYYYMMDD_HHMMSS` | P0 |
| SM-3 | Session stores: ID, user name, created_at, status, execution list | P0 |
| SM-4 | System maintains session list for audit | P0 |
| SM-5 | Maximum 5 sessions stored (FIFO cleanup) | P0 |
| SM-6 | Session status: active, completed, failed | P0 |
| SM-7 | Each session supports up to 10 executions (max 50 total) | P0 |

### 5.2 Configuration Management

| Requirement | Description | Priority |
|-------------|-------------|----------|
| CFG-1 | Central config file `config/products.json` defines hierarchy | P0 |
| CFG-2 | System loads categories, products, plans from config | P0 |
| CFG-3 | Adding new product/plan requires only config update | P0 |
| CFG-4 | System supports 5 categories: MV4, MV2, PET, PA, TRAVEL | P0 |
| CFG-5 | Each category has multiple products with unique `product_id` | P0 |
| CFG-6 | Each product has multiple plans with unique `plan_id` | P0 |

### 5.3 Test Execution

| Requirement | Description | Priority |
|-------------|-------------|----------|
| EX-1 | User selects: one category OR all categories (no partial) | P0 |
| EX-2 | User provides optional Admin and Customer auth tokens | P0 |
| EX-3 | Missing auth token skips related APIs | P0 |
| EX-4 | Execution is sequential (one Category+Product+Plan at a time) | P0 |
| EX-5 | Execution ID: `{session_name}_{YYYYMMDD}_{HHMMSS}` | P0 |
| EX-6 | Failed execution does NOT stop remaining executions | P0 |
| EX-7 | Failed executions are marked for identification | P0 |
| EX-8 | Execution status: in_progress, completed, failed | P0 |
| EX-9 | Each execution tests 7 APIs per environment | P0 |
| EX-10 | Environments tested: DEV, QA, STAGING | P0 |

### 5.4 API Execution

| Requirement | Description | Priority |
|-------------|-------------|----------|
| API-1 | Execute Application Submit API | P0 |
| API-2 | Execute Apply Coupon API (if voucher applicable) | P0 |
| API-3 | Execute Payment Checkout API | P0 |
| API-4 | Execute Admin Policy List API (if token provided) | P0 |
| API-5 | Execute Admin Policy Details API (if token provided) | P0 |
| API-6 | Execute Customer Policy List API (if token provided) | P0 |
| API-7 | Execute Customer Policy Details API (if token provided) | P0 |
| API-8 | Capture: endpoint, request payload, response, status code, execution time | P0 |
| API-9 | Capture errors with context | P0 |
| API-10 | Current scope: Dummy/mock responses only | P0 |

### 5.5 Response Comparison

| Requirement | Description | Priority |
|-------------|-------------|----------|
| CMP-1 | Compare Target (DEV/QA) vs Staging responses | P0 |
| CMP-2 | Use deepdiff library for intelligent comparison | P0 |
| CMP-3 | Ignore: timestamps, environment metadata | P0 |
| CMP-4 | Flag differences with severity: critical, warning, info | P0 |
| CMP-5 | Store comparison results with field paths and values | P0 |
| CMP-6 | Generate comparison summary (count by severity) | P0 |

### 5.6 Reporting

| Requirement | Description | Priority |
|-------------|-------------|----------|
| RPT-1 | Generate tab summary after each Category+Product+Plan completes | P0 |
| RPT-2 | Generate execution report after all combinations complete | P0 |
| RPT-3 | Tab summary includes: status, API breakdown, issues count | P0 |
| RPT-4 | Execution report includes: overall status, critical issues, recommendations | P0 |
| RPT-5 | Current scope: Placeholder for LLM integration (future) | P1 |
| RPT-6 | Future: Use Hugging Face LLM for intelligent insights | P1 |

### 5.7 Storage & Persistence

| Requirement | Description | Priority |
|-------------|-------------|----------|
| STO-1 | Store data in JSON files | P0 |
| STO-2 | Storage structure: sessions/, session_data/, executions/ | P0 |
| STO-3 | Session list stored in `storage/sessions/session_list.json` | P0 |
| STO-4 | Session data stored in `storage/session_data/session_{id}.json` | P0 |
| STO-5 | Execution results stored in `storage/executions/execution_{id}.json` | P0 |
| STO-6 | Max 5 sessions (FIFO cleanup when exceeded) | P0 |
| STO-7 | Max 10 executions per session (FIFO cleanup) | P0 |
| STO-8 | Auth tokens NOT persisted (only passed during execution) | P0 |

### 5.8 Real-Time Progress

| Requirement | Description | Priority |
|-------------|-------------|----------|
| RT-1 | Frontend polls for progress updates | P0 |
| RT-2 | Polling interval: 3 seconds (configurable) | P0 |
| RT-3 | API endpoint: GET /api/execution/status/{session_id} | P0 |
| RT-4 | API endpoint: GET /api/execution/tabs/{session_id} | P0 |
| RT-5 | API endpoint: GET /api/execution/progress/{session_id}/{tab_id} | P0 |
| RT-6 | Response includes: overall status, completed count, failed count | P0 |

### 5.9 User Interface

| Requirement | Description | Priority |
|-------------|-------------|----------|
| UI-1 | Landing page collects session name | P0 |
| UI-2 | Configuration page: select category(ies), enter auth tokens | P0 |
| UI-3 | Execution view: tab-based interface per Category+Product+Plan | P0 |
| UI-4 | Tab shows: API status, progress, completed/pending APIs | P0 |
| UI-5 | Click API to view details and Target vs Stage comparison | P0 |
| UI-6 | Comparison view: side-by-side responses, highlighted differences | P0 |
| UI-7 | History page: list all sessions (audit view) | P0 |

### 5.10 API Endpoints

| Requirement | Description | Priority |
|-------------|-------------|----------|
| EP-1 | POST /api/session/create - Create new session | P0 |
| EP-2 | GET /api/session/{id} - Get session details | P0 |
| EP-3 | GET /api/session/list - List all sessions | P0 |
| EP-4 | GET /api/config/categories - Get all categories | P0 |
| EP-5 | GET /api/config/products/{category} - Get products for category | P0 |
| EP-6 | GET /api/config/plans/{category}/{product} - Get plans | P0 |
| EP-7 | GET /api/config/full - Get full hierarchy | P0 |
| EP-8 | POST /api/execution/start - Start execution | P0 |
| EP-9 | GET /api/execution/status/{session_id} - Get overall status | P0 |
| EP-10 | GET /api/execution/tabs/{session_id} - Get all tabs | P0 |
| EP-11 | GET /api/execution/progress/{session_id}/{tab_id} - Get tab progress | P0 |
| EP-12 | GET /api/execution/{session_id}/api-call/{call_id} - Get API details | P0 |
| EP-13 | GET /api/execution/{session_id}/comparison/{call_id} - Get comparison | P0 |
| EP-14 | GET /api/reports/session/{session_id} - Get session report | P0 |
| EP-15 | GET /api/reports/execution/{execution_id} - Get execution report | P0 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Requirement | Target |
|-------------|--------|
| NFR-PERF-1 | Session creation < 500ms |
| NFR-PERF-2 | Execution start < 1s (before background processing begins) |
| NFR-PERF-3 | Progress poll response < 200ms |
| NFR-PERF-4 | Comparison generation < 500ms per API call |
| NFR-PERF-5 | Support 5 concurrent sessions |
| NFR-PERF-6 | Total execution time: < 10 minutes for all categories (dummy APIs) |

### 6.2 Reliability & Availability

| Requirement | Target |
|-------------|--------|
| NFR-REL-1 | System uptime: 99%+ (internal tool) |
| NFR-REL-2 | No data loss during execution (atomic JSON writes) |
| NFR-REL-3 | Continue execution on individual API failures |
| NFR-REL-4 | Graceful handling of config file errors |
| NFR-REL-5 | Proper error logging for debugging |

### 6.3 Scalability

| Requirement | Target |
|-------------|--------|
| NFR-SCAL-1 | Support up to 5 concurrent sessions |
| NFR-SCAL-2 | Easy to upgrade from sequential to parallel execution |
| NFR-SCAL-3 | Config-driven: no code changes for new products |
| NFR-SCAL-4 | Storage cleanup automatic (FIFO) |

### 6.4 Usability

| Requirement | Target |
|-------------|--------|
| NFR-USE-1 | Complete test setup in < 5 minutes |
| NFR-USE-2 | Clear error messages and status indicators |
| NFR-USE-3 | Intuitive UI with minimal training needed |
| NFR-USE-4 | Real-time progress updates (3s polling) |

### 6.5 Security

| Requirement | Target |
|-------------|--------|
| NFR-SEC-1 | Auth tokens NOT persisted (passed only during execution) |
| NFR-SEC-2 | No secrets logged (passwords, tokens, API keys) |
| NFR-SEC-3 | No PII in logs (customer details) |
| NFR-SEC-4 | Environment variables for sensitive config |

### 6.6 Maintainability

| Requirement | Target |
|-------------|--------|
| NFR-MAIN-1 | Follow agent.md engineering standards |
| NFR-MAIN-2 | Single Responsibility Principle |
| NFR-MAIN-3 | Type hints everywhere (Python) |
| NFR-MAIN-4 | Comprehensive logging |
| NFR-MAIN-5 | Clear code documentation (docstrings) |
| NFR-MAIN-6 | Test coverage for business logic and APIs |

### 6.7 Compatibility

| Requirement | Target |
|-------------|--------|
| NFR-COMP-1 | Python 3.8+ |
| NFR-COMP-2 | FastAPI framework |
| NFR-COMP-3 | HTML5, CSS3, Vanilla JavaScript |
| NFR-COMP-4 | Works on Chrome, Firefox, Safari (latest versions) |

---

## 7. System Architecture

### 7.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser (UI)                        │
│  Landing → Config → Execution → Comparison → History            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │   Routes   │  │  Services  │  │  Storage   │              │
│  │  (15 APIs) │  │ (Business  │  │ (JSON Files)│             │
│  │            │  │  Logic)    │  │            │              │
│  └────────────┘  └────────────┘  └────────────┘              │
│         │               │               │                        │
│         ▼               ▼               ▼                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │         Core Components                          │           │
│  │  - Config Loader                                │           │
│  │  - API Executor (Dummy)                         │           │
│  │  - Comparison Engine (deepdiff)                  │           │
│  │  - LLM Reporter (Placeholder)                    │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│              (FastAPI Routes - 15 Endpoints)              │
│  Session | Config | Execution | Comparison | Report         │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Service Layer (Business Logic)            │
│  SessionService | ConfigService | ExecutionService          │
│  APIExecutor | ComparisonService | LLMReporter             │
│  StorageService                                          │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      Data Layer                             │
│  Models: Session, Execution, APICall, Comparison, Report    │
│  Schemas: Request/Response Pydantic Models                 │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Storage Layer                             │
│  JSON Files: session_list.json, session_{id}.json          │
│              execution_{id}.json                            │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Sequential Execution** | Easier to debug, predictable, ready for parallel upgrade |
| **JSON File Storage** | Simple, no database overhead, easy audit trail |
| **Session-Based** | Isolated test runs, clear ownership, audit trail |
| **Polling (not WebSocket)** | Simpler implementation, adequate for current scale |
| **Configuration-Driven** | No code changes for new products, scalable |
| **No Pub/Sub Yet** | Sequential execution doesn't need async coordination |
| **Hybrid Reports** | Quick overview (per tab) + deep dive (per API) |

---

## 8. Technical Specifications

### 8.1 Backend Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.104.1 |
| **Server** | Uvicorn | 0.24.0 |
| **Data Validation** | Pydantic | 2.5.0 |
| **Config** | Pydantic Settings | 2.1.0 |
| **HTTP Client** | HTTPX | 0.25.2 |
| **Comparison** | DeepDiff | 6.7.1 |
| **Testing** | Pytest | 7.4.3 |
| **Async** | Pytest-AsyncIO | 0.21.1 |

### 8.2 Frontend Technology Stack

| Component | Technology |
|-----------|-----------|
| **HTML** | HTML5 |
| **CSS** | CSS3, Bootstrap 5 (optional) |
| **JavaScript** | Vanilla JS (ES6+) |
| **HTTP Library** | Fetch API or Axios |

### 8.3 Project Structure

```
internal-testing-portal/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── session_routes.py
│   │       ├── config_routes.py
│   │       ├── execution_routes.py
│   │       ├── comparison_routes.py
│   │       └── report_routes.py
│   ├── services/
│   │   ├── session_service.py
│   │   ├── config_service.py
│   │   ├── execution_service.py
│   │   ├── api_executor.py
│   │   ├── comparison_service.py
│   │   ├── llm_reporter.py
│   │   └── storage_service.py
│   ├── models/
│   │   ├── session.py
│   │   ├── execution.py
│   │   ├── api_call.py
│   │   ├── comparison.py
│   │   └── report.py
│   ├── schemas/
│   │   ├── session.py
│   │   ├── execution.py
│   │   ├── comparison.py
│   │   └── report.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── product_config.py
│   └── utils/
│       ├── dummy_payloads.py
│       ├── dummy_responses.py
│       └── response_normalizer.py
├── config/
│   └── products.json
├── storage/
│   ├── sessions/
│   ├── session_data/
│   └── executions/
├── static/
│   ├── index.html
│   ├── config.html
│   ├── execution.html
│   ├── comparison.html
│   ├── history.html
│   ├── css/
│   └── js/
├── tests/
│   ├── test_services/
│   └── test_api/
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 9. Current Scope Limitations

### 9.1 In Scope (Phase 1)

✅ Dummy/mock API responses
✅ Complete framework and structure
✅ Sequential execution
✅ JSON file storage
✅ Basic UI (HTML/CSS/JS)
✅ Comparison logic (deepdiff)
✅ Placeholder for LLM integration
✅ Configuration-driven product hierarchy
✅ Session-based architecture

### 9.2 Out of Scope (Future Phases)

❌ Real API integrations
❌ Real database connections
❌ Real authentication (Admin/Customer portals)
❌ Parallel execution
❌ Pub/Sub/Message Broker
❌ Full LLM integration (Hugging Face)
❌ WebSocket for real-time updates
❌ Advanced analytics/dashboard
❌ Test result notifications (email, Slack)
❌ CI/CD integration

---

## 10. Future Scope

### 10.1 Phase 2: Parallel Execution

- Parallelize within categories (asyncio)
- Improve execution speed
- Maintain sequential order for clarity

### 10.2 Phase 3: LLM Integration

- Integrate Hugging Face API
- Generate intelligent reports
- Provide insights and recommendations
- Natural language summaries

### 10.3 Phase 4: Advanced Features

- WebSocket for real-time updates
- Redis Streams for job queuing
- Email/Slack notifications
- CI/CD integration
- Advanced analytics dashboard
- Historical trend analysis

### 10.4 Phase 5: Production Integration

- Real API integrations
- Real database connections
- Real authentication
- Production environment testing
- Automated scheduling (cron jobs)

---

## 11. Glossary

| Term | Definition |
|------|-----------|
| **Category** | Top-level insurance product type (e.g., MV4, TRAVEL) |
| **Product** | Insurance brand/insurer (e.g., TOKIO_MARINE, SOMPO) |
| **Plan** | Insurance policy type with specific coverage (e.g., COMPREHENSIVE) |
| **Tab** | UI element representing a Category+Product+Plan combination |
| **Execution** | A test run (one category or all categories) |
| **Session** | A user-initiated test session containing executions |
| **Target Environment** | DEV or QA environment being tested |
| **Staging Environment** | Reference environment for comparison |
| **Sequential Execution** | Running one Category+Product+Plan at a time |
| **FIFO** | First-In-First-Out cleanup strategy |
| **deepdiff** | Python library for intelligent comparison |

---

## 12. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |
| Project Manager | | | |

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | AI Assistant | Initial PRD based on all discussions |

---

**Document End**

**This PRD serves as the single source of truth for the Internal Testing Platform project. All implementation must align with the specifications outlined in this document.**
