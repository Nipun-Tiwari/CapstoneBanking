import mysql.connector
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv


# load .env from project root
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# safely read env variables (with fallbacks)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'BankingCapstoneProject')
DB_PORT = int(os.getenv('DB_PORT', 3306))


# Step 1: Connect to MySQL Database
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT
)


cursor = conn.cursor()
print("<--------------Connected to MySQL database successfully!-------------->")








print("--------------Account table updated!--------------\n")


#---------------------FUNCTIONS-------------------------
def fill_db_with_csv():
        # Step 2: Read data from CSV file
    df = pd.read_csv("bank_customers.csv")
    print("<--------------CSV file loaded successfully!-------------->\n")



    # Step 3: Insert data into Customer table
    print("<--------------Inserting data into Customer table...-------------->")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Customer (CustomerID, Name, Email, Phone, City)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            Name=VALUES(Name), Email=VALUES(Email), Phone=VALUES(Phone), City=VALUES(City)
        """, (int(row['CustomerID']), row['Name'], row['Email'], row['Phone'], row['City']))
    conn.commit()




    print("<-------------- Customer table updated!-------------->\n")

    # Step 4: Insert data into Account table
    print("--------------Inserting data into Account table...--------------")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Account (AccountID, CustomerID, AccountType, Balance)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            AccountType=VALUES(AccountType), Balance=VALUES(Balance)
        """, (int(row['AccountID']), int(row['CustomerID']), row['AccountType'], float(row['Balance'])))
    conn.commit()


def show_all_customers_balances():
    cursor.callproc('ShowAllCustomersBalances')
    result = {}
    for res in cursor.stored_results():
        rows = res.fetchall()
        for row in rows:
            result[row[0]] = row[1]  # CustomerName: Balance
    return result

# 2. Show all transactions by customer id (list of tuples)
def show_transactions_by_customer(cust_id):
    cursor.callproc('ShowTransactionsByCustomer', [cust_id])
    transactions = []
    for res in cursor.stored_results():
        transactions.extend(res.fetchall())  # (AccountID, CustomerName, TransactionType, Amount)
    return transactions

# 3. Create customer
def create_customer(name, email, phone, city):
    cursor.callproc('CreateCustomer', [name, email, phone, city])
    for result in cursor.stored_results():
        customer_id = result.fetchone()[0]
    conn.commit()
    return f"Customer {name} created successfully with CustomerID: {customer_id}"

# 4. Create account
def create_account(cust_id, account_type, balance):
    cursor.callproc('CreateAccount', [cust_id, account_type, balance])
    conn.commit()
    return f"Account for CustomerID {cust_id} created successfully."

# 5. Delete customer by email
def delete_customer_by_email(email):
    cursor.callproc('DeleteCustomerByEmail', [email])
    conn.commit()
    return f"Customer with email {email} deleted successfully."

# 6. Deposit into account (tuple)
def deposit_amount(acc_id, amount):
    try:
        cursor.callproc('DepositAmount', [acc_id, amount])
        conn.commit()
        for res in cursor.stored_results():
            return res.fetchall()[0]  # (AccountID, Name, AccountType, Balance)
    except mysql.connector.Error as e:
        conn.rollback()
        return f"Error: {e.msg}"

# 7. Withdraw from account (tuple)
def withdraw_amount(acc_id, amount):
    try:
        cursor.callproc('WithdrawAmount', [acc_id, amount])
        conn.commit()
        for res in cursor.stored_results():
            return res.fetchall()[0]  # (AccountID, Name, AccountType, Balance)
    except mysql.connector.Error as e:
        return f"Error: {e.msg}"

# 8. Transfer money (list of tuples)
def transfer_amount(sender_id, receiver_id, amount):
    try:
        cursor.callproc('TransferAmount', [sender_id, receiver_id, amount])
        transfers = []
        for res in cursor.stored_results():
            transfers.extend(res.fetchall())  # [(AccountID, Name, AccountType, Balance), ...]
        return transfers
    except mysql.connector.Error as e:
        return f"Error: {e.msg}"

# 9. Function to show top 5 customers with highest balances
def show_high_balance_customers():
    cursor.execute("SELECT * FROM HighBalanceCustomers")
    results = cursor.fetchall()
    if results:
        print("\nTop 5 Customers by Balance:")
        for row in results:
            print(f"Name: {row[0]}, Account Type: {row[1]}, Balance: ₹{row[2]:.2f}")
    else:
        print("\nNo customers found.")

