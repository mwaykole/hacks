# SQL 7: Subqueries & Views

## What are Subqueries?
A **subquery** (or nested query) is a query inside another query. The inner query runs first, and its result is used by the outer query.

Think of it as asking a question within a question!

## Types of Subqueries

### 1. Single Value Subquery
Returns a single value (one row, one column).

```sql
-- Find employees with salary greater than average
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- Find the employee with the highest salary
SELECT name, salary
FROM employees
WHERE salary = (SELECT MAX(salary) FROM employees);
```

### 2. Multiple Value Subquery
Returns multiple values (multiple rows, one column).

```sql
-- Find students enrolled in Math or Science
SELECT name
FROM students
WHERE student_id IN (
    SELECT student_id
    FROM enrollments
    WHERE course_id IN (101, 102)
);

-- Find employees in departments with more than 10 people
SELECT name, department
FROM employees
WHERE department IN (
    SELECT department
    FROM employees
    GROUP BY department
    HAVING COUNT(*) > 10
);
```

### 3. Multiple Column Subquery
Returns multiple columns.

```sql
-- Find employees with same (department, salary) as someone hired in 2023
SELECT name, department, salary
FROM employees
WHERE (department, salary) IN (
    SELECT department, salary
    FROM employees
    WHERE YEAR(hire_date) = 2023
);
```

### 4. Correlated Subquery
The inner query depends on the outer query. It runs once for each row.

```sql
-- Find employees earning more than their department's average
SELECT e1.name, e1.department, e1.salary
FROM employees e1
WHERE salary > (
    SELECT AVG(salary)
    FROM employees e2
    WHERE e2.department = e1.department
);

-- Find students with above-average scores in their own grade
SELECT s1.name, s1.grade, s1.score
FROM students s1
WHERE score > (
    SELECT AVG(score)
    FROM students s2
    WHERE s2.grade = s1.grade
);
```

## Subquery Operators

### IN Operator
```sql
-- Find customers who placed orders
SELECT name
FROM customers
WHERE customer_id IN (
    SELECT DISTINCT customer_id
    FROM orders
);
```

### NOT IN Operator
```sql
-- Find customers who never placed orders
SELECT name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
);
```

### EXISTS Operator
Checks if subquery returns any rows (faster than IN for large datasets).

```sql
-- Find customers who have placed orders
SELECT name
FROM customers c
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);
```

### NOT EXISTS Operator
```sql
-- Find customers who never placed orders
SELECT name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);
```

### ANY / SOME Operator
```sql
-- Find employees earning more than ANY employee in HR
SELECT name, salary
FROM employees
WHERE salary > ANY (
    SELECT salary
    FROM employees
    WHERE department = 'HR'
);
-- Same as: salary > minimum salary in HR
```

### ALL Operator
```sql
-- Find employees earning more than ALL employees in HR
SELECT name, salary
FROM employees
WHERE salary > ALL (
    SELECT salary
    FROM employees
    WHERE department = 'HR'
);
-- Same as: salary > maximum salary in HR
```

## Subquery in Different Clauses

### 1. Subquery in SELECT Clause
```sql
-- Show each employee with department average salary
SELECT 
    name,
    salary,
    department,
    (SELECT AVG(salary) 
     FROM employees e2 
     WHERE e2.department = e1.department) AS dept_avg_salary
FROM employees e1;
```

### 2. Subquery in FROM Clause (Derived Table)
```sql
-- Find departments with average salary > 70000
SELECT dept, avg_sal
FROM (
    SELECT 
        department AS dept,
        AVG(salary) AS avg_sal
    FROM employees
    GROUP BY department
) AS dept_averages
WHERE avg_sal > 70000;
```

### 3. Subquery in WHERE Clause
```sql
-- Find products more expensive than average
SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);
```

### 4. Subquery in HAVING Clause
```sql
-- Find departments with total salary > company average
SELECT department, SUM(salary) AS total_salary
FROM employees
GROUP BY department
HAVING SUM(salary) > (
    SELECT AVG(dept_total)
    FROM (
        SELECT SUM(salary) AS dept_total
        FROM employees
        GROUP BY department
    ) AS dept_totals
);
```

