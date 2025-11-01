# SQL 3: CRUD Operations - Part 2

## UPDATE Operations

### What is UPDATE?
The UPDATE statement modifies existing data in a table.

### Basic Syntax:
```sql
UPDATE table_name
SET column1 = value1, column2 = value2
WHERE condition;
```

⚠️ **WARNING**: If you forget the WHERE clause, ALL rows will be updated!

### Example 1: Update Single Row
```sql
-- Update Alice's grade
UPDATE students
SET grade = 'A+'
WHERE name = 'Alice';
```

### Example 2: Update Multiple Columns
```sql
-- Update Bob's age and grade
UPDATE students
SET age = 20, grade = 'A'
WHERE name = 'Bob';
```

### Example 3: Update Multiple Rows
```sql
-- Give all students in grade B a promotion to B+
UPDATE students
SET grade = 'B+'
WHERE grade = 'B';
```

### Example 4: Update with Calculations
```sql
-- Give all employees a 10% raise
UPDATE employees
SET salary = salary * 1.10;

-- Give IT employees a 15% raise
UPDATE employees
SET salary = salary * 1.15
WHERE department = 'IT';
```

### Example 5: Update Based on Multiple Conditions
```sql
-- Update employees in IT or HR department, hired after 2023
UPDATE employees
SET salary = salary + 5000
WHERE (department = 'IT' OR department = 'HR')
  AND hire_date > '2023-01-01';
```

## DELETE Operations

### What is DELETE?
The DELETE statement removes rows from a table.

### Basic Syntax:
```sql
DELETE FROM table_name
WHERE condition;
```

⚠️ **WARNING**: If you forget the WHERE clause, ALL rows will be deleted!

### Example 1: Delete Single Row
```sql
-- Remove student named Charlie
DELETE FROM students
WHERE name = 'Charlie';
```

### Example 2: Delete Multiple Rows
```sql
-- Remove all students with grade F
DELETE FROM students
WHERE grade = 'F';
```

### Example 3: Delete with Multiple Conditions
```sql
-- Remove students older than 25 with grade below C
DELETE FROM students
WHERE age > 25 AND grade IN ('D', 'F');
```

### Example 4: Delete All Rows (but keep table structure)
```sql
-- Delete all data (use with caution!)
DELETE FROM students;
```

## TRUNCATE vs DELETE

### DELETE:
- Removes rows one by one
- Can use WHERE clause
- Slower for large tables
- Can be rolled back (if in transaction)

```sql
DELETE FROM students WHERE age > 30;
```

### TRUNCATE:
- Removes all rows at once
- Cannot use WHERE clause
- Much faster for large tables
- Cannot be rolled back easily

```sql
TRUNCATE TABLE students;
```

## DROP vs TRUNCATE vs DELETE

### DELETE:
```sql
DELETE FROM students;  -- Removes all data, keeps table
```

### TRUNCATE:
```sql
TRUNCATE TABLE students;  -- Removes all data, keeps table (faster)
```

### DROP:
```sql
DROP TABLE students;  -- Removes entire table including structure
```

## Practical Examples

### Example 1: Employee Management
```sql
-- Create table
CREATE TABLE employees (
    emp_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    performance_rating VARCHAR(20)
);

-- Insert sample data
INSERT INTO employees (name, department, salary, performance_rating)
VALUES 
    ('John', 'IT', 70000, 'Good'),
    ('Jane', 'HR', 65000, 'Excellent'),
    ('Mike', 'IT', 75000, 'Average'),
    ('Sarah', 'Finance', 80000, 'Excellent'),
    ('Tom', 'IT', 60000, 'Poor');

-- UPDATE examples:

-- 1. Give raise to excellent performers
UPDATE employees
SET salary = salary * 1.20
WHERE performance_rating = 'Excellent';

-- 2. Move Tom to HR department
UPDATE employees
SET department = 'HR'
WHERE name = 'Tom';

-- 3. Update multiple employees in IT
UPDATE employees
SET performance_rating = 'Good'
WHERE department = 'IT' AND performance_rating = 'Average';

-- 4. Give standard raise to all employees
UPDATE employees
SET salary = salary + 5000;

-- DELETE examples:

-- 1. Remove employees with poor performance
DELETE FROM employees
WHERE performance_rating = 'Poor';

-- 2. Remove employees with salary less than 50000
DELETE FROM employees
WHERE salary < 50000;
```

### Example 2: E-commerce System
```sql
-- Create products table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200),
    price DECIMAL(10,2),
    stock INT,
    status VARCHAR(20)
);

-- Insert sample data
INSERT INTO products (product_name, price, stock, status)
VALUES 
    ('Laptop', 1200.00, 5, 'active'),
    ('Mouse', 25.00, 100, 'active'),
    ('Keyboard', 75.00, 50, 'active'),
    ('Monitor', 300.00, 0, 'active'),
    ('Webcam', 80.00, 15, 'discontinued');

-- UPDATE examples:

-- 1. Reduce price by 20% for items with high stock
UPDATE products
SET price = price * 0.80
WHERE stock > 50;

-- 2. Mark out-of-stock items as inactive
UPDATE products
SET status = 'inactive'
WHERE stock = 0;

-- 3. Restock keyboards
UPDATE products
SET stock = stock + 100
WHERE product_name = 'Keyboard';

-- 4. Discontinue old products
UPDATE products
SET status = 'discontinued'
WHERE product_id IN (1, 2, 3);

-- DELETE examples:

-- 1. Remove discontinued products with no stock
DELETE FROM products
WHERE status = 'discontinued' AND stock = 0;

-- 2. Remove products priced below $10
DELETE FROM products
WHERE price < 10;
```