# 10. Function to show 3 most recent transactions
def show_recent_transactions():
    cursor.execute("SELECT * FROM RecentTransactions")
    results = cursor.fetchall()
    if results:
        print("\nRecent Transactions:")
        for row in results:
            print(f"TransactionID: {row[0]}, Name: {row[1]}, Account Type: {row[2]}, "
                  f"Type: {row[3]}, Amount: ₹{row[4]:.2f}, Date: {row[5]}")
    else:
        print("\nNo transactions found.")



print("\n\n------------------------------------------------------------\n")
print("---------------Welcome to the Capstone Bank---------------\n")
print("-------------------------------------------------------------\n\n")
superChoice=int(input("1. Fill database with CSV data\n2. Proceed to Pre-Filled Application\n\n\n"))
if superChoice==1:
    fill_db_with_csv()
elif superChoice!=2:
    print("\nInvalid choice. Exiting application.")
    exit()
else:
    while True:
        choice = int(input("1. Enter as Admin\n2. Enter as Customer\n3. Exit the Application: \n"))

        if choice == 1:
            innerChoice = int(input(
                "\n1. Show all customers' balances\n"
                "2. Show all transactions by customer ID\n"
                "3. Show Top 5 Highest Balance Holders\n"
                "4. Show 3 Most Recent Transactions\n"
                "5. Create customer\n"
                "6. Create account\n"
                "7. Delete customer by email\n"
            ))

            if innerChoice == 1:
                balances = show_all_customers_balances()
                print("\nCustomer Balances:")
                for name, balance in balances.items():
                    print(f"{name}: ₹{balance:.2f}")

            elif innerChoice == 2:
                cust_id = int(input("Enter Customer ID: "))
                transactions = show_transactions_by_customer(cust_id)
                print(f"\nTransactions for Customer ID {cust_id}:")
                for t in transactions:
                    print(f"AccountID: {t[0]}, Name: {t[1]}, Type: {t[2]}, Amount: ₹{t[3]:.2f}")
                
            elif innerChoice == 3:
                show_high_balance_customers()

            elif innerChoice == 4:
                show_recent_transactions()


            elif innerChoice == 5:
                name = input("Enter name: ")
                email = input("Enter email: ")
                phone = input("Enter phone: ")
                city = input("Enter city: ")
                print(create_customer(name, email, phone, city))

            elif innerChoice == 6:
                cust_id = int(input("Enter Customer ID: "))
                account_type = input("Enter account type (Saving/Checking): ")
                balance = float(input("Enter initial balance: "))
                print(create_account(cust_id, account_type, balance))

            elif innerChoice == 7:
                email = input("Enter email to delete: ")
                print(delete_customer_by_email(email))

            else:
                print("\nInvalid choice")

        elif choice == 2:
            acc_id = int(input("Enter Account ID: "))
            action = int(input(
                "\n1. Deposit\n"
                "2. Withdraw\n"
                "3. Transfer\n"
            ))

            if action == 1:
                amount = float(input("Enter amount to deposit: "))
                result = deposit_amount(acc_id, amount)
                if isinstance(result, tuple):
                    print(f"\nDeposit Successful! New Balance for AccountID {result[0]} ({result[1]} - {result[2]}): ₹{result[3]:.2f}")
                else:
                    print(result)

            elif action == 2:
                amount = float(input("Enter amount to withdraw: "))
                result = withdraw_amount(acc_id, amount)
                if isinstance(result, tuple):
                    print(f"\nWithdrawal Successful! New Balance for AccountID {result[0]} ({result[1]} - {result[2]}): ₹{result[3]:.2f}")
                else:
                    print(result)

            elif action == 3:
                receiver_id = int(input("Enter Receiver's Account ID: "))
                amount = float(input("Enter amount to transfer: "))
                results = transfer_amount(acc_id, receiver_id, amount)
                if isinstance(results, list):
                    print("\nTransfer Successful! Updated Balances:")
                    for res in results:
                        print(f"AccountID {res[0]} ({res[1]} - {res[2]}): ₹{res[3]:.2f}")
                else:
                    print(results)

            else:
                print("\nInvalid action")
        elif choice==3: 
            print("\nExiting application. Goodbye!")
            break
        else:
            print("\nInvalid choice")


# Step 6: Close connection
cursor.close()
conn.close()
print("\nAll operations completed successfully!")
