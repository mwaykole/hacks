# SQL 10: Window Functions

## What are Window Functions?
**Window functions** perform calculations across a set of rows related to the current row, WITHOUT collapsing the rows like GROUP BY does.

Think of it as looking through a "window" at related rows while keeping all individual rows!

## Window Functions vs GROUP BY

### GROUP BY (Collapses Rows):
```sql
SELECT department, AVG(salary)
FROM employees
GROUP BY department;

-- Result: One row per department
-- IT     | 75000
-- HR     | 65000
```

### Window Functions (Keeps All Rows):
```sql
SELECT 
    name,
    department,
    salary,
    AVG(salary) OVER (PARTITION BY department) as dept_avg
FROM employees;

-- Result: All employee rows with department average
-- Alice   | IT | 80000 | 75000
-- Bob     | IT | 70000 | 75000
-- Charlie | HR | 65000 | 65000
```

## Basic Syntax

```sql
function_name() OVER (
    [PARTITION BY column]
    [ORDER BY column]
    [ROWS/RANGE frame_specification]
)
```

**Components:**
- **Function**: What calculation to perform (SUM, AVG, RANK, etc.)
- **OVER**: Defines it's a window function
- **PARTITION BY**: Divides rows into groups (optional)
- **ORDER BY**: Orders rows within each partition (optional)
- **Frame**: Defines which rows to include in calculation (optional)

## Types of Window Functions

### 1. Aggregate Window Functions

#### AVG()
```sql
-- Average salary per department, shown for each employee
SELECT 
    name,
    department,
    salary,
    AVG(salary) OVER (PARTITION BY department) as dept_avg_salary
FROM employees;
```

#### SUM()
```sql
-- Running total of sales
SELECT 
    date,
    amount,
    SUM(amount) OVER (ORDER BY date) as running_total
FROM sales;
```

#### COUNT()
```sql
-- Count employees in each department
SELECT 
    name,
    department,
    COUNT(*) OVER (PARTITION BY department) as dept_count
FROM employees;
```

#### MIN() / MAX()
```sql
-- Show each employee with highest and lowest salary in their dept
SELECT 
    name,
    department,
    salary,
    MAX(salary) OVER (PARTITION BY department) as dept_max,
    MIN(salary) OVER (PARTITION BY department) as dept_min
FROM employees;
```

### 2. Ranking Functions

#### ROW_NUMBER()
Assigns unique sequential number to each row.

```sql
-- Number employees within each department
SELECT 
    name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num
FROM employees;

-- Result:
-- Alice   | IT | 80000 | 1
-- Bob     | IT | 75000 | 2
-- Charlie | IT | 70000 | 3
```

#### RANK()
Assigns rank with gaps for ties.

```sql
-- Rank employees by salary
SELECT 
    name,
    salary,
    RANK() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- If two employees have same salary:
-- Alice   | 80000 | 1
-- Bob     | 75000 | 2
-- Charlie | 75000 | 2
-- Diana   | 70000 | 4  (skips 3)
```

#### DENSE_RANK()
Assigns rank without gaps for ties.

```sql
-- Dense rank by salary
SELECT 
    name,
    salary,
    DENSE_RANK() OVER (ORDER BY salary DESC) as dense_rank
FROM employees;

-- Result:
-- Alice   | 80000 | 1
-- Bob     | 75000 | 2
-- Charlie | 75000 | 2
-- Diana   | 70000 | 3  (no gap)
```

#### NTILE(n)
Divides rows into n equal groups.

```sql
-- Divide employees into 4 quartiles by salary
SELECT 
    name,
    salary,
    NTILE(4) OVER (ORDER BY salary DESC) as quartile
FROM employees;

-- Result: Groups employees into 4 salary quartiles
```

### 3. Value Functions

#### LAG()
Accesses previous row's value.

```sql
-- Compare each employee's salary with previous one
SELECT 
    name,
    salary,
    LAG(salary, 1) OVER (ORDER BY salary) as previous_salary,
    salary - LAG(salary, 1) OVER (ORDER BY salary) as difference
FROM employees;
```

#### LEAD()
Accesses next row's value.

