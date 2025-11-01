# SQL 5: Aggregate Queries

## What are Aggregate Functions?
**Aggregate functions** perform calculations on multiple rows and return a single result. They're used to summarize data.

Think of them as Excel formulas like SUM, AVERAGE, COUNT, etc.

## Basic Aggregate Functions

### 1. COUNT()
Counts the number of rows.

```sql
-- Count total number of students
SELECT COUNT(*) AS total_students
FROM students;

-- Count students with grade A
SELECT COUNT(*) AS a_students
FROM students
WHERE grade = 'A';

-- Count non-NULL values in a column
SELECT COUNT(email) AS students_with_email
FROM students;

-- Count distinct values
SELECT COUNT(DISTINCT grade) AS unique_grades
FROM students;
```

**Example Output:**
```
total_students: 100
a_students: 25
students_with_email: 98
unique_grades: 5
```

### 2. SUM()
Adds up all values in a column.

```sql
-- Total sales amount
SELECT SUM(amount) AS total_sales
FROM orders;

-- Total sales for customer 1
SELECT SUM(amount) AS customer_1_total
FROM orders
WHERE customer_id = 1;

-- Total salary budget for IT department
SELECT SUM(salary) AS it_budget
FROM employees
WHERE department = 'IT';
```

### 3. AVG()
Calculates the average (mean) value.

```sql
-- Average product price
SELECT AVG(price) AS avg_price
FROM products;

-- Average age of students
SELECT AVG(age) AS avg_age
FROM students;

-- Average salary in IT department
SELECT AVG(salary) AS avg_it_salary
FROM employees
WHERE department = 'IT';
```

### 4. MAX()
Finds the maximum (highest) value.

```sql
-- Highest product price
SELECT MAX(price) AS highest_price
FROM products;

-- Oldest student
SELECT MAX(age) AS oldest_student_age
FROM students;

-- Latest order date
SELECT MAX(order_date) AS latest_order
FROM orders;
```

### 5. MIN()
Finds the minimum (lowest) value.

```sql
-- Lowest product price
SELECT MIN(price) AS lowest_price
FROM products;

-- Youngest student
SELECT MIN(age) AS youngest_student_age
FROM students;

-- Earliest order date
SELECT MIN(order_date) AS first_order
FROM orders;
```

## GROUP BY - Grouping Data

**GROUP BY** groups rows with the same values and applies aggregate functions to each group.

### Basic GROUP BY

```sql
-- Count students in each grade
SELECT 
    grade,
    COUNT(*) AS student_count
FROM students
GROUP BY grade;
```

**Result:**
| grade | student_count |
|-------|---------------|
| A     | 25            |
| B     | 30            |
| C     | 20            |
| D     | 15            |
| F     | 10            |

### Multiple Aggregates

```sql
-- Statistics by department
SELECT 
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary,
    SUM(salary) AS total_salary
FROM employees
GROUP BY department;
```

**Result:**
| department | employee_count | avg_salary | min_salary | max_salary | total_salary |
|------------|----------------|------------|------------|------------|--------------|
| IT         | 50             | 75000      | 60000      | 120000     | 3750000      |
| HR         | 20             | 65000      | 55000      | 80000      | 1300000      |
| Finance    | 25             | 70000      | 60000      | 90000      | 1750000      |

### GROUP BY Multiple Columns

```sql
-- Count students by grade and age
SELECT 
    grade,
    age,
    COUNT(*) AS count
FROM students
GROUP BY grade, age
ORDER BY grade, age;
```

**Result:**
| grade | age | count |
|-------|-----|-------|
| A     | 18  | 10    |
| A     | 19  | 15    |
| B     | 18  | 12    |
| B     | 19  | 18    |

## HAVING Clause

**HAVING** filters groups (used with GROUP BY). It's like WHERE, but for groups.

**WHERE** vs **HAVING**:
- **WHERE**: Filters individual rows BEFORE grouping
- **HAVING**: Filters groups AFTER grouping

```sql
-- Find departments with more than 20 employees
SELECT 
    department,
    COUNT(*) AS employee_count
FROM employees
GROUP BY department
HAVING COUNT(*) > 20;

-- Find grades with average age greater than 19
SELECT 
    grade,
    AVG(age) AS avg_age
FROM students
GROUP BY grade
HAVING AVG(age) > 19;

-- Find products with total sales > 10000
SELECT 
    product_id,
    SUM(quantity * price) AS total_sales
FROM order_items
GROUP BY product_id
HAVING SUM(quantity * price) > 10000;
```

### WHERE + GROUP BY + HAVING

```sql
-- Find IT and HR departments with avg salary > 70000
SELECT 
    department,
    AVG(salary) AS avg_salary
FROM employees
WHERE department IN ('IT', 'HR')  -- Filter rows first
GROUP BY department
HAVING AVG(salary) > 70000;       -- Filter groups after

-- Find grade A students' age distribution, where count > 5
SELECT 
    age,
    COUNT(*) AS count
FROM students
WHERE grade = 'A'                 -- Filter rows first
GROUP BY age
HAVING COUNT(*) > 5               -- Filter groups after
ORDER BY age;
```

