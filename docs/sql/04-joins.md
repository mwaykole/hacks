# SQL 4: Joins

## What are Joins?
**Joins** combine data from two or more tables based on a related column. This is one of the most powerful features of SQL!

Think of it like matching puzzle pieces - we connect tables using common information.

## Sample Tables for Examples

Let's create two related tables:

```sql
-- Customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(50)
);

INSERT INTO customers VALUES
(1, 'Alice', 'New York'),
(2, 'Bob', 'Los Angeles'),
(3, 'Charlie', 'Chicago'),
(4, 'Diana', 'Houston');

-- Orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product VARCHAR(100),
    amount DECIMAL(10,2)
);

INSERT INTO orders VALUES
(101, 1, 'Laptop', 1200.00),
(102, 1, 'Mouse', 25.00),
(103, 2, 'Keyboard', 75.00),
(104, 3, 'Monitor', 300.00),
(105, 999, 'Phone', 800.00);  -- customer_id 999 doesn't exist
```

**Customers Table:**
| customer_id | name    | city        |
|-------------|---------|-------------|
| 1           | Alice   | New York    |
| 2           | Bob     | Los Angeles |
| 3           | Charlie | Chicago     |
| 4           | Diana   | Houston     |

**Orders Table:**
| order_id | customer_id | product  | amount  |
|----------|-------------|----------|---------|
| 101      | 1           | Laptop   | 1200.00 |
| 102      | 1           | Mouse    | 25.00   |
| 103      | 2           | Keyboard | 75.00   |
| 104      | 3           | Monitor  | 300.00  |
| 105      | 999         | Phone    | 800.00  |

## Types of Joins

### 1. INNER JOIN
Returns only matching rows from both tables.

**Visual**: Only the overlapping part of two circles.

```sql
SELECT 
    customers.name,
    customers.city,
    orders.product,
    orders.amount
FROM customers
INNER JOIN orders ON customers.customer_id = orders.customer_id;
```

**Result:**
| name    | city        | product  | amount  |
|---------|-------------|----------|---------|
| Alice   | New York    | Laptop   | 1200.00 |
| Alice   | New York    | Mouse    | 25.00   |
| Bob     | Los Angeles | Keyboard | 75.00   |
| Charlie | Chicago     | Monitor  | 300.00  |

