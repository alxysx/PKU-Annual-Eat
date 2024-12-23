# PKU Card Transaction Analysis

Tools for fetching and analyzing PKU campus card transactions.

## Prerequisites

1. **Get `account`, `ASP.NETSessionId`, and `hallticket` from `https://card.pku.edu.cn/user/user`**  
   - Open `https://card.pku.edu.cn/user/user` and log in.
   - After logging in, click on "账户管理" (Account Management), where you can find the six-digit `account` number.
   - Open the developer tools in your browser by pressing `F12`.
   - Go to the "Application" (or "存储") tab in the developer tools.
   - In the left sidebar, select `Cookies`, and then choose `https://card.pku.edu.cn`.
   - Here, you will find the two required values:
     - `ASP.NETSessionId`: This is stored as a cookie and typically contains a random session ID.
     - `hallticket`: This is also stored as a cookie and may be required for further requests.

2. Run `python card_query.py <account> --start-date YYYY-MM-DD` to fetch transactions from the specified date.

3. Run `python transaction_analysis.py card_transactions_xxx.json` to analyze the transactions.
