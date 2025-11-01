# SQL Quick Reference Cheat Sheet

A quick lookup guide for common SQL commands and syntax.

## Table of Contents
- [Database Operations](#database-operations)
- [Table Operations](#table-operations)
- [CRUD Operations](#crud-operations)
- [Query Clauses](#query-clauses)
- [Joins](#joins)
- [Aggregate Functions](#aggregate-functions)
- [Window Functions](#window-functions)
- [Indexes](#indexes)
- [Transactions](#transactions)
- [Data Types](#data-types)

---

## Database Operations

```sql
-- Create database
CREATE DATABASE database_name;

-- Use database
USE database_name;

-- Show all databases
SHOW DATABASES;

-- Drop database
DROP DATABASE database_name;
```

## Table Operations

### Create Table
```sql
CREATE TABLE table_name (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    age INT CHECK (age >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Alter Table
```sql
-- Add column
ALTER TABLE table_name ADD column_name datatype;

-- Modify column
ALTER TABLE table_name MODIFY column_name new_datatype;

-- Drop column
ALTER TABLE table_name DROP COLUMN column_name;

-- Rename table
RENAME TABLE old_name TO new_name;
```

### Drop Table
```sql
DROP TABLE table_name;
DROP TABLE IF EXISTS table_name;
```

## CRUD Operations

### CREATE (Insert)
```sql
-- Insert single row
INSERT INTO table_name (col1, col2) VALUES (val1, val2);

-- Insert multiple rows
INSERT INTO table_name (col1, col2) VALUES 
    (val1, val2),
    (val3, val4),
    (val5, val6);

-- Insert from select
INSERT INTO table1 SELECT * FROM table2 WHERE condition;
```

### READ (Select)
```sql
-- Basic select
SELECT * FROM table_name;
SELECT col1, col2 FROM table_name;

-- With WHERE
SELECT * FROM table_name WHERE condition;

-- With multiple conditions
SELECT * FROM table_name WHERE col1 = val AND col2 > val;
SELECT * FROM table_name WHERE col1 = val OR col2 = val;
```

### UPDATE
```sql
-- Update records
UPDATE table_name SET col1 = val1 WHERE condition;

-- Update multiple columns
UPDATE table_name SET col1 = val1, col2 = val2 WHERE condition;

-- Update with calculation
UPDATE table_name SET col1 = col1 * 1.10 WHERE condition;
```

### DELETE
```sql
-- Delete records
DELETE FROM table_name WHERE condition;

-- Delete all records
DELETE FROM table_name;

-- Truncate (faster)
TRUNCATE TABLE table_name;
```

## Query Clauses

### WHERE
```sql
-- Comparison operators
WHERE age = 18
WHERE age != 18
WHERE age > 18
WHERE age >= 18
WHERE age < 18
WHERE age <= 18

-- BETWEEN
WHERE age BETWEEN 18 AND 25

-- IN
WHERE city IN ('NYC', 'LA', 'Chicago')

-- LIKE (pattern matching)
WHERE name LIKE 'A%'      -- Starts with A
WHERE name LIKE '%a'      -- Ends with a
WHERE name LIKE '%li%'    -- Contains li
WHERE name LIKE '_a%'     -- Second char is a

-- IS NULL / IS NOT NULL
WHERE email IS NULL
WHERE email IS NOT NULL
```

### ORDER BY
```sql
-- Ascending (default)
ORDER BY column_name
ORDER BY column_name ASC

-- Descending
ORDER BY column_name DESC

-- Multiple columns
ORDER BY col1 ASC, col2 DESC
```

### LIMIT
```sql
-- First 10 rows
LIMIT 10

-- Skip 20, take 10
LIMIT 20, 10
-- or
LIMIT 10 OFFSET 20
```

### DISTINCT
```sql
SELECT DISTINCT column_name FROM table_name;
```

## Joins

### INNER JOIN
```sql
SELECT a.*, b.*
FROM table_a a
INNER JOIN table_b b ON a.id = b.a_id;
```

### LEFT JOIN
```sql
SELECT a.*, b.*
FROM table_a a
LEFT JOIN table_b b ON a.id = b.a_id;
```

### RIGHT JOIN
```sql
SELECT a.*, b.*
FROM table_a a
RIGHT JOIN table_b b ON a.id = b.a_id;
```

### SELF JOIN
```sql
SELECT e.name, m.name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

## Aggregate Functions

```sql
-- Count
SELECT COUNT(*) FROM table_name;
SELECT COUNT(DISTINCT column) FROM table_name;

-- Sum
SELECT SUM(amount) FROM orders;

-- Average
SELECT AVG(salary) FROM employees;

-- Min/Max
SELECT MIN(price), MAX(price) FROM products;
```

### GROUP BY
```sql
SELECT department, COUNT(*), AVG(salary)
FROM employees
GROUP BY department;

-- Multiple columns
SELECT department, city, COUNT(*)
FROM employees
GROUP BY department, city;
```

### HAVING
```sql
SELECT department, AVG(salary)
FROM employees
GROUP BY department
HAVING AVG(salary) > 50000;
```

## Subqueries

```sql
-- In WHERE
SELECT * FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- In SELECT
SELECT name, salary,
    (SELECT AVG(salary) FROM employees) as avg_salary
FROM employees;

-- With IN
SELECT * FROM customers
WHERE id IN (SELECT customer_id FROM orders);

-- With EXISTS
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```

## Window Functions

### ROW_NUMBER
```sql
SELECT name, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) as row_num
FROM employees;
```

### RANK / DENSE_RANK
```sql
SELECT name, salary,
    RANK() OVER (ORDER BY salary DESC) as rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) as dense_rank
FROM employees;
```

### Partitioning
```sql
SELECT name, department, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;
```

### LAG / LEAD
```sql
SELECT date, amount,
    LAG(amount) OVER (ORDER BY date) as prev_amount,
    LEAD(amount) OVER (ORDER BY date) as next_amount
FROM sales;
```

### Running Total
```sql
SELECT date, amount,
    SUM(amount) OVER (ORDER BY date) as running_total
FROM sales;
```

## Views

```sql
-- Create view
CREATE VIEW view_name AS
SELECT col1, col2 FROM table_name WHERE condition;

-- Use view
SELECT * FROM view_name;

-- Drop view
DROP VIEW view_name;
```

## Indexes

```sql
-- Create index
CREATE INDEX idx_name ON table_name(column_name);

-- Create unique index
CREATE UNIQUE INDEX idx_name ON table_name(column_name);

-- Composite index
CREATE INDEX idx_name ON table_name(col1, col2);

-- Show indexes
SHOW INDEXES FROM table_name;

-- Drop index
DROP INDEX idx_name ON table_name;
```

## Transactions

```sql
-- Start transaction
START TRANSACTION;
-- or
BEGIN;

-- Make changes
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- Commit (save)
COMMIT;

-- Or Rollback (undo)
ROLLBACK;

-- With savepoint
START TRANSACTION;
UPDATE table1 SET col = val;
SAVEPOINT sp1;
UPDATE table2 SET col = val;
ROLLBACK TO sp1;  -- Undo only table2 update
COMMIT;
```

## Data Types

### Numeric
```sql
INT                    -- Integer
BIGINT                 -- Large integer
DECIMAL(10,2)          -- Fixed-point (10 digits, 2 after decimal)
FLOAT                  -- Floating-point
DOUBLE                 -- Double precision float
```

### String
```sql
CHAR(10)              -- Fixed length string
VARCHAR(100)          -- Variable length string
TEXT                  -- Long text
ENUM('val1', 'val2')  -- Enumeration
```

### Date/Time
```sql
DATE                  -- Date (YYYY-MM-DD)
TIME                  -- Time (HH:MM:SS)
DATETIME              -- Date and time
TIMESTAMP             -- Timestamp (auto-updates)
YEAR                  -- Year (YYYY)
```

### Other
```sql
BOOLEAN               -- TRUE/FALSE
JSON                  -- JSON data
BLOB                  -- Binary data
```

## Constraints

```sql
-- Primary Key
column_name INT PRIMARY KEY

-- Foreign Key
column_name INT,
FOREIGN KEY (column_name) REFERENCES other_table(id)

-- Unique
column_name VARCHAR(100) UNIQUE

-- Not Null
column_name VARCHAR(100) NOT NULL

-- Check
column_name INT CHECK (column_name > 0)

-- Default
column_name INT DEFAULT 0

-- Auto Increment
column_name INT AUTO_INCREMENT
```

## Common Patterns

### Get Top N per Group
```sql
SELECT * FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) as rn
    FROM products
) ranked
WHERE rn <= 3;
```

### Find Duplicates
```sql
SELECT column_name, COUNT(*)
FROM table_name
GROUP BY column_name
HAVING COUNT(*) > 1;
```

### Delete Duplicates (Keep One)
```sql
DELETE t1 FROM table_name t1
INNER JOIN table_name t2
WHERE t1.id > t2.id AND t1.email = t2.email;
```

### Pivot Data
```sql
SELECT 
    student,
    MAX(CASE WHEN subject = 'Math' THEN score END) as Math,
    MAX(CASE WHEN subject = 'Science' THEN score END) as Science
FROM scores
GROUP BY student;
```

### Running Total
```sql
SELECT date, amount,
    SUM(amount) OVER (ORDER BY date) as running_total
FROM sales;
```

### Year Over Year Growth
```sql
SELECT 
    year,
    revenue,
    LAG(revenue) OVER (ORDER BY year) as prev_year,
    (revenue - LAG(revenue) OVER (ORDER BY year)) * 100.0 / 
        LAG(revenue) OVER (ORDER BY year) as growth_percent
FROM annual_revenue;
```

## Useful Functions

### String Functions
```sql
CONCAT(str1, str2)           -- Concatenate strings
UPPER(str)                   -- Convert to uppercase
LOWER(str)                   -- Convert to lowercase
LENGTH(str)                  -- String length
SUBSTRING(str, start, len)   -- Extract substring
TRIM(str)                    -- Remove spaces
REPLACE(str, from, to)       -- Replace text
```

### Date Functions
```sql
NOW()                        -- Current date and time
CURDATE()                    -- Current date
CURTIME()                    -- Current time
DATE_ADD(date, INTERVAL n DAY)  -- Add days
DATEDIFF(date1, date2)       -- Difference in days
YEAR(date)                   -- Extract year
MONTH(date)                  -- Extract month
DAY(date)                    -- Extract day
```

### Math Functions
```sql
ROUND(num, decimals)         -- Round number
CEIL(num)                    -- Round up
FLOOR(num)                   -- Round down
ABS(num)                     -- Absolute value
POWER(num, power)            -- Raise to power
MOD(num, divisor)            -- Modulo
```

### Conditional
```sql
-- CASE
CASE
    WHEN condition1 THEN result1
    WHEN condition2 THEN result2
    ELSE default_result
END

-- IF
IF(condition, true_value, false_value)

-- COALESCE (return first non-null)
COALESCE(col1, col2, 'default')

-- NULLIF (return NULL if equal)
NULLIF(col1, col2)
```

## Performance Tips

1. **Use indexes** on WHERE, JOIN, ORDER BY columns
2. **Avoid SELECT *** - specify needed columns
3. **Use LIMIT** for large result sets
4. **Use EXPLAIN** to analyze queries
5. **Avoid functions** on indexed columns in WHERE
6. **Use proper data types** to save space
7. **Normalize** to reduce redundancy
8. **Denormalize** for read-heavy tables
9. **Use prepared statements** to prevent SQL injection
10. **Keep transactions short**

## Common Interview Questions

**Q: Difference between WHERE and HAVING?**
- WHERE filters rows before grouping
- HAVING filters groups after GROUP BY

**Q: Difference between INNER JOIN and LEFT JOIN?**
- INNER JOIN returns only matching rows
- LEFT JOIN returns all left table rows + matches

**Q: Difference between DELETE and TRUNCATE?**
- DELETE can use WHERE, slower, can rollback
- TRUNCATE removes all rows, faster, can't rollback

**Q: Difference between RANK and DENSE_RANK?**
- RANK leaves gaps for ties
- DENSE_RANK doesn't leave gaps

**Q: How to find 2nd highest salary?**
```sql
SELECT MAX(salary) FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```

---

**For detailed explanations and examples, refer to the main documentation files!**

