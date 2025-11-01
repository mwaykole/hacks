# SQL 11: Schema Design - Part 1

## What is Schema Design?
**Schema design** is the process of defining how data will be organized and structured in a database. It's the blueprint of your database!

Think of it as designing the floor plan of a house before building it.

## Why is Schema Design Important?

Good schema design:
✅ Makes queries faster and more efficient
✅ Ensures data integrity and consistency
✅ Prevents data anomalies
✅ Makes maintenance easier
✅ Scales better as data grows

Bad schema design:
❌ Slow queries
❌ Data inconsistencies
❌ Difficult to maintain
❌ Wasted storage space

## Database Normalization

**Normalization** is the process of organizing data to reduce redundancy and improve data integrity.

### Problems with Bad Design (Unnormalized)

```sql
-- Bad design: Everything in one table
CREATE TABLE orders_bad (
    order_id INT,
    customer_name VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(15),
    customer_address TEXT,
    product1_name VARCHAR(100),
    product1_price DECIMAL(10,2),
    product1_quantity INT,
    product2_name VARCHAR(100),
    product2_price DECIMAL(10,2),
    product2_quantity INT,
    order_date DATE
);
```

**Problems:**
1. **Redundancy**: Customer info repeated for each order
2. **Update Anomaly**: If customer changes email, must update all orders
3. **Insert Anomaly**: Can't add customer without an order
4. **Delete Anomaly**: Deleting last order deletes customer info
5. **Limited Products**: What if customer orders 3+ products?
6. **Wasted Space**: Empty product2 columns if only 1 item ordered

## Normal Forms

### 1st Normal Form (1NF)
**Rule**: Each column contains atomic (single) values, no repeating groups.

**Before 1NF (Bad):**
```sql
CREATE TABLE students_bad (
    student_id INT,
    name VARCHAR(100),
    courses VARCHAR(200)  -- "Math, Science, English" - Multiple values!
);
```

**After 1NF (Good):**
```sql
-- Solution 1: Separate table for courses
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY,
    student_id INT,
    course VARCHAR(50)
);

-- Or Solution 2: Multiple rows
INSERT INTO enrollments VALUES
(1, 1, 'Math'),
(2, 1, 'Science'),
(3, 1, 'English');
```

### 2nd Normal Form (2NF)
**Rule**: Must be in 1NF + No partial dependencies (all non-key columns depend on entire primary key).

**Before 2NF (Bad):**
```sql
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    product_name VARCHAR(100),    -- Depends only on product_id
    product_price DECIMAL(10,2),  -- Depends only on product_id
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);
-- product_name and product_price depend on product_id only, not on full key!
```

**After 2NF (Good):**
```sql
-- Separate products table
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    product_price DECIMAL(10,2)
);

CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

### 3rd Normal Form (3NF)
**Rule**: Must be in 2NF + No transitive dependencies (non-key columns depend only on primary key).

**Before 3NF (Bad):**
```sql
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    dept_name VARCHAR(50),      -- Depends on dept_id, not emp_id
    dept_location VARCHAR(100)  -- Depends on dept_id, not emp_id
);
-- dept_name and dept_location depend on dept_id, which depends on emp_id
```

**After 3NF (Good):**
```sql
CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(50),
    dept_location VARCHAR(100)
);

CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);
```

## Practical Schema Design Examples

### Example 1: E-commerce System

```sql
-- Products
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    INDEX idx_category (category_id),
    INDEX idx_price (price)
);

-- Categories
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    parent_category_id INT,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- Customers
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- Customer Addresses
CREATE TABLE addresses (
    address_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    address_type ENUM('shipping', 'billing'),
    street_address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Orders
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled'),
    total_amount DECIMAL(10,2),
    shipping_address_id INT,
    billing_address_id INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (shipping_address_id) REFERENCES addresses(address_id),
    FOREIGN KEY (billing_address_id) REFERENCES addresses(address_id),
    INDEX idx_customer (customer_id),
    INDEX idx_status (status),
    INDEX idx_date (order_date)
);

-- Order Items
CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_purchase DECIMAL(10,2) NOT NULL,  -- Store price at time of purchase
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Reviews
CREATE TABLE product_reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    UNIQUE KEY unique_customer_product (customer_id, product_id)
);
```

### Example 2: Social Media Platform

```sql
-- Users
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    profile_picture_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Posts
CREATE TABLE posts (
    post_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);

-- Comments
CREATE TABLE comments (
    comment_id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    parent_comment_id INT,  -- For nested comments (replies)
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (parent_comment_id) REFERENCES comments(comment_id),
    INDEX idx_post (post_id),
    INDEX idx_user (user_id)
);

-- Likes
CREATE TABLE likes (
    like_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    post_id INT,
    comment_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_post (user_id, post_id),
    UNIQUE KEY unique_user_comment (user_id, comment_id),
    CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    )
);

-- Followers/Following
CREATE TABLE follows (
    follow_id INT PRIMARY KEY AUTO_INCREMENT,
    follower_id INT NOT NULL,  -- User who follows
    following_id INT NOT NULL,  -- User being followed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES users(user_id),
    FOREIGN KEY (following_id) REFERENCES users(user_id),
    UNIQUE KEY unique_follow (follower_id, following_id),
    INDEX idx_follower (follower_id),
    INDEX idx_following (following_id)
);

