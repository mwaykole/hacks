# SQL 2: CRUD Operations - Part 1

## What is CRUD?
**CRUD** stands for:
- **C**reate - Adding new data
- **R**ead - Retrieving data
- **U**pdate - Modifying existing data
- **D**elete - Removing data

These are the four basic operations you'll do with any database.

## CREATE Operations

### 1. INSERT - Adding Data

#### Basic Syntax:
```sql
INSERT INTO table_name (column1, column2, column3)
VALUES (value1, value2, value3);
```

#### Example 1: Insert Single Row
```sql
-- Create table first
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    age INT,
    grade CHAR(1)
);

-- Insert one student
INSERT INTO students (name, age, grade)
VALUES ('Alice', 18, 'A');
```

#### Example 2: Insert Multiple Rows
```sql
INSERT INTO students (name, age, grade)
VALUES 
    ('Bob', 19, 'B'),
    ('Charlie', 18, 'A'),
    ('Diana', 20, 'C');
```

#### Example 3: Insert Without Specifying Columns
```sql
-- Must provide values for ALL columns in order
INSERT INTO students
VALUES (5, 'Eve', 19, 'B');
```

### 2. INSERT with SELECT
Copy data from one table to another:

```sql
-- Create a backup table
CREATE TABLE students_backup LIKE students;

-- Copy all data
INSERT INTO students_backup
SELECT * FROM students;
```

## READ Operations (SELECT)

### 1. Basic SELECT
```sql
-- Select all columns
SELECT * FROM students;

-- Select specific columns
SELECT name, age FROM students;
```

### 2. WHERE Clause - Filtering Data
```sql
-- Single condition
SELECT * FROM students
WHERE age > 18;

-- Multiple conditions with AND
SELECT * FROM students
WHERE age > 18 AND grade = 'A';

-- Multiple conditions with OR
SELECT * FROM students
WHERE grade = 'A' OR grade = 'B';
```

### 3. Comparison Operators
```sql
-- Equal to
SELECT * FROM students WHERE age = 18;

-- Not equal to
SELECT * FROM students WHERE grade != 'F';
SELECT * FROM students WHERE grade <> 'F';  -- Same as !=

-- Greater than / Less than
SELECT * FROM students WHERE age > 18;
SELECT * FROM students WHERE age < 20;

-- Greater than or equal / Less than or equal
SELECT * FROM students WHERE age >= 18;
SELECT * FROM students WHERE age <= 20;
```

### 4. BETWEEN Operator
```sql
-- Age between 18 and 20 (inclusive)
SELECT * FROM students
WHERE age BETWEEN 18 AND 20;

-- Same as:
SELECT * FROM students
WHERE age >= 18 AND age <= 20;
```

### 5. IN Operator
```sql
-- Students with grade A, B, or C
SELECT * FROM students
WHERE grade IN ('A', 'B', 'C');

-- Same as:
SELECT * FROM students
WHERE grade = 'A' OR grade = 'B' OR grade = 'C';
```

### 6. LIKE Operator - Pattern Matching
```sql
-- Names starting with 'A'
SELECT * FROM students
WHERE name LIKE 'A%';

-- Names ending with 'e'
SELECT * FROM students
WHERE name LIKE '%e';

-- Names containing 'li'
SELECT * FROM students
WHERE name LIKE '%li%';

-- Names with exactly 5 characters
SELECT * FROM students
WHERE name LIKE '_____';

-- Names with 'a' as second character
SELECT * FROM students
WHERE name LIKE '_a%';
```

**Wildcards:**
- `%` - Matches any number of characters (0 or more)
- `_` - Matches exactly one character

### 7. NULL Values
```sql
-- Find students without a grade
SELECT * FROM students
WHERE grade IS NULL;

-- Find students with a grade
SELECT * FROM students
WHERE grade IS NOT NULL;
```

### 8. DISTINCT - Remove Duplicates
```sql
-- Get unique grades
SELECT DISTINCT grade FROM students;

-- Get unique combinations
SELECT DISTINCT age, grade FROM students;
```

### 9. ORDER BY - Sorting
```sql
-- Sort by age (ascending - default)
SELECT * FROM students
ORDER BY age;

-- Sort by age (descending)
SELECT * FROM students
ORDER BY age DESC;

-- Sort by multiple columns
SELECT * FROM students
ORDER BY grade ASC, age DESC;
```

### 10. LIMIT - Restrict Number of Results
```sql
-- Get first 5 students
SELECT * FROM students
LIMIT 5;

-- Get 5 students starting from the 10th (skip 10, take 5)
SELECT * FROM students
LIMIT 10, 5;

-- Same as:
SELECT * FROM students
LIMIT 5 OFFSET 10;
```

## Practical Examples