```sql
-- Compare with next employee's salary
SELECT 
    name,
    salary,
    LEAD(salary, 1) OVER (ORDER BY salary) as next_salary
FROM employees;
```

#### FIRST_VALUE()
Gets first value in the window.

```sql
-- Show highest salary in department for each employee
SELECT 
    name,
    department,
    salary,
    FIRST_VALUE(salary) OVER (
        PARTITION BY department 
        ORDER BY salary DESC
    ) as highest_dept_salary
FROM employees;
```

#### LAST_VALUE()
Gets last value in the window.

```sql
-- Show lowest salary in department
SELECT 
    name,
    department,
    salary,
    LAST_VALUE(salary) OVER (
        PARTITION BY department 
        ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as lowest_dept_salary
FROM employees;
```

## Practical Examples

### Example 1: Sales Analysis

```sql
-- Create sales table
CREATE TABLE sales (
    sale_id INT PRIMARY KEY,
    sale_date DATE,
    product VARCHAR(100),
    category VARCHAR(50),
    amount DECIMAL(10,2)
);

-- Insert sample data
INSERT INTO sales VALUES
(1, '2024-01-01', 'Laptop', 'Electronics', 1200.00),
(2, '2024-01-02', 'Mouse', 'Electronics', 25.00),
(3, '2024-01-03', 'Desk', 'Furniture', 300.00),
(4, '2024-01-04', 'Chair', 'Furniture', 150.00),
(5, '2024-01-05', 'Keyboard', 'Electronics', 75.00),
(6, '2024-01-06', 'Monitor', 'Electronics', 400.00);

-- Query 1: Running total of sales
SELECT 
    sale_date,
    product,
    amount,
    SUM(amount) OVER (ORDER BY sale_date) as running_total
FROM sales;

-- Result:
-- 2024-01-01 | Laptop   | 1200.00 | 1200.00
-- 2024-01-02 | Mouse    | 25.00   | 1225.00
-- 2024-01-03 | Desk     | 300.00  | 1525.00
-- ...

-- Query 2: Running total by category
SELECT 
    sale_date,
    product,
    category,
    amount,
    SUM(amount) OVER (
        PARTITION BY category 
        ORDER BY sale_date
    ) as category_running_total
FROM sales;

-- Query 3: Compare with previous day's sale
SELECT 
    sale_date,
    product,
    amount,
    LAG(amount, 1) OVER (ORDER BY sale_date) as prev_day_amount,
    amount - LAG(amount, 1) OVER (ORDER BY sale_date) as difference
FROM sales;

-- Query 4: Rank products by sales amount
SELECT 
    product,
    amount,
    RANK() OVER (ORDER BY amount DESC) as sales_rank,
    DENSE_RANK() OVER (ORDER BY amount DESC) as dense_rank
FROM sales;

-- Query 5: Moving average (3-day)
SELECT 
    sale_date,
    amount,
    AVG(amount) OVER (
        ORDER BY sale_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as moving_avg_3day
FROM sales;
```

### Example 2: Employee Performance

```sql
-- Create employees table
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE,
    performance_score INT
);

-- Insert sample data
INSERT INTO employees VALUES
(1, 'Alice', 'IT', 90000, '2020-01-15', 95),
(2, 'Bob', 'IT', 75000, '2021-03-20', 85),
(3, 'Charlie', 'IT', 80000, '2019-05-10', 90),
(4, 'Diana', 'HR', 70000, '2020-07-12', 88),
(5, 'Eve', 'HR', 65000, '2022-02-01', 92),
(6, 'Frank', 'Finance', 85000, '2020-11-20', 87),
(7, 'Grace', 'Finance', 80000, '2021-09-15', 91);

-- Query 1: Rank employees by salary within department
SELECT 
    name,
    department,
    salary,
    RANK() OVER (
        PARTITION BY department 
        ORDER BY salary DESC
    ) as dept_salary_rank
FROM employees;

-- Query 2: Compare salary with department average
SELECT 
    name,
    department,
    salary,
    AVG(salary) OVER (PARTITION BY department) as dept_avg_salary,
    salary - AVG(salary) OVER (PARTITION BY department) as diff_from_avg
FROM employees;

-- Query 3: Top 2 earners per department
SELECT * FROM (
    SELECT 
        name,
        department,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department 
            ORDER BY salary DESC
        ) as rn
    FROM employees
) ranked
WHERE rn <= 2;

-- Query 4: Salary percentile
SELECT 
    name,
    salary,
    PERCENT_RANK() OVER (ORDER BY salary) as percentile
FROM employees;

-- Query 5: Compare with previous hire in department
SELECT 
    name,
    department,
    hire_date,
    salary,
    LAG(name) OVER (
        PARTITION BY department 
        ORDER BY hire_date
    ) as previous_hire,
    LAG(salary) OVER (
        PARTITION BY department 
        ORDER BY hire_date
    ) as previous_salary
FROM employees;
```