-- Messages (Direct Messages)
CREATE TABLE messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES users(user_id),
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id)
);
```

### Example 3: School Management System

```sql
-- Students
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    date_of_birth DATE,
    enrollment_date DATE,
    grade_level INT,
    INDEX idx_grade (grade_level)
);

-- Teachers
CREATE TABLE teachers (
    teacher_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    hire_date DATE,
    department VARCHAR(50)
);

-- Courses
CREATE TABLE courses (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    description TEXT,
    credits INT,
    department VARCHAR(50)
);

-- Class Sections
CREATE TABLE sections (
    section_id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT NOT NULL,
    teacher_id INT NOT NULL,
    semester VARCHAR(20),
    year INT,
    room_number VARCHAR(20),
    schedule VARCHAR(100),  -- e.g., "MWF 9:00-10:00"
    max_students INT DEFAULT 30,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    INDEX idx_course (course_id),
    INDEX idx_teacher (teacher_id)
);

-- Enrollments
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    enrollment_date DATE,
    status ENUM('enrolled', 'dropped', 'completed'),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id),
    UNIQUE KEY unique_student_section (student_id, section_id)
);

-- Grades
CREATE TABLE grades (
    grade_id INT PRIMARY KEY AUTO_INCREMENT,
    enrollment_id INT NOT NULL,
    assignment_type VARCHAR(50),  -- 'homework', 'exam', 'project'
    assignment_name VARCHAR(100),
    score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    grade_date DATE,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
    INDEX idx_enrollment (enrollment_id)
);

-- Attendance
CREATE TABLE attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    enrollment_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('present', 'absent', 'late', 'excused'),
    notes TEXT,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
    UNIQUE KEY unique_enrollment_date (enrollment_id, date)
);
```

## Relationships

### One-to-One (1:1)
One record in Table A relates to exactly one record in Table B.

```sql
-- Example: User and Profile
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100)
);

CREATE TABLE user_profiles (
    profile_id INT PRIMARY KEY,
    user_id INT UNIQUE,  -- UNIQUE ensures 1-to-1
    bio TEXT,
    website VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### One-to-Many (1:M)
One record in Table A relates to many records in Table B.

```sql
-- Example: Customer and Orders
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
-- One customer can have many orders
```

### Many-to-Many (M:N)
Many records in Table A relate to many records in Table B.

```sql
-- Example: Students and Courses
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE courses (
    course_id INT PRIMARY KEY,
    course_name VARCHAR(100)
);

-- Junction/Bridge table
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY,
    student_id INT,
    course_id INT,
    enrollment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    UNIQUE KEY (student_id, course_id)
);
-- Many students can take many courses
```

## Naming Conventions

### Table Names:
- **Plural nouns**: `customers`, `orders`, `products`
- **Lowercase**: `users` not `Users`
- **Underscores for multi-word**: `order_items`, `product_reviews`

### Column Names:
- **Descriptive**: `first_name` not `fn`
- **Lowercase with underscores**: `created_at`, `total_amount`
- **Prefix for clarity**: `is_active`, `has_premium`

### Primary Keys:
- **Format**: `table_name_id` (e.g., `customer_id`, `order_id`)
- Or simply: `id`

### Foreign Keys:
- **Same name as referenced PK**: If referencing `users(user_id)`, use `user_id`
- **Clear naming**: `customer_id`, `product_id`

### Indexes:
- **Format**: `idx_column_name` (e.g., `idx_email`, `idx_customer_date`)

## Key Takeaways

1. **Normalization** reduces redundancy and improves integrity
2. **1NF**: Atomic values, no repeating groups
3. **2NF**: No partial dependencies
4. **3NF**: No transitive dependencies
5. **Relationships**: One-to-One, One-to-Many, Many-to-Many
6. **Use foreign keys** to maintain referential integrity
7. **Follow naming conventions** for consistency
8. **Think about scalability** and future needs
9. **Index frequently queried columns**
10. **Store historical data** when needed (e.g., `price_at_purchase`)

## Best Practices

1. **Use appropriate data types** (don't use VARCHAR for numbers!)
2. **Set NOT NULL** for required fields
3. **Use DEFAULT values** where appropriate
4. **Add indexes** on foreign keys and frequently queried columns
5. **Use ENUM** for fixed set of values
6. **Use TIMESTAMP** for tracking changes
7. **Store money** as DECIMAL, not FLOAT
8. **Avoid NULL** in foreign keys if possible
9. **Use junction tables** for many-to-many relationships
10. **Document your schema** with comments

## Common Mistakes to Avoid

1. ❌ Storing calculated values (can be computed)
2. ❌ Using VARCHAR for everything
3. ❌ Not using foreign keys
4. ❌ Over-normalization (too many tables)
5. ❌ Inconsistent naming conventions
6. ❌ No indexes on foreign keys
7. ❌ Not planning for future requirements
8. ❌ Storing comma-separated values in a column

## Practice Exercises

1. Design schema for a library management system
2. Create schema for a hotel booking system
3. Design database for a blog platform
4. Create schema for inventory management
5. Design schema for a ride-sharing app
6. Normalize a poorly designed schema
7. Add appropriate indexes to your schema
8. Design schema for a food delivery app