### Example 1: Employee Database
```sql
-- Create table
CREATE TABLE employees (
    emp_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE
);

-- Insert data
INSERT INTO employees (name, department, salary, hire_date)
VALUES 
    ('John Doe', 'IT', 75000.00, '2023-01-15'),
    ('Jane Smith', 'HR', 65000.00, '2023-02-20'),
    ('Mike Johnson', 'IT', 80000.00, '2023-03-10'),
    ('Sarah Williams', 'Finance', 70000.00, '2023-04-05'),
    ('Tom Brown', 'IT', 72000.00, '2023-05-12');

-- Query examples:

-- 1. Find all IT employees
SELECT * FROM employees
WHERE department = 'IT';

-- 2. Find employees earning more than 70000
SELECT * FROM employees
WHERE salary > 70000;

-- 3. Find IT employees earning more than 70000
SELECT * FROM employees
WHERE department = 'IT' AND salary > 70000;

-- 4. Find employees hired in 2023
SELECT * FROM employees
WHERE hire_date BETWEEN '2023-01-01' AND '2023-12-31';

-- 5. Find employees in IT or HR
SELECT * FROM employees
WHERE department IN ('IT', 'HR');

-- 6. Find employees whose name starts with 'J'
SELECT * FROM employees
WHERE name LIKE 'J%';

-- 7. Get top 3 highest paid employees
SELECT * FROM employees
ORDER BY salary DESC
LIMIT 3;

-- 8. Get unique departments
SELECT DISTINCT department FROM employees;
```

### Example 2: Products Database
```sql
-- Create table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT
);

-- Insert data
INSERT INTO products (product_name, category, price, stock)
VALUES 
    ('iPhone 15', 'Electronics', 999.99, 50),
    ('Samsung TV', 'Electronics', 799.99, 30),
    ('Nike Shoes', 'Fashion', 129.99, 100),
    ('Adidas Jacket', 'Fashion', 89.99, 75),
    ('Dell Laptop', 'Electronics', 1299.99, 25),
    ('Coffee Maker', 'Home', 49.99, 200);

-- Query examples:

-- 1. Find products under $100
SELECT * FROM products
WHERE price < 100;

-- 2. Find Electronics products
SELECT * FROM products
WHERE category = 'Electronics';

-- 3. Find products out of stock or low stock (less than 30)
SELECT * FROM products
WHERE stock < 30;

-- 4. Find products between $50 and $500
SELECT * FROM products
WHERE price BETWEEN 50 AND 500;

-- 5. Search for products with "Laptop" or "Phone" in name
SELECT * FROM products
WHERE product_name LIKE '%Laptop%' OR product_name LIKE '%Phone%';

-- 6. Get most expensive products first
SELECT * FROM products
ORDER BY price DESC;

-- 7. Get cheapest Fashion products
SELECT * FROM products
WHERE category = 'Fashion'
ORDER BY price ASC
LIMIT 3;
```

### Example 3: Library System
```sql
-- Create table
CREATE TABLE books (
    book_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200),
    author VARCHAR(100),
    genre VARCHAR(50),
    year INT,
    available BOOLEAN
);

-- Insert data
INSERT INTO books (title, author, genre, year, available)
VALUES 
    ('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 1925, TRUE),
    ('To Kill a Mockingbird', 'Harper Lee', 'Fiction', 1960, TRUE),
    ('1984', 'George Orwell', 'Science Fiction', 1949, FALSE),
    ('Pride and Prejudice', 'Jane Austen', 'Romance', 1813, TRUE),
    ('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 1937, TRUE);

-- Query examples:

-- 1. Find available books
SELECT * FROM books
WHERE available = TRUE;

-- 2. Find Fiction books
SELECT * FROM books
WHERE genre = 'Fiction';

-- 3. Find books published after 1900
SELECT * FROM books
WHERE year > 1900;

-- 4. Find books by author name containing 'Lee'
SELECT * FROM books
WHERE author LIKE '%Lee%';

-- 5. Find available Fiction or Fantasy books
SELECT * FROM books
WHERE available = TRUE AND (genre = 'Fiction' OR genre = 'Fantasy');

-- 6. Get oldest books first
SELECT * FROM books
ORDER BY year ASC;
```

## Combining Multiple Conditions

### Example: Complex Queries
```sql
-- Find IT employees hired in 2023 earning between 70k and 80k
SELECT * FROM employees
WHERE department = 'IT'
  AND hire_date BETWEEN '2023-01-01' AND '2023-12-31'
  AND salary BETWEEN 70000 AND 80000;

-- Find products that are Electronics or Fashion, priced under $1000, with stock > 20
SELECT * FROM products
WHERE (category = 'Electronics' OR category = 'Fashion')
  AND price < 1000
  AND stock > 20;
```

## Column Aliases
Make column names more readable in results:

```sql
-- Rename columns in output
SELECT 
    name AS 'Employee Name',
    salary AS 'Monthly Salary',
    salary * 12 AS 'Annual Salary'
FROM employees;

-- Can omit AS keyword
SELECT 
    name 'Employee Name',
    department 'Department'
FROM employees;
```

## Key Takeaways
1. **INSERT**: Add new data to tables
2. **SELECT**: Retrieve data from tables
3. **WHERE**: Filter data based on conditions
4. **ORDER BY**: Sort results
5. **LIMIT**: Restrict number of results
6. **LIKE**: Pattern matching with wildcards (% and _)
7. **IN**: Check if value is in a list
8. **BETWEEN**: Check if value is in a range
9. **DISTINCT**: Remove duplicate rows
10. **IS NULL / IS NOT NULL**: Check for NULL values

## Practice Questions

Try to write queries for these scenarios:

1. Find all students aged 18 or 19
2. Find students whose name ends with 'a'
3. Get the 5 youngest students
4. Find students with grades A, B, or C
5. Find all products in Electronics category priced above $500
6. Get the top 10 most expensive products
7. Find employees hired in the last 6 months
8. Find books published between 1800 and 1900

