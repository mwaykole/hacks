# SQL 9: Transactions

## What is a Transaction?
A **transaction** is a group of SQL operations that are treated as a single unit of work. Either ALL operations succeed, or NONE of them do.

Think of it like a bank transfer: Money must leave one account AND enter another account. If either fails, both must be cancelled!

## Real-World Example
**Banking Transaction:**
```
1. Deduct $100 from Account A
2. Add $100 to Account B
```
If step 2 fails, step 1 must be rolled back. You can't just deduct money without adding it elsewhere!

## ACID Properties

Transactions follow **ACID** principles:

### A - Atomicity
**All or Nothing**: Either all operations succeed, or none do.

```sql
-- Both must succeed or both fail
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
COMMIT;
```

### C - Consistency
Database remains in a valid state before and after the transaction.

```sql
-- Total money in system remains same
-- Before: Account1($1000) + Account2($500) = $1500
-- After:  Account1($900)  + Account2($600) = $1500
```

### I - Isolation
Transactions don't interfere with each other. Each runs independently.

```sql
-- Transaction 1 and Transaction 2 can run simultaneously
-- without corrupting each other's data
```

### D - Durability
Once committed, changes are permanent (even if system crashes).

```sql
-- After COMMIT, data is saved permanently
-- Power failure won't lose the transaction
```

## Transaction Commands

### 1. START TRANSACTION / BEGIN
Starts a new transaction.

```sql
START TRANSACTION;
-- or simply
BEGIN;
```

### 2. COMMIT
Saves all changes permanently.

```sql
START TRANSACTION;
-- ... SQL operations ...
COMMIT;  -- All changes are saved
```

### 3. ROLLBACK
Undoes all changes since transaction started.

```sql
START TRANSACTION;
-- ... SQL operations ...
ROLLBACK;  -- All changes are cancelled
```

### 4. SAVEPOINT
Creates a checkpoint within a transaction.

```sql
START TRANSACTION;
-- ... some operations ...
SAVEPOINT checkpoint1;
-- ... more operations ...
ROLLBACK TO checkpoint1;  -- Undo only after checkpoint1
COMMIT;
```

## Basic Transaction Examples

### Example 1: Simple Transaction

```sql
-- Create accounts table
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    account_holder VARCHAR(100),
    balance DECIMAL(10,2)
);

-- Insert data
INSERT INTO accounts VALUES
(1, 'Alice', 1000.00),
(2, 'Bob', 500.00);

-- Transaction: Transfer $100 from Alice to Bob
START TRANSACTION;

-- Deduct from Alice
UPDATE accounts 
SET balance = balance - 100 
WHERE account_id = 1;

-- Add to Bob
UPDATE accounts 
SET balance = balance + 100 
WHERE account_id = 2;

-- Check if everything is correct
SELECT * FROM accounts;

-- If correct, save changes
COMMIT;

-- If something wrong, undo changes
-- ROLLBACK;
```

### Example 2: Transaction with Error Handling

```sql
START TRANSACTION;

-- Check if Alice has enough balance
SELECT balance FROM accounts WHERE account_id = 1;
-- If balance < 100, don't proceed

-- If yes, proceed
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;

-- Check if both updates succeeded
-- If yes:
COMMIT;
-- If no:
-- ROLLBACK;
```

### Example 3: Using SAVEPOINT

```sql
START TRANSACTION;

-- Operation 1
INSERT INTO orders (customer_id, amount) VALUES (1, 500);
SAVEPOINT after_order;

-- Operation 2
UPDATE inventory SET stock = stock - 10 WHERE product_id = 5;

-- Oops, realized inventory update was wrong!
ROLLBACK TO after_order;  -- Undo only inventory update

-- Operation 2 (corrected)
UPDATE inventory SET stock = stock - 5 WHERE product_id = 5;

COMMIT;  -- Save order and corrected inventory update
```

## Practical Examples

### Example 1: E-commerce Order Processing

