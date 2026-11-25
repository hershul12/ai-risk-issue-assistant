# SQL Queries for pgAdmin

Four demonstration queries on the RiskPilot database. They use standard SQL and work on
PostgreSQL (pgAdmin) and on the local SQLite file.

**How to run:** in pgAdmin, open the RiskPilot database, choose **Tools > Query Tool**,
paste a query and press **F5**. All queries are read-only.

**Tables used** (created by the app):
- `items`: one row per risk or issue (title, category, probability, impact, score,
  priority, owner, status, due_date, ...)
- `audit_log`: one row per change (item_id, action, changed_by, details, timestamp)

The results below are from the local PostgreSQL 16 database (`riskpilot`, 32 records) on
2026-11-25. The same queries were also run on the local SQLite file. Results on the live
database will differ as records are added and reviewed.

## 1. Open High and Critical risks by category

**Purpose:** shows where the serious open exposure is, so the programme can focus attention
on the riskiest areas. Uses the same priority bands as the app (High 13-19, Critical 20-25).

```sql
SELECT category,
       COUNT(*) AS open_high_or_critical,
       SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) AS critical,
       SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) AS high
FROM items
WHERE status <> 'Closed'
  AND priority IN ('High', 'Critical')
GROUP BY category
ORDER BY open_high_or_critical DESC, category;
```

**Result:**

| category | open_high_or_critical | critical | high |
|----------|----------------------:|---------:|-----:|
| Technical | 5 | 2 | 3 |
| Compliance | 2 | 0 | 2 |
| Vendor | 2 | 0 | 2 |
| Resource | 1 | 0 | 1 |
| Schedule | 1 | 1 | 0 |
| Scope | 1 | 0 | 1 |
| Security | 1 | 0 | 1 |

Technical has the most serious open items (5, including 2 Critical).

## 2. Overdue records per owner

**Purpose:** shows who has overdue work, for follow-up. Uses the app's overdue rule: the due
date has passed and the record is not Closed.

```sql
SELECT owner,
       COUNT(*) AS overdue_records,
       MIN(due_date) AS oldest_due_date,
       MAX(score) AS highest_score
FROM items
WHERE status <> 'Closed'
  AND due_date < CURRENT_DATE
GROUP BY owner
ORDER BY overdue_records DESC, owner;
```

**Result:**

| owner | overdue_records | oldest_due_date | highest_score |
|-------|----------------:|-----------------|--------------:|
| Priya Nair | 3 | 2026-11-12 | 20 |
| Sanjay Iyer | 2 | 2026-11-17 | 12 |
| Asha Menon | 1 | 2026-11-20 | 16 |
| Neha Kapoor | 1 | 2026-11-10 | 16 |
| Vikram Shah | 1 | 2026-11-18 | 16 |

8 overdue records in total, the same number the dashboard shows. Priya Nair has the most,
including a Critical one (score 20).

## 3. Records by status

**Purpose:** shows how work is moving through the review workflow
(Open -> In Progress -> Pending Review -> Closed).

```sql
SELECT status,
       COUNT(*) AS records
FROM items
GROUP BY status
ORDER BY CASE status
           WHEN 'Open' THEN 1
           WHEN 'In Progress' THEN 2
           WHEN 'Pending Review' THEN 3
           WHEN 'Closed' THEN 4
           ELSE 5
         END;
```

**Result:**

| status | records |
|--------|--------:|
| Open | 17 |
| In Progress | 10 |
| Pending Review | 3 |
| Closed | 2 |

3 records are waiting for a Programme Lead's review decision.

## 4. Full audit trail of one record

**Purpose:** shows every change to one record (who did what, when, and why), which is the
traceability the review workflow depends on. Change `1` to the record you want to inspect.

```sql
SELECT i.id,
       i.title,
       a.timestamp,
       a.action,
       a.changed_by,
       a.details
FROM audit_log a
JOIN items i ON i.id = a.item_id
WHERE a.item_id = 1
ORDER BY a.timestamp, a.id;
```

**Result:**

| id | title | timestamp | action | changed_by | details |
|----|-------|-----------|--------|------------|---------|
| 1 | Core banking migration schedule slip | 2026-11-20 23:47:21 | created | System | Loaded from sample register |

In the local database each record so far has only its `created` entry. When a record is
edited or moved through review, the trail also shows `updated` rows (details such as
`mitigation: old -> new`) and `status_change` rows (for example
`Open -> In Progress. Note: ...`), each with the role that made the change.

**Tip:** to find a record with a long history to demonstrate, run:

```sql
SELECT item_id, COUNT(*) AS changes
FROM audit_log
GROUP BY item_id
ORDER BY changes DESC, item_id
LIMIT 3;
```