## Practical Examples

### Example 1: Sales Analysis

```sql
-- Create tables
CREATE TABLE sales (
    sale_id INT PRIMARY KEY,
    product VARCHAR(100),
    category VARCHAR(50),
    quantity INT,
    price DECIMAL(10,2),
    sale_date DATE
);

-- Insert sample data
INSERT INTO sales VALUES
(1, 'Laptop', 'Electronics', 2, 1200.00, '2024-01-15'),
(2, 'Mouse', 'Electronics', 10, 25.00, '2024-01-16'),
(3, 'Desk', 'Furniture', 5, 300.00, '2024-01-17'),
(4, 'Chair', 'Furniture', 8, 150.00, '2024-01-18'),
(5, 'Keyboard', 'Electronics', 15, 75.00, '2024-01-19'),
(6, 'Monitor', 'Electronics', 3, 400.00, '2024-01-20');

-- Query 1: Total revenue
SELECT SUM(quantity * price) AS total_revenue
FROM sales;
-- Result: 8,575.00

-- Query 2: Revenue by category
SELECT 
    category,
    SUM(quantity * price) AS revenue,
    COUNT(*) AS number_of_sales,
    AVG(quantity * price) AS avg_sale_value
FROM sales
GROUP BY category;

-- Result:
-- Electronics | 5,875.00 | 4 | 1,468.75
-- Furniture   | 2,700.00 | 2 | 1,350.00

-- Query 3: Top selling products (by quantity)
SELECT 
    product,
    SUM(quantity) AS total_quantity,
    SUM(quantity * price) AS revenue
FROM sales
GROUP BY product
ORDER BY total_quantity DESC
LIMIT 5;

-- Query 4: Categories with revenue > 5000
SELECT 
    category,
    SUM(quantity * price) AS revenue
FROM sales
GROUP BY category
HAVING SUM(quantity * price) > 5000;

-- Result: Electronics (5,875.00)

-- Query 5: Daily sales summary
SELECT 
    sale_date,
    COUNT(*) AS number_of_sales,
    SUM(quantity) AS items_sold,
    SUM(quantity * price) AS daily_revenue
FROM sales
GROUP BY sale_date
ORDER BY sale_date;
```

### Example 2: Student Performance Analysis

```sql
-- Create tables
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

-- Query 1: Average score by student
SELECT 
    student_name,
    AVG(score) AS avg_score,
    MAX(score) AS best_score,
    MIN(score) AS worst_score,
    COUNT(*) AS subjects_taken
FROM student_scores
GROUP BY student_name
ORDER BY avg_score DESC;

-- Result:
-- Charlie | 91.67 | 95 | 88 | 3
-- Alice   | 91.67 | 95 | 88 | 3
-- Bob     | 81.00 | 85 | 78 | 3

-- Query 2: Average score by subject
SELECT 
    subject,
    AVG(score) AS avg_score,
    MAX(score) AS highest_score,
    MIN(score) AS lowest_score,
    COUNT(*) AS student_count
FROM student_scores
GROUP BY subject;

-- Result:
-- Math    | 88.33 | 95 | 78 | 3
-- Science | 89.33 | 95 | 85 | 3
-- English | 86.67 | 92 | 80 | 3

-- Query 3: Students with average score > 85
SELECT 
    student_name,
    AVG(score) AS avg_score
FROM student_scores
GROUP BY student_name
HAVING AVG(score) > 85;

-- Result: Alice, Charlie

-- Query 4: Subjects where no one scored below 80
SELECT subject
FROM student_scores
GROUP BY subject
HAVING MIN(score) >= 80;

-- Result: Science, English
```

### Example 3: E-commerce Order Analysis

```sql
-- Create tables
CREATE TABLE order_data (
    order_id INT,
    customer_id INT,
    customer_name VARCHAR(100),
    product VARCHAR(100),
    quantity INT,
    price DECIMAL(10,2),
    order_date DATE
);

-- Insert sample data
INSERT INTO order_data VALUES
(101, 1, 'Alice', 'Laptop', 1, 1200.00, '2024-01-01'),
(101, 1, 'Alice', 'Mouse', 2, 25.00, '2024-01-01'),
(102, 1, 'Alice', 'Keyboard', 1, 75.00, '2024-01-15'),
(103, 2, 'Bob', 'Monitor', 2, 400.00, '2024-01-10'),
(104, 3, 'Charlie', 'Laptop', 1, 1200.00, '2024-01-12'),
(105, 2, 'Bob', 'Mouse', 5, 25.00, '2024-01-20');

-- Query 1: Total spent by each customer
SELECT 
    customer_name,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(quantity) AS total_items,
    SUM(quantity * price) AS total_spent
FROM order_data
GROUP BY customer_name
ORDER BY total_spent DESC;

-- Result:
-- Alice   | 2 | 4  | 1,325.00
-- Charlie | 1 | 1  | 1,200.00
-- Bob     | 2 | 7  | 925.00

-- Query 2: Most popular products
SELECT 
    product,
    SUM(quantity) AS total_sold,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(quantity * price) AS revenue
FROM order_data
GROUP BY product
ORDER BY total_sold DESC;

-- Query 3: Customers who spent more than 1000
SELECT 
    customer_name,
    SUM(quantity * price) AS total_spent
FROM order_data
GROUP BY customer_name
HAVING SUM(quantity * price) > 1000;

-- Result: Alice, Charlie

-- Query 4: Products sold to more than 1 customer
SELECT 
    product,
    COUNT(DISTINCT customer_id) AS customer_count
FROM order_data
GROUP BY product
HAVING COUNT(DISTINCT customer_id) > 1;

-- Result: Laptop (2), Mouse (2)

-- Query 5: Monthly sales summary
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(quantity * price) AS revenue
FROM order_data
GROUP BY DATE_FORMAT(order_date, '%Y-%m');
```

