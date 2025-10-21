create database BankingCapstoneProject;
use BankingCapstoneProject;

CREATE TABLE Customer (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Phone VARCHAR(15),
    City VARCHAR(50)
);


CREATE TABLE Account (
    AccountID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    AccountType VARCHAR(50) NOT NULL,
    Balance DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE TransactionTable (
    TransactionID INT AUTO_INCREMENT PRIMARY KEY,
    AccountID INT NOT NULL,
    TransactionType VARCHAR(30),
    Amount DECIMAL(15,2) NOT NULL,
    TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ---------------Stored Procedures---------------------



-- ---------Show all the customer and their balance
delimiter //
CREATE PROCEDURE ShowAllCustomersBalances()
BEGIN
    SELECT c.Name AS CustomerName,a.Balance
    FROM Customer c
    JOIN Account a ON c.CustomerID = a.CustomerID;
END //


-- ------------Show all the transactions by Customer Id

delimiter //
CREATE PROCEDURE ShowTransactionsByCustomer(IN cust_id INT)
BEGIN
    SELECT 
        a.AccountID,
        c.Name AS CustomerName,
        t.TransactionType,
        t.Amount
    FROM TransactionTable t
    JOIN Account a ON t.AccountID = a.AccountID
    JOIN Customer c ON a.CustomerID = c.CustomerID
    WHERE c.CustomerID = cust_id;
END //

-- ----------------Create Customer
DELIMITER //
CREATE PROCEDURE CreateCustomer(
    IN name_in VARCHAR(100),
    IN email_in VARCHAR(100),
    IN phone_in VARCHAR(15),
    IN city_in VARCHAR(50)
)
BEGIN
    INSERT INTO Customer (Name, Email, Phone, City)
    VALUES (name_in, email_in, phone_in, city_in);

    -- Return the auto-generated CustomerID
    SELECT LAST_INSERT_ID() AS CustomerID;
END //
DELIMITER //




-- -----------------Create Account
delimiter //
CREATE PROCEDURE CreateAccount(
	IN cust_id INT,
	IN account_type varchar(10),
    IN balance DECIMAL(15,2)
)
BEGIN 
	Insert into Account ( CustomerID, AccountType, Balance)
    values (cust_id, account_type, balance);
END //


-- --------------------Delete Customer by Email ID
DELIMITER //
CREATE PROCEDURE DeleteCustomerByEmail(IN email_in VARCHAR(100))
BEGIN
    DELETE FROM Customer WHERE Email = email_in;
END //


DELIMITER //
-- ---------------------Deposit Into Account
DELIMITER //
CREATE PROCEDURE DepositAmount(IN acc_id INT, IN amount_in DECIMAL(15,2))
BEGIN
    DECLARE acc_exists INT;
    SELECT COUNT(*) INTO acc_exists FROM Account WHERE AccountID = acc_id;

    IF acc_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid Account ID';
    ELSE
        UPDATE Account SET Balance = Balance + amount_in WHERE AccountID = acc_id;
        INSERT INTO TransactionTable (AccountID, TransactionType, Amount)
        VALUES (acc_id, 'Deposit', amount_in);

        SELECT a.AccountID, c.Name, a.AccountType, a.Balance
        FROM Account a
        JOIN Customer c ON a.CustomerID = c.CustomerID
        WHERE a.AccountID = acc_id;
    END IF;
END //


-- --------------------------Withdraw from account
DELIMITER //
CREATE PROCEDURE WithdrawAmount(IN acc_id INT, IN amount_in DECIMAL(15,2))
BEGIN
    DECLARE acc_exists INT;
    DECLARE curr_balance DECIMAL(15,2);

    -- Check if account exists
    SELECT COUNT(*) INTO acc_exists 
    FROM Account 
    WHERE AccountID = acc_id;

    IF acc_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid Account ID';
    ELSE
        -- Get current balance
        SELECT Balance INTO curr_balance 
        FROM Account 
        WHERE AccountID = acc_id;

        IF curr_balance < amount_in THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient Balance';
        ELSE
            UPDATE Account 
            SET Balance = Balance - amount_in 
            WHERE AccountID = acc_id;

            INSERT INTO TransactionTable (AccountID, TransactionType, Amount)
            VALUES (acc_id, 'Withdrawal', amount_in);

            SELECT a.AccountID, c.Name, a.AccountType, a.Balance
            FROM Account a
            JOIN Customer c ON a.CustomerID = c.CustomerID
            WHERE a.AccountID = acc_id;
        END IF;
    END IF;
END //
DELIMITER //


-- ---------------------TRANSFER MONEY-----------------
DELIMITER //
CREATE PROCEDURE TransferAmount(
    IN sender_id INT,
    IN receiver_id INT,
    IN amount_in DECIMAL(15,2)
)
BEGIN
    DECLARE sender_exists, receiver_exists INT;
    DECLARE sender_balance DECIMAL(15,2);

    -- Check if sender exists
    SELECT COUNT(*) INTO sender_exists 
    FROM Account 
    WHERE AccountID = sender_id;

    -- Check if receiver exists
    SELECT COUNT(*) INTO receiver_exists 
    FROM Account 
    WHERE AccountID = receiver_id;

    -- Get sender balance
    SELECT Balance INTO sender_balance 
    FROM Account 
    WHERE AccountID = sender_id;

    IF sender_exists = 0 OR receiver_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid Account ID(s)';
    ELSEIF sender_balance < amount_in THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient Balance';
    ELSE
        START TRANSACTION;
            UPDATE Account SET Balance = Balance - amount_in WHERE AccountID = sender_id;
            UPDATE Account SET Balance = Balance + amount_in WHERE AccountID = receiver_id;

            INSERT INTO TransactionTable (AccountID, TransactionType, Amount)
            VALUES (sender_id, 'Transfer Sent', amount_in),
                   (receiver_id, 'Transfer Received', amount_in);
        COMMIT;

        -- Return updated balances for both accounts
        SELECT 
            a.AccountID, c.Name, a.AccountType, a.Balance
        FROM Account a
        JOIN Customer c ON a.CustomerID = c.CustomerID
        WHERE a.AccountID IN (sender_id, receiver_id);
    END IF;
END //
DELIMITER ;


-- ----------------------Views--------------------------------

-- --------------------Top 5 Balance Holders
CREATE OR REPLACE VIEW HighBalanceCustomers AS
SELECT 
    c.Name AS CustomerName,
    a.AccountType,
    a.Balance
FROM Account a
JOIN Customer c ON c.CustomerID = a.CustomerID
ORDER BY a.Balance DESC
LIMIT 5;


select * from customer;
-- -------------------Recent Transactions
CREATE OR REPLACE VIEW RecentTransactions AS
SELECT 
    t.TransactionID,
    c.Name AS CustomerName,
    a.AccountType,
    t.TransactionType,
    t.Amount,
    t.TransactionDate
FROM TransactionTable t
JOIN Account a ON t.AccountID = a.AccountID
JOIN Customer c ON a.CustomerID = c.CustomerID
ORDER BY t.TransactionDate DESC
LIMIT 3;