### Example 3: Student Management
```sql
-- Create students table
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    age INT,
    grade CHAR(1),
    attendance_percentage DECIMAL(5,2),
    status VARCHAR(20)
);

-- Insert sample data
INSERT INTO students (name, age, grade, attendance_percentage, status)
VALUES 
    ('Alice', 18, 'A', 95.50, 'active'),
    ('Bob', 19, 'B', 85.00, 'active'),
    ('Charlie', 17, 'C', 70.00, 'active'),
    ('Diana', 18, 'F', 45.00, 'probation'),
    ('Eve', 20, 'B', 88.00, 'active');

-- UPDATE examples:

-- 1. Promote students with A grade
UPDATE students
SET grade = 'A+'
WHERE grade = 'A' AND attendance_percentage > 90;

-- 2. Put students with low attendance on probation
UPDATE students
SET status = 'probation'
WHERE attendance_percentage < 75;

-- 3. Improve Charlie's grade after extra credit
UPDATE students
SET grade = 'B', attendance_percentage = 80.00
WHERE name = 'Charlie';

-- 4. Age all students by 1 year at year end
UPDATE students
SET age = age + 1;

-- DELETE examples:

-- 1. Remove students who failed and have low attendance
DELETE FROM students
WHERE grade = 'F' AND attendance_percentage < 50;

-- 2. Remove inactive students
DELETE FROM students
WHERE status = 'inactive';
```

## UPDATE with CASE Statement

You can use CASE for conditional updates:

```sql
-- Give different raises based on department
UPDATE employees
SET salary = CASE
    WHEN department = 'IT' THEN salary * 1.15
    WHEN department = 'HR' THEN salary * 1.10
    WHEN department = 'Finance' THEN salary * 1.12
    ELSE salary * 1.05
END;

-- Update grades based on attendance
UPDATE students
SET grade = CASE
    WHEN attendance_percentage >= 90 THEN 'A'
    WHEN attendance_percentage >= 80 THEN 'B'
    WHEN attendance_percentage >= 70 THEN 'C'
    WHEN attendance_percentage >= 60 THEN 'D'
    ELSE 'F'
END;
```

## Safe UPDATE/DELETE Practices

### 1. Always Use WHERE Clause
```sql
-- DANGEROUS - Updates all rows
UPDATE employees SET salary = 50000;

-- SAFE - Updates specific rows
UPDATE employees SET salary = 50000 WHERE emp_id = 5;
```

### 2. Test with SELECT First
```sql
-- First, check what will be updated
SELECT * FROM employees WHERE department = 'IT';

-- Then update
UPDATE employees SET salary = salary * 1.10 WHERE department = 'IT';
```

### 3. Use Transactions for Safety
```sql
-- Start transaction
START TRANSACTION;

-- Make changes
UPDATE employees SET salary = 50000 WHERE emp_id = 5;

-- Check if correct
SELECT * FROM employees WHERE emp_id = 5;

-- If correct, save changes
COMMIT;

-- If wrong, undo changes
-- ROLLBACK;
```

### 4. Backup Before Major Changes
```sql
-- Create backup
CREATE TABLE employees_backup AS SELECT * FROM employees;

-- Make changes
DELETE FROM employees WHERE performance_rating = 'Poor';

-- If something goes wrong, restore from backup
-- INSERT INTO employees SELECT * FROM employees_backup;
```

## Common Mistakes to Avoid

### Mistake 1: Forgetting WHERE Clause
```sql
-- WRONG - Updates all students!
UPDATE students SET grade = 'A';

-- CORRECT
UPDATE students SET grade = 'A' WHERE student_id = 5;
```

### Mistake 2: Using = for NULL
```sql
-- WRONG - Doesn't work with NULL
SELECT * FROM students WHERE grade = NULL;
UPDATE students SET status = 'active' WHERE grade = NULL;

-- CORRECT
SELECT * FROM students WHERE grade IS NULL;
UPDATE students SET status = 'active' WHERE grade IS NULL;
```

### Mistake 3: String Comparison Case Sensitivity
```sql
-- May not match if database is case-sensitive
UPDATE students SET grade = 'A' WHERE name = 'alice';

-- Better - use correct case or use function
UPDATE students SET grade = 'A' WHERE LOWER(name) = 'alice';
```

## Key Takeaways

1. **UPDATE**: Modify existing data
   - Always use WHERE clause to specify which rows to update
   - Can update multiple columns at once
   - Can use calculations and CASE statements

2. **DELETE**: Remove data
   - Always use WHERE clause to specify which rows to delete
   - Cannot be easily undone
   - Use TRUNCATE for faster deletion of all rows

3. **Safety First**:
   - Test with SELECT before UPDATE/DELETE
   - Use transactions for critical operations
   - Create backups before major changes
   - Double-check WHERE conditions

4. **Differences**:
   - DELETE: Removes rows, keeps table
   - TRUNCATE: Removes all rows quickly, keeps table
   - DROP: Removes entire table

## Practice Exercises

Try these exercises:

1. Update all products priced below $50 to increase by 10%
2. Delete all orders older than 1 year
3. Update employees in 'Sales' department to give 5% raise
4. Mark all products with stock = 0 as 'out_of_stock'
5. Delete all students with grade F and attendance < 50%
6. Update book prices based on publication year (older = cheaper)
7. Give all employees hired before 2020 a $10,000 bonus
8. Remove all inactive users who haven't logged in for 2 years

