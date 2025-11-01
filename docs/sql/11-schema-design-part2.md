# SQL 12: Schema Design - Part 2

## Advanced Schema Design Concepts

This guide covers advanced topics in database schema design, denormalization, performance optimization, and special design patterns.

## Denormalization

**Denormalization** is intentionally adding redundancy to improve read performance. It's the opposite of normalization!

### When to Denormalize?

✅ **Use denormalization when:**
- Read performance is critical
- Data is read much more than written
- Complex joins slow down queries
- Need to reduce query complexity

❌ **Avoid denormalization when:**
- Data changes frequently
- Data integrity is critical
- Storage space is limited
- Write performance is critical

### Example: Denormalization

```sql
-- Normalized (requires join)
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    customer_email VARCHAR(100)
);

-- Query requires JOIN
SELECT o.order_id, c.customer_name, c.customer_email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id;

-- Denormalized (faster reads, but redundant data)
CREATE TABLE orders_denormalized (
    order_id INT PRIMARY KEY,
    customer_id INT,
    customer_name VARCHAR(100),    -- Redundant!
    customer_email VARCHAR(100),   -- Redundant!
    order_date DATE
);

-- Query without JOIN (faster!)
SELECT order_id, customer_name, customer_email
FROM orders_denormalized;

-- Trade-off: If customer changes name, must update all orders
```

### Calculated/Derived Columns

Store computed values to avoid calculating them repeatedly.

```sql
-- Example: Store total in orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    total_amount DECIMAL(10,2),  -- Denormalized (sum of order_items)
    tax_amount DECIMAL(10,2),
    final_amount DECIMAL(10,2)   -- Denormalized (total + tax)
);

CREATE TABLE order_items (
    item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    subtotal DECIMAL(10,2)  -- Denormalized (quantity * price)
);

-- Trigger to update totals
CREATE TRIGGER update_order_total
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT SUM(subtotal)
        FROM order_items
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
END;
```

## Soft Deletes vs Hard Deletes

### Hard Delete
Permanently remove data from database.

```sql
-- Hard delete - data is gone forever
DELETE FROM users WHERE user_id = 123;
```

### Soft Delete
Mark data as deleted without actually removing it.

```sql
-- Add deleted_at column
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    deleted_at TIMESTAMP NULL,
    INDEX idx_deleted (deleted_at)
);

-- Soft delete - mark as deleted
UPDATE users
SET deleted_at = NOW()
WHERE user_id = 123;

-- Query active users only
SELECT * FROM users
WHERE deleted_at IS NULL;

-- Query deleted users
SELECT * FROM users
WHERE deleted_at IS NOT NULL;

-- Restore deleted user
UPDATE users
SET deleted_at = NULL
WHERE user_id = 123;
```

**Benefits of Soft Delete:**
- Can restore accidentally deleted data
- Maintain audit trail
- Preserve foreign key relationships
- Better for compliance/legal requirements

## Audit Tables

Track all changes to important data.

```sql
-- Main table
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10,2),
    stock INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Audit table
CREATE TABLE products_audit (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    product_name VARCHAR(100),
    price DECIMAL(10,2),
    stock INT,
    action VARCHAR(20),  -- 'INSERT', 'UPDATE', 'DELETE'
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to log changes
CREATE TRIGGER product_audit_trigger
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    INSERT INTO products_audit (
        product_id, product_name, price, stock, 
        action, changed_by
    )
    VALUES (
        OLD.product_id, OLD.product_name, OLD.price, OLD.stock,
        'UPDATE', USER()
    );
END;
```

## Versioning

Keep history of changes by storing multiple versions.

```sql
-- Approach 1: Version number
CREATE TABLE documents (
    document_id INT,
    version INT,
    title VARCHAR(200),
    content TEXT,
    created_at TIMESTAMP,
    created_by INT,
    PRIMARY KEY (document_id, version)
);

-- Insert new version
INSERT INTO documents (document_id, version, title, content, created_by)
SELECT 
    document_id,
    MAX(version) + 1,
    'Updated Title',
    'Updated Content',
    123
FROM documents
WHERE document_id = 1;

-- Approach 2: Separate history table
CREATE TABLE documents_current (
    document_id INT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE documents_history (
    history_id INT PRIMARY KEY AUTO_INCREMENT,
    document_id INT,
    title VARCHAR(200),
    content TEXT,
    version INT,
    created_at TIMESTAMP
);
```

## JSON Columns

Store semi-structured data using JSON.

```sql
-- Store user preferences as JSON
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    preferences JSON
);

-- Insert with JSON
INSERT INTO users (user_id, username, preferences)
VALUES (
    1,
    'alice',
    '{"theme": "dark", "language": "en", "notifications": {"email": true, "sms": false}}'
);

-- Query JSON data
SELECT 
    user_id,
    username,
    preferences->'$.theme' AS theme,
    preferences->'$.notifications.email' AS email_notifications
FROM users;

-- Update JSON field
UPDATE users
SET preferences = JSON_SET(preferences, '$.theme', 'light')
WHERE user_id = 1;
```

