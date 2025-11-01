# SQL 8: Indexing

## What is an Index?
An **index** is a database structure that improves the speed of data retrieval operations. Think of it like an index in a book that helps you find topics quickly!

**Without Index**: Database scans every row (like reading a book page by page)
**With Index**: Database jumps directly to relevant rows (like using a book's index)

## Real-World Analogy
Imagine a phone book:
- **Without Index**: Search every page to find "John Smith" (slow!)
- **With Index**: Names are alphabetically sorted, you go directly to 'S' section (fast!)

## Why Use Indexes?

### Advantages:
✅ **Faster SELECT queries** with WHERE, ORDER BY, GROUP BY
✅ **Faster JOIN operations**
✅ **Enforce uniqueness** (unique indexes)
✅ **Improve sorting performance**

### Disadvantages:
❌ **Slower INSERT/UPDATE/DELETE** (index must be updated too)
❌ **Uses additional disk space**
❌ **Too many indexes can slow down writes**

## When to Use Indexes

### Use indexes when:
- Column is frequently used in WHERE clause
- Column is used in JOIN conditions
- Column is used in ORDER BY or GROUP BY
- Large tables with many rows
- Column has high cardinality (many unique values)

### Don't use indexes when:
- Small tables (overhead not worth it)
- Columns frequently updated
- Columns with few unique values (low cardinality)
- Columns rarely used in queries

## Types of Indexes

### 1. Primary Key Index
Automatically created with PRIMARY KEY. Unique + Not Null.

```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,  -- Automatically indexed
    name VARCHAR(100),
    age INT
);
```

### 2. Unique Index
Ensures all values are unique.

```sql
-- Create unique index
CREATE UNIQUE INDEX idx_email ON users(email);

-- Or with ALTER TABLE
ALTER TABLE users ADD UNIQUE INDEX idx_email (email);

-- Or during table creation
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    email VARCHAR(100) UNIQUE  -- Automatically creates unique index
);
```

### 3. Regular (Non-Unique) Index
Most common type, allows duplicates.

```sql
-- Create index on single column
CREATE INDEX idx_lastname ON employees(last_name);

-- Create index with specific name
CREATE INDEX idx_dept ON employees(department);
```

### 4. Composite Index (Multi-Column)
Index on multiple columns.

```sql
-- Index on multiple columns
CREATE INDEX idx_name_dept ON employees(last_name, first_name, department);

-- Order matters!
-- This index helps queries on:
-- 1. last_name
-- 2. last_name + first_name
-- 3. last_name + first_name + department
-- But NOT on first_name alone or department alone
```

### 5. Full-Text Index
For text searching (LIKE queries).

```sql
-- Create full-text index
CREATE FULLTEXT INDEX idx_description ON products(description);

-- Use with MATCH AGAINST
SELECT * FROM products
WHERE MATCH(description) AGAINST('laptop computer');
```

## Creating Indexes

### Method 1: CREATE INDEX
```sql
-- Basic syntax
CREATE INDEX index_name ON table_name(column_name);

-- Examples
CREATE INDEX idx_age ON students(age);
CREATE INDEX idx_city ON customers(city);
CREATE INDEX idx_salary ON employees(salary);
```

### Method 2: ALTER TABLE
```sql
-- Add index to existing table
ALTER TABLE students ADD INDEX idx_age (age);

-- Add unique index
ALTER TABLE users ADD UNIQUE INDEX idx_email (email);

-- Add composite index
ALTER TABLE orders ADD INDEX idx_customer_date (customer_id, order_date);
```

### Method 3: During Table Creation
```sql
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE,
    
    INDEX idx_dept (department),
    INDEX idx_salary (salary),
    UNIQUE INDEX idx_email (email)
);
```

## Viewing Indexes

```sql
-- Show all indexes on a table
SHOW INDEXES FROM employees;

-- Or use
SHOW INDEX FROM employees;

-- Get index information
SHOW CREATE TABLE employees;

-- MySQL information_schema
SELECT * FROM information_schema.statistics
WHERE table_name = 'employees';
```

## Dropping Indexes

```sql
-- Drop index
DROP INDEX idx_age ON students;

-- Or with ALTER TABLE
ALTER TABLE students DROP INDEX idx_age;

-- Drop primary key
ALTER TABLE students DROP PRIMARY KEY;
```

## Practical Examples

### Example 1: E-commerce System

```sql
-- Create products table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT,
    created_at TIMESTAMP
);

-- Insert sample data (imagine 1 million products)
INSERT INTO products (product_name, category, price, stock, created_at)
VALUES 
('Laptop Dell', 'Electronics', 1200.00, 50, NOW()),
('iPhone 15', 'Electronics', 999.00, 100, NOW()),
('Nike Shoes', 'Fashion', 129.99, 200, NOW());

-- Slow query without index
SELECT * FROM products WHERE category = 'Electronics';
-- Scans all 1 million rows

-- Create index on category
CREATE INDEX idx_category ON products(category);

-- Now this query is MUCH faster!
SELECT * FROM products WHERE category = 'Electronics';
-- Uses index to jump directly to Electronics products

-- More useful indexes for this table
CREATE INDEX idx_price ON products(price);
CREATE INDEX idx_stock ON products(stock);
CREATE INDEX idx_created ON products(created_at);

-- Composite index for common queries
CREATE INDEX idx_category_price ON products(category, price);

-- This query benefits from composite index
SELECT * FROM products 
WHERE category = 'Electronics' 
AND price < 1000;
```

### Example 2: User Management

```sql
-- Create users table
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    email VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);

-- Add indexes
CREATE UNIQUE INDEX idx_username ON users(username);
CREATE UNIQUE INDEX idx_email ON users(email);
CREATE INDEX idx_last_name ON users(last_name);
CREATE INDEX idx_city ON users(city);
CREATE INDEX idx_created ON users(created_at);

-- Composite index for name searches
CREATE INDEX idx_full_name ON users(last_name, first_name);

-- These queries now run fast:

-- 1. Login (uses idx_username)
SELECT * FROM users WHERE username = 'john_doe';

-- 2. Email lookup (uses idx_email)
SELECT * FROM users WHERE email = 'john@example.com';

-- 3. Search by last name (uses idx_last_name)
SELECT * FROM users WHERE last_name = 'Smith';

-- 4. Search by full name (uses idx_full_name)
SELECT * FROM users 
WHERE last_name = 'Smith' AND first_name = 'John';

-- 5. Users by city (uses idx_city)
SELECT * FROM users WHERE city = 'New York';
```

### Example 3: Order Management

```sql
-- Create orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    order_date DATE,
    status VARCHAR(20),
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP,
    
    INDEX idx_customer (customer_id),
    INDEX idx_date (order_date),
    INDEX idx_status (status),
    INDEX idx_amount (total_amount)
);

-- Composite indexes for common query patterns
CREATE INDEX idx_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_status_date ON orders(status, order_date);

-- Fast queries:

-- 1. Customer's orders (uses idx_customer_date)
SELECT * FROM orders 
WHERE customer_id = 123 
ORDER BY order_date DESC;

-- 2. Pending orders (uses idx_status)
SELECT * FROM orders WHERE status = 'pending';

-- 3. Orders in date range (uses idx_date)
SELECT * FROM orders 
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';

-- 4. High value orders (uses idx_amount)
SELECT * FROM orders WHERE total_amount > 1000;
```

## Understanding Index Performance

### Example: Performance Comparison

```sql
-- Create large table without indexes
CREATE TABLE test_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    email VARCHAR(100),
    age INT
);

-- Insert 1 million rows (imagine)
-- ... bulk insert ...

-- Query without index (SLOW - full table scan)
EXPLAIN SELECT * FROM test_users WHERE username = 'john123';
-- Type: ALL (scans all rows)
-- Rows: 1,000,000

-- Create index
CREATE INDEX idx_username ON test_users(username);

-- Query with index (FAST - index lookup)
EXPLAIN SELECT * FROM test_users WHERE username = 'john123';
-- Type: ref (uses index)
-- Rows: 1 (only checks relevant rows)
```

### EXPLAIN Command
Shows how MySQL executes a query.

```sql
-- Check query execution plan
EXPLAIN SELECT * FROM orders 
WHERE customer_id = 123 AND order_date > '2024-01-01';

-- Key columns to check:
-- type: How MySQL accesses data
--   ALL (worst) -> index -> range -> ref -> const (best)
-- key: Which index is used
-- rows: Estimated rows to scan
```

## Index Best Practices

### 1. Index Selectivity
Index columns with high selectivity (many unique values).

```sql
-- Good: Email (unique)
CREATE INDEX idx_email ON users(email);

-- Good: Customer ID (many unique values)
CREATE INDEX idx_customer ON orders(customer_id);

-- Bad: Gender (only 2-3 values)
-- CREATE INDEX idx_gender ON users(gender);  -- Don't do this!

-- Bad: Boolean flags
-- CREATE INDEX idx_active ON users(is_active);  -- Don't do this!
```

### 2. Composite Index Order
Put most selective column first.

```sql
-- Good: last_name has more selectivity than first_name
CREATE INDEX idx_name ON users(last_name, first_name);

-- This helps queries:
SELECT * FROM users WHERE last_name = 'Smith';  -- ✅
SELECT * FROM users WHERE last_name = 'Smith' AND first_name = 'John';  -- ✅

-- But NOT:
SELECT * FROM users WHERE first_name = 'John';  -- ❌ (doesn't use index)
```

### 3. Cover Frequently Used Queries
Analyze your queries and create indexes accordingly.

```sql
-- If you often run:
SELECT * FROM products WHERE category = 'Electronics' ORDER BY price;

-- Create composite index:
CREATE INDEX idx_category_price ON products(category, price);
```

### 4. Don't Over-Index
Too many indexes slow down writes.

```sql
-- Don't create indexes on every column!
-- Each index adds overhead to INSERT/UPDATE/DELETE

-- Good: 2-5 indexes per table
-- Okay: 5-10 indexes
-- Bad: 15+ indexes (unless very specific use case)
```

### 5. Regular Maintenance
Rebuild/optimize indexes periodically.

```sql
-- Analyze table (updates index statistics)
ANALYZE TABLE products;

-- Optimize table (rebuilds and defragments)
OPTIMIZE TABLE products;
```

## Covering Index
An index that contains all columns needed for a query.

```sql
-- Create covering index
CREATE INDEX idx_covering ON orders(customer_id, order_date, total_amount);

-- This query uses only the index (no table access needed!)
SELECT customer_id, order_date, total_amount 
FROM orders 
WHERE customer_id = 123;
```

## Index on Computed Columns

```sql
-- Create index on expression
CREATE INDEX idx_year ON orders(YEAR(order_date));

-- Now this is fast:
SELECT * FROM orders WHERE YEAR(order_date) = 2024;

-- Or create a generated column
ALTER TABLE orders 
ADD COLUMN order_year INT GENERATED ALWAYS AS (YEAR(order_date)) STORED;

CREATE INDEX idx_order_year ON orders(order_year);
```

## Common Mistakes

### Mistake 1: Not Using Index
```sql
-- Index exists on 'name'
-- But this doesn't use it (function on column)
SELECT * FROM users WHERE UPPER(name) = 'JOHN';

-- Better: Use index-friendly query
SELECT * FROM users WHERE name = 'john';
```

### Mistake 2: Wrong Composite Index Order
```sql
-- Index: idx_date_customer on (order_date, customer_id)

-- Uses index ✅
SELECT * FROM orders WHERE order_date = '2024-01-01';

-- Doesn't use index ❌
SELECT * FROM orders WHERE customer_id = 123;

-- Better: Create idx_customer_date (customer_id, order_date)
```

### Mistake 3: Too Many Indexes
```sql
-- Too many indexes slow down INSERT/UPDATE
-- Only create indexes for frequently used queries
```

## Key Takeaways

1. **Indexes speed up reads, slow down writes**
2. **Index frequently queried columns** (WHERE, JOIN, ORDER BY)
3. **Unique index** for unique columns
4. **Composite index** for multi-column queries
5. **Index selectivity matters** (high uniqueness = better)
6. **Composite index order matters** (most selective first)
7. **Don't over-index** (2-5 indexes per table is typical)
8. **Use EXPLAIN** to check query performance
9. **Maintain indexes** (ANALYZE, OPTIMIZE)

## Interview Questions

**Q1: What is an index?**
Data structure that improves query performance by allowing quick data lookup.

**Q2: Types of indexes?**
Primary, Unique, Regular (non-unique), Composite, Full-text

**Q3: Disadvantages of indexes?**
Slower writes (INSERT/UPDATE/DELETE), extra storage space

**Q4: When to use composite index?**
When queries filter/sort on multiple columns together

**Q5: How to check if query uses index?**
Use EXPLAIN command

## Practice Exercises

1. Create indexes for a blog system (posts, comments, tags)
2. Identify which queries benefit from indexes
3. Create composite indexes for multi-column searches
4. Use EXPLAIN to analyze query performance
5. Find slow queries and optimize with indexes
6. Create covering index for report queries
7. Design index strategy for large tables (1M+ rows)