## Practical Examples

### Example 1: E-commerce Analysis

```sql
-- Create tables
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    amount DECIMAL(10,2)
);

-- Insert data
INSERT INTO customers VALUES
(1, 'Alice', 'alice@email.com'),
(2, 'Bob', 'bob@email.com'),
(3, 'Charlie', 'charlie@email.com'),
(4, 'Diana', 'diana@email.com');

INSERT INTO orders VALUES
(101, 1, '2024-01-15', 500.00),
(102, 1, '2024-02-20', 750.00),
(103, 2, '2024-01-25', 300.00),
(104, 3, '2024-03-10', 1000.00);

-- Query 1: Customers who spent more than average
SELECT name
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    GROUP BY customer_id
    HAVING SUM(amount) > (SELECT AVG(total) FROM (
        SELECT SUM(amount) AS total
        FROM orders
        GROUP BY customer_id
    ) AS customer_totals)
);

-- Query 2: Customers who never ordered
SELECT name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id FROM orders
);
-- Result: Diana

-- Query 3: Orders above average order value
SELECT 
    order_id,
    customer_id,
    amount,
    (SELECT AVG(amount) FROM orders) AS avg_order_value
FROM orders
WHERE amount > (SELECT AVG(amount) FROM orders);

-- Query 4: Customer with highest total spending
SELECT 
    c.name,
    (SELECT SUM(amount) 
     FROM orders o 
     WHERE o.customer_id = c.customer_id) AS total_spent
FROM customers c
ORDER BY total_spent DESC
LIMIT 1;
```

### Example 2: Employee Management

```sql
-- Create table
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    manager_id INT
);

-- Insert data
INSERT INTO employees VALUES
(1, 'Alice', 'IT', 90000, NULL),
(2, 'Bob', 'IT', 75000, 1),
(3, 'Charlie', 'IT', 70000, 1),
(4, 'Diana', 'HR', 80000, NULL),
(5, 'Eve', 'HR', 65000, 4),
(6, 'Frank', 'Finance', 85000, NULL),
(7, 'Grace', 'Finance', 70000, 6);

-- Query 1: Employees earning more than their department's average
SELECT 
    name,
    department,
    salary,
    (SELECT AVG(salary) 
     FROM employees e2 
     WHERE e2.department = e1.department) AS dept_avg
FROM employees e1
WHERE salary > (
    SELECT AVG(salary)
    FROM employees e2
    WHERE e2.department = e1.department
);

-- Query 2: Employees earning more than their manager
SELECT 
    e.name AS employee,
    e.salary AS emp_salary,
    m.name AS manager,
    m.salary AS mgr_salary
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id
WHERE e.salary > m.salary;

-- Query 3: Departments with all employees earning > 65000
SELECT DISTINCT department
FROM employees e1
WHERE NOT EXISTS (
    SELECT 1
    FROM employees e2
    WHERE e2.department = e1.department
    AND e2.salary <= 65000
);

-- Query 4: Second highest salary
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Query 5: Nth highest salary (e.g., 3rd highest)
SELECT DISTINCT salary
FROM employees e1
WHERE 3 = (
    SELECT COUNT(DISTINCT salary)
    FROM employees e2
    WHERE e2.salary >= e1.salary
);
```

### Example 3: Student Performance