**When to use JSON:**
- Flexible schema needs
- Semi-structured data
- User preferences/settings
- API responses
- Metadata

**When NOT to use JSON:**
- Need to query/index frequently
- Need data validation
- Need foreign key relationships
- Performance is critical

## Temporal Tables (History Tracking)

Track data changes over time.

```sql
-- System-versioned table (MySQL 8.0+)
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10,2),
    valid_from TIMESTAMP(6) GENERATED ALWAYS AS ROW START,
    valid_to TIMESTAMP(6) GENERATED ALWAYS AS ROW END,
    PERIOD FOR SYSTEM_TIME (valid_from, valid_to)
) WITH SYSTEM VERSIONING;

-- Query current data
SELECT * FROM products;

-- Query historical data
SELECT * FROM products
FOR SYSTEM_TIME AS OF '2024-01-01 12:00:00';

-- Query all versions
SELECT * FROM products
FOR SYSTEM_TIME ALL;
```

## Partition Tables

Split large tables into smaller, manageable pieces.

```sql
-- Partition by range (e.g., by date)
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    amount DECIMAL(10,2)
)
PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Partition by list
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    country VARCHAR(50)
)
PARTITION BY LIST COLUMNS(country) (
    PARTITION p_usa VALUES IN ('USA'),
    PARTITION p_canada VALUES IN ('Canada'),
    PARTITION p_uk VALUES IN ('UK'),
    PARTITION p_other VALUES IN ('Other')
);

-- Partition by hash (distribute evenly)
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50)
)
PARTITION BY HASH(user_id)
PARTITIONS 4;
```

**Benefits:**
- Improved query performance on large tables
- Easier data management (drop old partitions)
- Better indexing
- Parallel query execution

## Entity-Attribute-Value (EAV) Pattern

Store dynamic attributes (use sparingly!).

```sql
-- Traditional approach (rigid)
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    color VARCHAR(50),
    size VARCHAR(20),
    weight DECIMAL(10,2)
    -- What if we need to add new attributes?
);

-- EAV approach (flexible but complex queries)
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE product_attributes (
    attribute_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    attribute_name VARCHAR(50),
    attribute_value VARCHAR(200),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_product_attr (product_id, attribute_name)
);

-- Insert product with attributes
INSERT INTO products VALUES (1, 'T-Shirt');
INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
VALUES 
(1, 'color', 'red'),
(1, 'size', 'M'),
(1, 'material', 'cotton');

-- Query (more complex)
SELECT 
    p.name,
    MAX(CASE WHEN pa.attribute_name = 'color' THEN pa.attribute_value END) AS color,
    MAX(CASE WHEN pa.attribute_name = 'size' THEN pa.attribute_value END) AS size
FROM products p
LEFT JOIN product_attributes pa ON p.product_id = pa.product_id
GROUP BY p.product_id, p.name;
```

**Use EAV when:**
- Need extreme flexibility
- Attributes vary greatly by product
- Can't predict attributes in advance

**Avoid EAV when:**
- Attributes are mostly consistent
- Need fast queries
- Need data validation

## Polymorphic Associations

One table relates to multiple tables.

```sql
-- Example: Comments on both Posts and Photos

-- Approach 1: Polymorphic (flexible but no foreign key constraints)
CREATE TABLE comments (
    comment_id INT PRIMARY KEY,
    commentable_type VARCHAR(50),  -- 'post' or 'photo'
    commentable_id INT,             -- ID in posts or photos table
    user_id INT,
    content TEXT
);

-- Approach 2: Separate foreign keys (more rigid but safer)
CREATE TABLE comments (
    comment_id INT PRIMARY KEY,
    post_id INT,
    photo_id INT,
    user_id INT,
    content TEXT,
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id),
    CHECK (
        (post_id IS NOT NULL AND photo_id IS NULL) OR
        (post_id IS NULL AND photo_id IS NOT NULL)
    )
);

-- Approach 3: Separate tables (normalized)
CREATE TABLE post_comments (
    comment_id INT PRIMARY KEY,
    post_id INT,
    user_id INT,
    content TEXT,
    FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

CREATE TABLE photo_comments (
    comment_id INT PRIMARY KEY,
    photo_id INT,
    user_id INT,
    content TEXT,
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id)
);
```

## Handling Hierarchical Data

### Approach 1: Adjacency List (Simple)
```sql
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100),
    parent_id INT,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

-- Data:
-- Electronics (1, NULL)
--   ├─ Laptops (2, 1)
--   └─ Phones (3, 1)
--       └─ iPhone (4, 3)

INSERT INTO categories VALUES
(1, 'Electronics', NULL),
(2, 'Laptops', 1),
(3, 'Phones', 1),
(4, 'iPhone', 3);

-- Query: Get all children of Electronics (requires recursive query)
```