### Example 4: Employee Analytics

```sql
-- Create table
CREATE TABLE employee_data (
    emp_id INT,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE,
    city VARCHAR(50)
);

-- Insert sample data
INSERT INTO employee_data VALUES
(1, 'Alice', 'IT', 75000, '2020-01-15', 'New York'),
(2, 'Bob', 'IT', 80000, '2019-03-20', 'New York'),
(3, 'Charlie', 'HR', 65000, '2021-05-10', 'Chicago'),
(4, 'Diana', 'Finance', 70000, '2020-07-12', 'New York'),
(5, 'Eve', 'IT', 72000, '2022-02-01', 'Chicago'),
(6, 'Frank', 'HR', 60000, '2021-09-15', 'Chicago'),
(7, 'Grace', 'Finance', 75000, '2020-11-20', 'New York');

-- Query 1: Department statistics
SELECT 
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary
FROM employee_data
GROUP BY department;

-- Query 2: City-wise distribution
SELECT 
    city,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary
FROM employee_data
GROUP BY city;

-- Query 3: Departments with average salary > 70000
SELECT 
    department,
    AVG(salary) AS avg_salary
FROM employee_data
GROUP BY department
HAVING AVG(salary) > 70000;

-- Result: IT (75,666.67)

-- Query 4: City + Department breakdown
SELECT 
    city,
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary
FROM employee_data
GROUP BY city, department
ORDER BY city, department;

-- Query 5: Years with most hires
SELECT 
    YEAR(hire_date) AS hire_year,
    COUNT(*) AS hires
FROM employee_data
GROUP BY YEAR(hire_date)
ORDER BY hires DESC;
```

## Advanced Techniques

### Using ROUND() with Aggregates

```sql
-- Round average to 2 decimal places
SELECT 
    department,
    ROUND(AVG(salary), 2) AS avg_salary
FROM employees
GROUP BY department;
```

### Percentage Calculations

```sql
-- Calculate percentage of total
SELECT 
    category,
    SUM(quantity * price) AS revenue,
    ROUND(
        SUM(quantity * price) * 100.0 / 
        (SELECT SUM(quantity * price) FROM sales),
        2
    ) AS percentage_of_total
FROM sales
GROUP BY category;
```

### Combining with Joins

```sql
-- Revenue by customer with customer details
SELECT 
    c.customer_name,
    c.city,
    COUNT(o.order_id) AS order_count,
    SUM(o.amount) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_name, c.city
ORDER BY total_spent DESC;
```

## Key Takeaways

1. **Aggregate Functions**:
   - COUNT(): Count rows
   - SUM(): Add values
   - AVG(): Calculate average
   - MAX(): Find maximum
   - MIN(): Find minimum

2. **GROUP BY**: Groups rows with same values

3. **HAVING**: Filters groups (like WHERE for groups)

4. **Order of Execution**:
   ```
   FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
   ```

5. **Important Rules**:
   - Every column in SELECT must be either in GROUP BY or an aggregate function
   - Use WHERE to filter rows before grouping
   - Use HAVING to filter groups after grouping
   - Can't use WHERE with aggregate functions (use HAVING)

## Common Mistakes to Avoid

### Mistake 1: Missing GROUP BY
```sql
-- WRONG - name is not aggregated or in GROUP BY
SELECT name, AVG(salary)
FROM employees;

-- CORRECT
SELECT name, AVG(salary)
FROM employees
GROUP BY name;
```

### Mistake 2: Using WHERE with Aggregates
```sql
-- WRONG - Can't use aggregate in WHERE
SELECT department
FROM employees
WHERE AVG(salary) > 70000;

-- CORRECT - Use HAVING
SELECT department
FROM employees
GROUP BY department
HAVING AVG(salary) > 70000;
```

## Practice Exercises

1. Find the total number of orders per customer
2. Calculate average order value by month
3. Find products with more than 100 units sold
4. List departments with more than 10 employees
5. Find the top 5 customers by total spending
6. Calculate the percentage distribution of grades
7. Find subjects where average score is below 70
8. List cities with average salary > 75000