```sql
-- Create tables
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100),
    grade CHAR(1)
);

CREATE TABLE exam_scores (
    score_id INT PRIMARY KEY,
    student_id INT,
    subject VARCHAR(50),
    score INT
);

-- Insert data
INSERT INTO students VALUES
(1, 'Alice', 'A'),
(2, 'Bob', 'B'),
(3, 'Charlie', 'A'),
(4, 'Diana', 'C');

INSERT INTO exam_scores VALUES
(1, 1, 'Math', 95),
(2, 1, 'Science', 88),
(3, 2, 'Math', 78),
(4, 2, 'Science', 85),
(5, 3, 'Math', 92),
(6, 3, 'Science', 90),
(7, 4, 'Math', 70),
(8, 4, 'Science', 75);

-- Query 1: Students scoring above subject average
SELECT 
    s.name,
    e.subject,
    e.score,
    (SELECT AVG(score) 
     FROM exam_scores e2 
     WHERE e2.subject = e.subject) AS subject_avg
FROM students s
JOIN exam_scores e ON s.student_id = e.student_id
WHERE e.score > (
    SELECT AVG(score)
    FROM exam_scores e2
    WHERE e2.subject = e.subject
);

-- Query 2: Students with all scores above 80
SELECT name
FROM students s
WHERE NOT EXISTS (
    SELECT 1
    FROM exam_scores e
    WHERE e.student_id = s.student_id
    AND e.score < 80
);
-- Result: Alice, Charlie

-- Query 3: Top performing student in each subject
SELECT subject, name, score
FROM (
    SELECT 
        e.subject,
        s.name,
        e.score,
        (SELECT MAX(score) 
         FROM exam_scores e2 
         WHERE e2.subject = e.subject) AS max_score
    FROM exam_scores e
    JOIN students s ON e.student_id = s.student_id
) AS scores_with_max
WHERE score = max_score;

-- Query 4: Students with average score > overall class average
SELECT 
    s.name,
    AVG(e.score) AS avg_score
FROM students s
JOIN exam_scores e ON s.student_id = e.student_id
GROUP BY s.name
HAVING AVG(e.score) > (SELECT AVG(score) FROM exam_scores);
```

## VIEWS

### What are Views?
A **view** is a virtual table based on a SQL query. It doesn't store data itself but shows data from underlying tables.

Think of a view as a saved query that you can treat like a table!

### Why Use Views?

1. **Simplify Complex Queries**: Save complicated joins/subqueries
2. **Security**: Hide sensitive columns from users
3. **Reusability**: Use the same query multiple times
4. **Abstraction**: Hide complexity from users

### Creating Views

#### Basic Syntax:
```sql
CREATE VIEW view_name AS
SELECT column1, column2, ...
FROM table_name
WHERE condition;
```

#### Example 1: Simple View
```sql
-- Create view of active employees
CREATE VIEW active_employees AS
SELECT emp_id, name, department, salary
FROM employees
WHERE status = 'active';

-- Use the view like a table
SELECT * FROM active_employees;
SELECT * FROM active_employees WHERE department = 'IT';
```

#### Example 2: View with Joins
```sql
-- Create view of customer order details
CREATE VIEW customer_orders AS
SELECT 
    c.customer_id,
    c.name AS customer_name,
    o.order_id,
    o.order_date,
    o.amount
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;

-- Use it
SELECT * FROM customer_orders WHERE customer_name = 'Alice';
```

#### Example 3: View with Aggregates
```sql
-- Create view of department statistics
CREATE VIEW department_stats AS
SELECT 
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_salary,
    SUM(salary) AS total_salary
FROM employees
GROUP BY department;

-- Use it
SELECT * FROM department_stats WHERE avg_salary > 70000;
```

#### Example 4: View with Subquery
```sql
-- Create view of high performers
CREATE VIEW high_performers AS
SELECT 
    name,
    department,
    salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- Use it
SELECT * FROM high_performers ORDER BY salary DESC;
```

### Modifying Views

#### Replace Existing View:
```sql
CREATE OR REPLACE VIEW active_employees AS
SELECT emp_id, name, department, salary, hire_date
FROM employees
WHERE status = 'active';
```

#### Alter View:
```sql
ALTER VIEW active_employees AS
SELECT emp_id, name, department
FROM employees
WHERE status = 'active';
```

### Dropping Views

```sql
DROP VIEW active_employees;

-- Drop only if exists (no error if doesn't exist)
DROP VIEW IF EXISTS active_employees;
```

### Updatable Views

Some views allow INSERT, UPDATE, DELETE operations:

```sql
-- Create simple view
CREATE VIEW it_employees AS
SELECT emp_id, name, salary
FROM employees
WHERE department = 'IT';

-- Update through view
UPDATE it_employees
SET salary = salary * 1.10
WHERE emp_id = 5;

-- This updates the underlying employees table!
```