### Approach 2: Nested Set Model (Fast reads)
```sql
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100),
    lft INT,
    rgt INT
);

-- Data with left/right values:
-- Electronics (1, 8)
--   ├─ Laptops (2, 3)
--   └─ Phones (4, 7)
--       └─ iPhone (5, 6)

-- Query all descendants (simple!)
SELECT c2.*
FROM categories c1, categories c2
WHERE c2.lft BETWEEN c1.lft AND c1.rgt
AND c1.category_id = 1;
```

### Approach 3: Closure Table (Most flexible)
```sql
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100)
);

CREATE TABLE category_paths (
    ancestor_id INT,
    descendant_id INT,
    depth INT,
    PRIMARY KEY (ancestor_id, descendant_id),
    FOREIGN KEY (ancestor_id) REFERENCES categories(category_id),
    FOREIGN KEY (descendant_id) REFERENCES categories(category_id)
);

-- For hierarchy: Electronics > Phones > iPhone
-- Store all paths:
INSERT INTO category_paths VALUES
(1, 1, 0),  -- Electronics to itself
(1, 3, 1),  -- Electronics to Phones
(1, 4, 2),  -- Electronics to iPhone
(3, 3, 0),  -- Phones to itself
(3, 4, 1),  -- Phones to iPhone
(4, 4, 0);  -- iPhone to itself

-- Query all descendants (easy!)
SELECT c.*
FROM categories c
JOIN category_paths cp ON c.category_id = cp.descendant_id
WHERE cp.ancestor_id = 1;
```

## Design Patterns for Common Scenarios

### 1. Tags/Labels (Many-to-Many)
```sql
CREATE TABLE posts (
    post_id INT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT
);

CREATE TABLE tags (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(50) UNIQUE
);

CREATE TABLE post_tags (
    post_id INT,
    tag_id INT,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);
```

### 2. Ratings/Reviews
```sql
CREATE TABLE product_ratings (
    rating_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    user_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY unique_user_product (user_id, product_id)
);

-- Denormalized average rating in products table
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    avg_rating DECIMAL(3,2),
    rating_count INT DEFAULT 0
);
```

### 3. Activity Feed/Timeline
```sql
CREATE TABLE activities (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    activity_type VARCHAR(50),  -- 'post', 'comment', 'like'
    target_type VARCHAR(50),    -- 'post', 'photo', 'video'
    target_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_created (user_id, created_at)
);
```

### 4. Notifications
```sql
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    notification_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_unread (user_id, is_read, created_at)
);
```

## Performance Optimization Tips

### 1. Use Appropriate Indexes
```sql
-- Index foreign keys
CREATE INDEX idx_order_customer ON orders(customer_id);

-- Composite index for common queries
CREATE INDEX idx_order_status_date ON orders(status, order_date);

-- Covering index
CREATE INDEX idx_covering ON orders(customer_id, order_date, total_amount);
```

### 2. Denormalize for Read-Heavy Tables
```sql
-- Store count in parent table
CREATE TABLE posts (
    post_id INT PRIMARY KEY,
    title VARCHAR(200),
    comment_count INT DEFAULT 0,  -- Denormalized
    like_count INT DEFAULT 0      -- Denormalized
);
```

### 3. Archive Old Data
```sql
-- Current data
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    amount DECIMAL(10,2)
);

-- Archived data (older than 2 years)
CREATE TABLE orders_archive (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    amount DECIMAL(10,2)
);
```

### 4. Use Caching Tables
```sql
-- Cache expensive calculations
CREATE TABLE daily_sales_cache (
    date DATE PRIMARY KEY,
    total_sales DECIMAL(10,2),
    order_count INT,
    calculated_at TIMESTAMP
);
```

## Key Takeaways

1. **Denormalization** trades storage for speed
2. **Soft deletes** preserve data and relationships
3. **Audit tables** track all changes
4. **JSON columns** for flexible schema
5. **Partitioning** improves performance on large tables
6. **Choose right pattern** for hierarchical data
7. **Consider read vs write** patterns
8. **Index strategically** for common queries
9. **Archive old data** to keep tables lean
10. **Document design decisions** for future reference

## Best Practices Summary

1. ✅ Normalize first, denormalize for performance
2. ✅ Use soft deletes for important data
3. ✅ Add audit trails for critical tables
4. ✅ Index foreign keys and query columns
5. ✅ Use appropriate data types
6. ✅ Plan for scalability
7. ✅ Document schema changes
8. ✅ Use version control for schema
9. ✅ Test with realistic data volumes
10. ✅ Monitor query performance

## Practice Exercises

1. Design schema with soft deletes and audit logging
2. Create denormalized views for reporting
3. Implement hierarchical categories using closure table
4. Design activity feed with polymorphic associations
5. Add partitioning to large tables
6. Create caching strategy for expensive queries
7. Design versioning system for documents
8. Implement notification system with read/unread tracking