```sql
-- Create tables
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    order_date TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20)
);

CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2)
);

CREATE TABLE inventory (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    stock INT
);

CREATE TABLE customer_wallet (
    customer_id INT PRIMARY KEY,
    balance DECIMAL(10,2)
);

-- Insert sample data
INSERT INTO inventory VALUES
(1, 'Laptop', 10),
(2, 'Mouse', 50);

INSERT INTO customer_wallet VALUES
(101, 2000.00);

-- Transaction: Process an order
START TRANSACTION;

-- Step 1: Create order
INSERT INTO orders (customer_id, order_date, total_amount, status)
VALUES (101, NOW(), 1250.00, 'processing');

SET @order_id = LAST_INSERT_ID();

-- Step 2: Add order items
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES 
(@order_id, 1, 1, 1200.00),
(@order_id, 2, 2, 25.00);

-- Step 3: Reduce inventory
UPDATE inventory SET stock = stock - 1 WHERE product_id = 1;
UPDATE inventory SET stock = stock - 2 WHERE product_id = 2;

-- Step 4: Deduct from customer wallet
UPDATE customer_wallet 
SET balance = balance - 1250.00 
WHERE customer_id = 101;

-- Step 5: Mark order as complete
UPDATE orders 
SET status = 'completed' 
WHERE order_id = @order_id;

-- If all succeeded, commit
COMMIT;

-- If any step fails, rollback
-- ROLLBACK;
```

### Example 2: Banking System

```sql
-- Create tables
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    account_holder VARCHAR(100),
    balance DECIMAL(10,2),
    account_type VARCHAR(20)
);

CREATE TABLE transactions_log (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    from_account INT,
    to_account INT,
    amount DECIMAL(10,2),
    transaction_date TIMESTAMP,
    status VARCHAR(20)
);

-- Insert sample data
INSERT INTO accounts VALUES
(1001, 'Alice', 5000.00, 'savings'),
(1002, 'Bob', 3000.00, 'checking'),
(1003, 'Charlie', 10000.00, 'savings');

-- Transaction: Transfer money
START TRANSACTION;

-- Declare variables
SET @from_acc = 1001;
SET @to_acc = 1002;
SET @amount = 500.00;

-- Check if sufficient balance
SET @current_balance = (SELECT balance FROM accounts WHERE account_id = @from_acc);

-- If balance sufficient, proceed
IF @current_balance >= @amount THEN
    
    -- Deduct from sender
    UPDATE accounts 
    SET balance = balance - @amount 
    WHERE account_id = @from_acc;
    
    -- Add to receiver
    UPDATE accounts 
    SET balance = balance + @amount 
    WHERE account_id = @to_acc;
    
    -- Log the transaction
    INSERT INTO transactions_log (from_account, to_account, amount, transaction_date, status)
    VALUES (@from_acc, @to_acc, @amount, NOW(), 'success');
    
    -- Commit the transaction
    COMMIT;
    
ELSE
    -- Insufficient balance, rollback
    INSERT INTO transactions_log (from_account, to_account, amount, transaction_date, status)
    VALUES (@from_acc, @to_acc, @amount, NOW(), 'failed');
    
    ROLLBACK;
END IF;
```

### Example 3: Inventory Management

```sql
-- Create tables
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    stock INT,
    reserved INT DEFAULT 0
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    quantity INT,
    status VARCHAR(20)
);

-- Insert sample data
INSERT INTO products VALUES
(1, 'Laptop', 50, 0),
(2, 'Mouse', 200, 0);

-- Transaction: Reserve inventory for order
START TRANSACTION;

SET @product = 1;
SET @quantity = 5;

-- Check if stock available
SET @available = (SELECT stock - reserved FROM products WHERE product_id = @product);

IF @available >= @quantity THEN
    
    -- Reserve the stock
    UPDATE products 
    SET reserved = reserved + @quantity 
    WHERE product_id = @product;
    
    -- Create order
    INSERT INTO orders (product_id, quantity, status)
    VALUES (@product, @quantity, 'reserved');
    
    COMMIT;
    
ELSE
    -- Not enough stock
    ROLLBACK;
END IF;

-- Later: When order ships
START TRANSACTION;

SET @order = 1;
SET @product = (SELECT product_id FROM orders WHERE order_id = @order);
SET @quantity = (SELECT quantity FROM orders WHERE order_id = @order);

-- Reduce reserved and stock
UPDATE products 
SET stock = stock - @quantity,
    reserved = reserved - @quantity
WHERE product_id = @product;

-- Update order status
UPDATE orders 
SET status = 'shipped' 
WHERE order_id = @order;

COMMIT;
```

## Transaction Isolation Levels

Controls how transactions see changes made by other transactions.