### Example 3: Student Grades

```sql
-- Create students table
CREATE TABLE student_scores (
    student_id INT,
    student_name VARCHAR(100),
    subject VARCHAR(50),
    score INT,
    exam_date DATE
);

-- Insert sample data
INSERT INTO student_scores VALUES
(1, 'Alice', 'Math', 95, '2024-01-15'),
(1, 'Alice', 'Science', 88, '2024-01-16'),
(1, 'Alice', 'English', 92, '2024-01-17'),
(2, 'Bob', 'Math', 78, '2024-01-15'),
(2, 'Bob', 'Science', 85, '2024-01-16'),
(2, 'Bob', 'English', 80, '2024-01-17'),
(3, 'Charlie', 'Math', 92, '2024-01-15'),
(3, 'Charlie', 'Science', 95, '2024-01-16'),
(3, 'Charlie', 'English', 88, '2024-01-17');

-- Query 1: Average score per student, shown for each exam
SELECT 
    student_name,
    subject,
    score,
    AVG(score) OVER (PARTITION BY student_name) as student_avg
FROM student_scores;

-- Query 2: Rank students in each subject
SELECT 
    student_name,
    subject,
    score,
    RANK() OVER (
        PARTITION BY subject 
        ORDER BY score DESC
    ) as subject_rank
FROM student_scores;

-- Query 3: Compare with previous exam score
SELECT 
    student_name,
    exam_date,
    subject,
    score,
    LAG(score) OVER (
        PARTITION BY student_name 
        ORDER BY exam_date
    ) as previous_score,
    score - LAG(score) OVER (
        PARTITION BY student_name 
        ORDER BY exam_date
    ) as improvement
FROM student_scores;

-- Query 4: Best and worst subject per student
SELECT DISTINCT
    student_name,
    FIRST_VALUE(subject) OVER (
        PARTITION BY student_name 
        ORDER BY score DESC
    ) as best_subject,
    LAST_VALUE(subject) OVER (
        PARTITION BY student_name 
        ORDER BY score DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as worst_subject
FROM student_scores;

-- Query 5: Top 3 scores per subject
SELECT * FROM (
    SELECT 
        subject,
        student_name,
        score,
        DENSE_RANK() OVER (
            PARTITION BY subject 
            ORDER BY score DESC
        ) as rank
    FROM student_scores
) ranked
WHERE rank <= 3;
```

### Example 4: E-commerce Orders

```sql
-- Create orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    customer_name VARCHAR(100),
    order_date DATE,
    amount DECIMAL(10,2)
);

-- Insert sample data
INSERT INTO orders VALUES
(1, 101, 'Alice', '2024-01-15', 500.00),
(2, 101, 'Alice', '2024-02-20', 750.00),
(3, 101, 'Alice', '2024-03-10', 300.00),
(4, 102, 'Bob', '2024-01-25', 400.00),
(5, 102, 'Bob', '2024-02-15', 600.00),
(6, 103, 'Charlie', '2024-01-30', 1000.00);

-- Query 1: Customer lifetime value (running total)
SELECT 
    customer_name,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date
    ) as lifetime_value
FROM orders;

-- Query 2: Order number for each customer
SELECT 
    customer_name,
    order_date,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY order_date
    ) as order_number
FROM orders;

-- Query 3: Compare with previous order
SELECT 
    customer_name,
    order_date,
    amount,
    LAG(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date
    ) as previous_order_amount,
    LAG(order_date) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date
    ) as previous_order_date
FROM orders;

-- Query 4: Days since last order
SELECT 
    customer_name,
    order_date,
    amount,
    DATEDIFF(
        order_date,
        LAG(order_date) OVER (
            PARTITION BY customer_id 
            ORDER BY order_date
        )
    ) as days_since_last_order
FROM orders;

-- Query 5: Moving average of order amount
SELECT 
    customer_name,
    order_date,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as moving_avg
FROM orders;
```