**Notice**: 
- Diana (no orders) is excluded
- Order 105 (customer doesn't exist) is excluded

### 2. LEFT JOIN (LEFT OUTER JOIN)
Returns ALL rows from the left table, matching rows from the right table.

**Visual**: Entire left circle + overlapping part.

```sql
SELECT 
    customers.name,
    customers.city,
    orders.product,
    orders.amount
FROM customers
LEFT JOIN orders ON customers.customer_id = orders.customer_id;
```

**Result:**
| name    | city        | product  | amount  |
|---------|-------------|----------|---------|
| Alice   | New York    | Laptop   | 1200.00 |
| Alice   | New York    | Mouse    | 25.00   |
| Bob     | Los Angeles | Keyboard | 75.00   |
| Charlie | Chicago     | Monitor  | 300.00  |
| Diana   | Houston     | NULL     | NULL    |

**Notice**: Diana is included even though she has no orders (NULL values).

### 3. RIGHT JOIN (RIGHT OUTER JOIN)
Returns ALL rows from the right table, matching rows from the left table.

**Visual**: Entire right circle + overlapping part.

```sql
SELECT 
    customers.name,
    customers.city,
    orders.product,
    orders.amount
FROM customers
RIGHT JOIN orders ON customers.customer_id = orders.customer_id;
```

**Result:**
| name    | city        | product  | amount  |
|---------|-------------|----------|---------|
| Alice   | New York    | Laptop   | 1200.00 |
| Alice   | New York    | Mouse    | 25.00   |
| Bob     | Los Angeles | Keyboard | 75.00   |
| Charlie | Chicago     | Monitor  | 300.00  |
| NULL    | NULL        | Phone    | 800.00  |

**Notice**: Order 105 is included even though customer doesn't exist.

### 4. FULL OUTER JOIN
Returns ALL rows from both tables, matching where possible.

**Visual**: Both circles completely.

```sql
-- MySQL doesn't support FULL OUTER JOIN directly
-- We use UNION of LEFT and RIGHT joins
SELECT 
    customers.name,
    customers.city,
    orders.product,
    orders.amount
FROM customers
LEFT JOIN orders ON customers.customer_id = orders.customer_id

UNION

SELECT 
    customers.name,
    customers.city,
    orders.product,
    orders.amount
FROM customers
RIGHT JOIN orders ON customers.customer_id = orders.customer_id;
```

**Result:**
| name    | city        | product  | amount  |
|---------|-------------|----------|---------|
| Alice   | New York    | Laptop   | 1200.00 |
| Alice   | New York    | Mouse    | 25.00   |
| Bob     | Los Angeles | Keyboard | 75.00   |
| Charlie | Chicago     | Monitor  | 300.00  |
| Diana   | Houston     | NULL     | NULL    |
| NULL    | NULL        | Phone    | 800.00  |

### 5. CROSS JOIN
Returns the Cartesian product (every possible combination).

```sql
SELECT 
    customers.name,
    orders.product
FROM customers
CROSS JOIN orders;
```

**Result**: 4 customers × 5 orders = 20 rows (every customer paired with every order)

**Use case**: Rarely used, but useful for generating combinations.

### 6. SELF JOIN
Joining a table with itself.

```sql
-- Employee table with manager_id
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    manager_id INT
);

INSERT INTO employees VALUES
(1, 'Alice', NULL),      -- CEO, no manager
(2, 'Bob', 1),          -- Reports to Alice
(3, 'Charlie', 1),      -- Reports to Alice
(4, 'Diana', 2),        -- Reports to Bob
(5, 'Eve', 2);          -- Reports to Bob

-- Find each employee with their manager's name
SELECT 
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id;
```

**Result:**
| employee | manager |
|----------|---------|
| Alice    | NULL    |
| Bob      | Alice   |
| Charlie  | Alice   |
| Diana    | Bob     |
| Eve      | Bob     |

## Practical Examples

### Example 1: School System

```sql
-- Create tables
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100),
    age INT
);

CREATE TABLE courses (
    course_id INT PRIMARY KEY,
    course_name VARCHAR(100)
);

CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY,
    student_id INT,
    course_id INT,
    grade CHAR(1)
);

-- Insert data
INSERT INTO students VALUES
(1, 'Alice', 20),
(2, 'Bob', 21),
(3, 'Charlie', 19),
(4, 'Diana', 20);

INSERT INTO courses VALUES
(101, 'Math'),
(102, 'Science'),
(103, 'History'),
(104, 'Art');

INSERT INTO enrollments VALUES
(1, 1, 101, 'A'),
(2, 1, 102, 'B'),
(3, 2, 101, 'B'),
(4, 3, 103, 'A');

-- Query 1: Which students are taking which courses?
SELECT 
    s.name AS student,
    c.course_name AS course,
    e.grade
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c ON e.course_id = c.course_id;

-- Result:
-- Alice    | Math    | A
-- Alice    | Science | B
-- Bob      | Math    | B
-- Charlie  | History | A

-- Query 2: Show all students and their courses (including students with no courses)
SELECT 
    s.name AS student,
    c.course_name AS course,
    e.grade
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
LEFT JOIN courses c ON e.course_id = c.course_id;

-- Result includes Diana with NULL course

-- Query 3: Which courses have no students?
SELECT c.course_name
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
WHERE e.enrollment_id IS NULL;

-- Result: Art (no one enrolled)
```

### Example 2: E-commerce System

```sql
-- Create tables
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10,2)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT
);

-- Insert data
INSERT INTO products VALUES
(1, 'Laptop', 1200.00),
(2, 'Mouse', 25.00),
(3, 'Keyboard', 75.00),
(4, 'Monitor', 300.00);

INSERT INTO customers VALUES
(1, 'Alice', 'alice@email.com'),
(2, 'Bob', 'bob@email.com'),
(3, 'Charlie', 'charlie@email.com');

INSERT INTO orders VALUES
(101, 1, '2024-01-15'),
(102, 1, '2024-02-20'),
(103, 2, '2024-01-25');

INSERT INTO order_items VALUES
(1, 101, 1, 1),  -- Alice ordered 1 Laptop
(2, 101, 2, 2),  -- Alice ordered 2 Mice
(3, 102, 3, 1),  -- Alice ordered 1 Keyboard
(4, 103, 4, 2);  -- Bob ordered 2 Monitors

-- Query 1: Show all order details with customer and product info
SELECT 
    c.name AS customer,
    o.order_date,
    p.product_name,
    oi.quantity,
    p.price,
    (oi.quantity * p.price) AS total
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id;

-- Query 2: Find customers who never placed an order
SELECT c.name, c.email
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- Result: Charlie (never ordered)

-- Query 3: Find products that were never ordered
SELECT p.product_name
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;

-- Query 4: Total spent by each customer
SELECT 
    c.name,
    SUM(oi.quantity * p.price) AS total_spent
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
GROUP BY c.name;
```

### Example 3: Employee Management

```sql
-- Create tables
CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100)
);

CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    salary DECIMAL(10,2)
);

CREATE TABLE projects (
    project_id INT PRIMARY KEY,
    project_name VARCHAR(100)
);

CREATE TABLE emp_projects (
    emp_id INT,
    project_id INT,
    role VARCHAR(50),
    PRIMARY KEY (emp_id, project_id)
);

-- Insert data
INSERT INTO departments VALUES
(1, 'IT'),
(2, 'HR'),
(3, 'Finance'),
(4, 'Marketing');

INSERT INTO employees VALUES
(1, 'Alice', 1, 75000),
(2, 'Bob', 1, 80000),
(3, 'Charlie', 2, 65000),
(4, 'Diana', 3, 70000);

INSERT INTO projects VALUES
(101, 'Website Redesign'),
(102, 'Mobile App'),
(103, 'Data Migration');

INSERT INTO emp_projects VALUES
(1, 101, 'Developer'),
(1, 102, 'Lead Developer'),
(2, 102, 'Developer'),
(4, 103, 'Analyst');

-- Query 1: Show employees with their departments
SELECT 
    e.name,
    d.dept_name,
    e.salary
FROM employees e
INNER JOIN departments d ON e.dept_id = d.dept_id;

-- Query 2: Show all departments and count of employees
SELECT 
    d.dept_name,
    COUNT(e.emp_id) AS employee_count
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id
GROUP BY d.dept_name;

-- Result shows Marketing with 0 employees

-- Query 3: Show employees with their projects
SELECT 
    e.name AS employee,
    p.project_name,
    ep.role
FROM employees e
INNER JOIN emp_projects ep ON e.emp_id = ep.emp_id
INNER JOIN projects p ON ep.project_id = p.project_id;

-- Query 4: Find employees not assigned to any project
SELECT e.name
FROM employees e
LEFT JOIN emp_projects ep ON e.emp_id = ep.emp_id
WHERE ep.project_id IS NULL;

-- Result: Charlie (not on any project)
```

## Using Table Aliases

Make queries shorter and more readable:

```sql
-- Without aliases (verbose)
SELECT 
    customers.name,
    orders.product
FROM customers
INNER JOIN orders ON customers.customer_id = orders.customer_id;

-- With aliases (cleaner)
SELECT 
    c.name,
    o.product
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;
```

## Multiple Join Conditions

```sql
-- Join on multiple columns
SELECT *
FROM table1 t1
INNER JOIN table2 t2 
    ON t1.id = t2.id 
    AND t1.year = t2.year;

-- Join with additional WHERE conditions
SELECT 
    c.name,
    o.product
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.amount > 100;
```

## Key Takeaways

1. **INNER JOIN**: Only matching rows from both tables
2. **LEFT JOIN**: All from left table + matches from right
3. **RIGHT JOIN**: All from right table + matches from left
4. **FULL OUTER JOIN**: All rows from both tables
5. **CROSS JOIN**: Every combination (Cartesian product)
6. **SELF JOIN**: Join table with itself
7. **Use aliases** to make queries readable
8. **Chain multiple joins** to connect multiple tables
9. **LEFT JOIN + IS NULL** to find unmatched records

## Common Interview Questions

**Q1: Difference between INNER JOIN and LEFT JOIN?**
- INNER JOIN: Only matching records
- LEFT JOIN: All from left + matching from right (NULLs for non-matches)

**Q2: How to find customers who never placed an order?**
```sql
SELECT c.name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

**Q3: What is a SELF JOIN?**
- Joining a table with itself, useful for hierarchical data (employees-managers)

## Practice Exercises

1. Find all students not enrolled in any course
2. List all courses with student count (including courses with 0 students)
3. Show products that were ordered more than once
4. Find employees working on multiple projects
5. List customers who ordered both Laptop and Mouse

