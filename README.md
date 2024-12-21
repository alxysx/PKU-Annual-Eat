# PKU Card Transaction Analysis

Tools for fetching and analyzing PKU campus card transactions.

## Prerequisites

1. Get `account`, `ASP.NETSessionId` and `hallticket` from `https://card.pku.edu.cn/user/user`
2. Run `python card_query.py <account> --start-date YYYY-MM-DD` to fetch transactions from the specified date
3. Run `python transaction_analysis.py card_transactions_xxx.json` to analyze the transactions