## Window Frame Specifications

Control which rows to include in calculation.

### ROWS vs RANGE

```sql
-- ROWS: Physical rows
SELECT 
    date,
    amount,
    SUM(amount) OVER (
        ORDER BY date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as sum_last_3_rows
FROM sales;

-- RANGE: Logical range (includes ties)
SELECT 
    date,
    amount,
    SUM(amount) OVER (
        ORDER BY date
        RANGE BETWEEN INTERVAL 3 DAY PRECEDING AND CURRENT ROW
    ) as sum_last_3_days
FROM sales;
```

### Frame Specifications

```sql
-- Current row only
ROWS BETWEEN CURRENT ROW AND CURRENT ROW

-- All rows before current
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- All rows after current
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING

-- All rows
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

-- 2 rows before to 1 row after
ROWS BETWEEN 2 PRECEDING AND 1 FOLLOWING

-- Previous 3 rows (including current)
ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
```

## Common Use Cases

### 1. Running Totals
```sql
SELECT 
    date,
    amount,
    SUM(amount) OVER (ORDER BY date) as running_total
FROM sales;
```

### 2. Moving Averages
```sql
SELECT 
    date,
    price,
    AVG(price) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7days
FROM stock_prices;
```

### 3. Ranking
```sql
SELECT 
    product,
    sales,
    RANK() OVER (ORDER BY sales DESC) as rank
FROM product_sales;
```

### 4. Top N per Group
```sql
SELECT * FROM (
    SELECT 
        category,
        product,
        sales,
        ROW_NUMBER() OVER (
            PARTITION BY category 
            ORDER BY sales DESC
        ) as rn
    FROM products
) ranked
WHERE rn <= 5;
```

### 5. Percentage of Total
```sql
SELECT 
    product,
    sales,
    sales * 100.0 / SUM(sales) OVER () as percent_of_total
FROM product_sales;
```

### 6. Year-over-Year Growth
```sql
SELECT 
    year,
    revenue,
    LAG(revenue) OVER (ORDER BY year) as prev_year_revenue,
    (revenue - LAG(revenue) OVER (ORDER BY year)) * 100.0 / 
    LAG(revenue) OVER (ORDER BY year) as yoy_growth_percent
FROM annual_revenue;
```

## Key Takeaways

1. **Window functions** perform calculations across rows without collapsing them
2. **PARTITION BY** divides data into groups
3. **ORDER BY** orders rows within partitions
4. **Ranking functions**: ROW_NUMBER, RANK, DENSE_RANK, NTILE
5. **Value functions**: LAG, LEAD, FIRST_VALUE, LAST_VALUE
6. **Aggregate functions**: SUM, AVG, COUNT, MIN, MAX (with OVER clause)
7. **Frame specifications** control which rows to include
8. Keep individual rows unlike GROUP BY

## Interview Questions

**Q1: Difference between window function and GROUP BY?**
Window functions keep all rows; GROUP BY collapses rows into groups.

**Q2: Difference between RANK and DENSE_RANK?**
RANK leaves gaps for ties; DENSE_RANK doesn't.

**Q3: What does PARTITION BY do?**
Divides data into groups (like GROUP BY but without collapsing).

**Q4: Use case for LAG function?**
Compare current row with previous row (e.g., growth calculations).

**Q5: What is ROW_NUMBER?**
Assigns unique sequential number to each row.

## Practice Exercises

1. Calculate running total of sales by month
2. Find top 3 products per category by sales
3. Calculate moving average for stock prices
4. Compare each month's sales with previous month
5. Rank employees by salary within department
6. Calculate percentage contribution to total sales
7. Find customers with decreasing order amounts
8. Calculate year-over-year growth rate

