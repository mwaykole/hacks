# SQL 1: Introduction to DBMS & Keys

## What is a Database?
A **database** is an organized collection of data stored electronically. Think of it as a digital filing cabinet where you can store, retrieve, and manage information.

### Example:
- A library stores information about books, members, and borrowed books
- An e-commerce site stores products, customers, and orders

## What is a DBMS?
**DBMS (Database Management System)** is software that helps you create, manage, and use databases.

### Popular DBMS:
- MySQL
- PostgreSQL
- Oracle
- SQL Server
- MongoDB (NoSQL)

### Why Use a DBMS?
- **Data Security**: Control who can access what
- **Data Integrity**: Keep data accurate and consistent
- **Concurrent Access**: Multiple users can work simultaneously
- **Backup & Recovery**: Protect against data loss

## SQL (Structured Query Language)
SQL is the language we use to communicate with databases.

### Basic SQL Commands:
```sql
-- Create a database
CREATE DATABASE school;

-- Use the database
USE school;

-- Show all databases
SHOW DATABASES;
```

## Tables
A **table** is where data is actually stored. It has rows and columns.

### Example: Students Table
| student_id | name    | age | grade |
|------------|---------|-----|-------|
| 1          | Alice   | 18  | A     |
| 2          | Bob     | 19  | B     |
| 3          | Charlie | 18  | A     |

### Creating a Table:
```sql
CREATE TABLE students (
    student_id INT,
    name VARCHAR(50),
    age INT,
    grade CHAR(1)
);
```

## Data Types
Common data types in SQL:

### Numeric Types:
- `INT` - Whole numbers (e.g., 1, 100, -50)
- `DECIMAL(10,2)` - Decimal numbers (e.g., 99.99)
- `FLOAT` - Floating-point numbers

### String Types:
- `VARCHAR(50)` - Variable-length text (up to 50 characters)
- `CHAR(10)` - Fixed-length text (exactly 10 characters)
- `TEXT` - Long text

### Date/Time Types:
- `DATE` - Date only (2024-01-15)
- `TIME` - Time only (14:30:00)
- `DATETIME` - Date and time (2024-01-15 14:30:00)

### Example:
```sql
CREATE TABLE employees (
    emp_id INT,
    name VARCHAR(100),
    salary DECIMAL(10,2),
    hire_date DATE,
    is_active BOOLEAN
);
```

## Keys in Database

### 1. Primary Key
A **Primary Key** uniquely identifies each row in a table. It cannot be NULL or duplicate.

#### Example:
```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100)
);
```

**Real-world analogy**: Like your Aadhaar number - unique to you!

### 2. Foreign Key
A **Foreign Key** links two tables together. It refers to the Primary Key of another table.

#### Example:
```sql
-- Parent table
CREATE TABLE courses (
    course_id INT PRIMARY KEY,
    course_name VARCHAR(100)
);

-- Child table
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY,
    student_id INT,
    course_id INT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
```

**Real-world analogy**: Your school ID card has your class number, which links you to your class.

### 3. Unique Key
Ensures all values in a column are different (but can have one NULL).

#### Example:
```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15) UNIQUE
);
```

### 4. Composite Key
A combination of two or more columns that uniquely identifies a row.

#### Example:
```sql
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);
```

### 5. Candidate Key
Any column that could be a primary key.

#### Example:
In a students table:
- `student_id` - Candidate Key
- `email` - Candidate Key
- `roll_number` - Candidate Key

You choose one as Primary Key; others become Unique Keys.

### 6. Super Key
A set of one or more columns that can uniquely identify a row.

#### Example:
In students table, all these are Super Keys:
- `student_id`
- `student_id + name`
- `student_id + name + email`
- `email`

## Constraints
Rules applied to columns to enforce data integrity.

### Common Constraints:
```sql
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) CHECK (price > 0),
    stock INT DEFAULT 0,
    category VARCHAR(50),
    UNIQUE (product_name)
);
```

### Constraint Types:
1. **NOT NULL**: Column must have a value
2. **UNIQUE**: All values must be different
3. **PRIMARY KEY**: Unique + Not Null
4. **FOREIGN KEY**: Links to another table
5. **CHECK**: Custom validation rule
6. **DEFAULT**: Default value if none provided

## Practice Examples

### Example 1: School Database
```sql
-- Create database
CREATE DATABASE school;
USE school;

-- Students table
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    age INT CHECK (age >= 5 AND age <= 100),
    enrollment_date DATE DEFAULT CURRENT_DATE
);

-- Courses table
CREATE TABLE courses (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    course_name VARCHAR(100) NOT NULL,
    credits INT CHECK (credits > 0)
);

-- Enrollments table (linking students and courses)
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    course_id INT,
    enrollment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
```

### Example 2: E-commerce Database
```sql
-- Customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15)
);

-- Products table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) CHECK (price >= 0),
    stock INT DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Order items table
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT CHECK (quantity > 0),
    price DECIMAL(10,2),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

## Key Takeaways
1. **Database**: Organized collection of data
2. **DBMS**: Software to manage databases
3. **SQL**: Language to interact with databases
4. **Primary Key**: Unique identifier for each row
5. **Foreign Key**: Links tables together
6. **Constraints**: Rules to maintain data quality
7. **Data Types**: Define what kind of data a column can store

## Common Interview Questions

**Q1: What's the difference between Primary Key and Unique Key?**
- Primary Key: Cannot be NULL, only one per table
- Unique Key: Can have one NULL, multiple unique keys per table

**Q2: What's the difference between CHAR and VARCHAR?**
- CHAR: Fixed length (wastes space if shorter)
- VARCHAR: Variable length (saves space)

**Q3: Why use Foreign Keys?**
- Maintains referential integrity
- Prevents orphaned records
- Enforces relationships between tables