**Requirements for Updatable Views:**
- No aggregate functions (SUM, AVG, etc.)
- No DISTINCT
- No GROUP BY or HAVING
- No UNION
- FROM clause has only one table

### Views vs. Tables

| Feature      | Table                 | View                        |
|--------------|-----------------------|-----------------------------|
| Storage      | Stores actual data    | Stores only query           |
| Performance  | Faster                | May be slower (depends)     |
| Space        | Takes disk space      | Minimal space               |
| Update       | Directly updatable    | Sometimes updatable         |
| Purpose      | Store data            | Simplify/secure access      |

## Practical View Examples

### Example 1: E-commerce Dashboard

```sql
-- View: Customer summary
CREATE VIEW customer_summary AS
SELECT 
    c.customer_id,
    c.name,
    c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.amount), 0) AS total_spent,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.email;

-- View: Top customers
CREATE VIEW top_customers AS
SELECT *
FROM customer_summary
WHERE total_spent > 1000
ORDER BY total_spent DESC;

-- View: Inactive customers (no orders in 6 months)
CREATE VIEW inactive_customers AS
SELECT *
FROM customer_summary
WHERE last_order_date < DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
   OR last_order_date IS NULL;
```

### Example 2: Employee Dashboard

```sql
-- View: Employee full details
CREATE VIEW employee_details AS
SELECT 
    e.emp_id,
    e.name,
    e.department,
    e.salary,
    e.hire_date,
    m.name AS manager_name,
    TIMESTAMPDIFF(YEAR, e.hire_date, CURDATE()) AS years_of_service
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id;

-- View: Department overview
CREATE VIEW department_overview AS
SELECT 
    department,
    COUNT(*) AS employee_count,
    ROUND(AVG(salary), 2) AS avg_salary,
    MIN(salary) AS min_salary,
    MAX(salary) AS max_salary,
    SUM(salary) AS payroll
FROM employees
GROUP BY department;

-- View: Senior employees
CREATE VIEW senior_employees AS
SELECT *
FROM employee_details
WHERE years_of_service >= 5;
```

### Example 3: Academic System

```sql
-- View: Student performance
CREATE VIEW student_performance AS
SELECT 
    s.student_id,
    s.name,
    COUNT(e.score_id) AS exams_taken,
    AVG(e.score) AS average_score,
    MIN(e.score) AS lowest_score,
    MAX(e.score) AS highest_score
FROM students s
LEFT JOIN exam_scores e ON s.student_id = e.student_id
GROUP BY s.student_id, s.name;

-- View: Honor students
CREATE VIEW honor_students AS
SELECT *
FROM student_performance
WHERE average_score >= 90;

-- View: At-risk students
CREATE VIEW at_risk_students AS
SELECT *
FROM student_performance
WHERE average_score < 70;
```

## Key Takeaways

### Subqueries:
1. Query within a query
2. Types: Single value, multiple value, correlated
3. Use with: SELECT, FROM, WHERE, HAVING
4. Operators: IN, NOT IN, EXISTS, ANY, ALL

### Views:
1. Virtual table based on a query
2. Simplifies complex queries
3. Provides security/abstraction
4. Can sometimes be updated
5. Doesn't store data (just the query)

## Common Interview Questions

**Q1: Difference between subquery and join?**
- Both can achieve similar results
- Joins often faster for large datasets
- Subqueries more readable for complex logic

**Q2: When to use EXISTS vs IN?**
- EXISTS: Better for large subquery results (stops at first match)
- IN: Better for small subquery results

**Q3: Can you update data through a view?**
- Yes, if view meets criteria (no aggregates, no GROUP BY, single table, etc.)

## Practice Exercises

1. Find employees earning more than company average
2. Find customers who ordered all available products
3. Create view of monthly sales summary
4. Find students who scored above average in every subject
5. Create view of departments with their top earner
6. Find products never ordered
7. Create view of customer lifetime value
8. Find employees earning more than any manager