### 1. READ UNCOMMITTED (Lowest)
Can read uncommitted changes from other transactions (dirty reads).

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;
-- ... queries ...
COMMIT;
```

### 2. READ COMMITTED
Can only read committed changes (prevents dirty reads).

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

### 3. REPEATABLE READ (Default in MySQL)
Same query returns same results within transaction.

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

### 4. SERIALIZABLE (Highest)
Full isolation, transactions run one after another.

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

## Locking

### Row-Level Locks

```sql
-- Lock rows for update
START TRANSACTION;
SELECT * FROM accounts WHERE account_id = 1 FOR UPDATE;
-- Other transactions can't modify this row until we commit/rollback
UPDATE accounts SET balance = 1000 WHERE account_id = 1;
COMMIT;
```

### Shared Locks (Read Lock)

```sql
-- Multiple transactions can read, none can modify
START TRANSACTION;
SELECT * FROM accounts WHERE account_id = 1 LOCK IN SHARE MODE;
-- ... do something ...
COMMIT;
```

## Auto-commit Mode

By default, MySQL runs in auto-commit mode (each statement is a transaction).

```sql
-- Check auto-commit status
SELECT @@autocommit;  -- 1 = ON, 0 = OFF

-- Disable auto-commit
SET autocommit = 0;

-- Now you must explicitly COMMIT or ROLLBACK
UPDATE accounts SET balance = 1000 WHERE account_id = 1;
COMMIT;  -- Must commit manually

-- Re-enable auto-commit
SET autocommit = 1;
```

## Best Practices

### 1. Keep Transactions Short
```sql
-- BAD: Long transaction
START TRANSACTION;
-- ... lots of operations ...
-- ... user input ...
-- ... more operations ...
COMMIT;

-- GOOD: Short transaction
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
COMMIT;
```

### 2. Handle Errors
```sql
-- Use try-catch in application code
try {
    START TRANSACTION;
    // ... operations ...
    COMMIT;
} catch (error) {
    ROLLBACK;
    // Handle error
}
```

### 3. Use Savepoints for Complex Transactions
```sql
START TRANSACTION;
-- ... operations ...
SAVEPOINT sp1;
-- ... more operations ...
IF error THEN
    ROLLBACK TO sp1;
END IF;
COMMIT;
```

### 4. Avoid Nested Transactions
```sql
-- Don't do this:
START TRANSACTION;
    START TRANSACTION;  -- MySQL doesn't support nested transactions
    COMMIT;
COMMIT;
```

## Common Problems

### Problem 1: Deadlock
Two transactions waiting for each other.

```sql
-- Transaction 1
START TRANSACTION;
UPDATE accounts SET balance = 1000 WHERE account_id = 1;
-- Waiting for lock on account 2...
UPDATE accounts SET balance = 2000 WHERE account_id = 2;

-- Transaction 2 (running simultaneously)
START TRANSACTION;
UPDATE accounts SET balance = 2000 WHERE account_id = 2;
-- Waiting for lock on account 1...
UPDATE accounts SET balance = 1000 WHERE account_id = 1;

-- DEADLOCK! Both wait forever
-- MySQL detects and kills one transaction
```

**Solution**: Always lock resources in same order.

### Problem 2: Lost Updates
Two transactions update same data, one overwrites the other.

**Solution**: Use locking or optimistic concurrency control.

## Key Takeaways

1. **Transaction**: Group of operations treated as single unit
2. **ACID**: Atomicity, Consistency, Isolation, Durability
3. **Commands**: BEGIN, COMMIT, ROLLBACK, SAVEPOINT
4. **Use transactions** for operations that must succeed together
5. **Keep transactions short** to avoid locking issues
6. **Handle errors** with ROLLBACK
7. **Use isolation levels** based on requirements
8. **Avoid deadlocks** by locking in consistent order

## Interview Questions

**Q1: What is a transaction?**
Group of SQL operations that execute as a single unit (all or nothing).

**Q2: What are ACID properties?**
Atomicity, Consistency, Isolation, Durability

**Q3: Difference between COMMIT and ROLLBACK?**
COMMIT saves changes permanently, ROLLBACK undoes changes.

**Q4: What is a deadlock?**
Two transactions waiting for each other to release locks.

**Q5: What is isolation level?**
Controls how transactions see changes from other transactions.

## Practice Exercises

1. Create transaction for transferring money between accounts
2. Implement order processing with inventory update
3. Handle transaction rollback on insufficient balance
4. Use savepoints for multi-step operations
5. Implement booking system with transaction locks
6. Create audit log within transaction
7. Handle concurrent transactions on same data

