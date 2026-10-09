
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profit_loss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL NOT NULL,
    operating_profit REAL NOT NULL,
    ebitda REAL NOT NULL,
    net_profit REAL NOT NULL,
    UNIQUE(ticker, year),
    FOREIGN KEY(ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS balance_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    year INTEGER NOT NULL,
    total_assets REAL NOT NULL,
    shareholders_equity REAL NOT NULL,
    total_debt REAL NOT NULL,
    other_liabilities REAL NOT NULL,
    current_assets REAL NOT NULL,
    current_liabilities REAL NOT NULL,
    UNIQUE(ticker, year),
    FOREIGN KEY(ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS cash_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    year INTEGER NOT NULL,
    cash_from_operations REAL NOT NULL,
    cash_from_investing REAL NOT NULL,
    cash_from_financing REAL NOT NULL,
    capex REAL NOT NULL,
    UNIQUE(ticker, year),
    FOREIGN KEY(ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    UNIQUE(ticker, date),
    FOREIGN KEY(ticker) REFERENCES companies(ticker)
);

CREATE INDEX IF NOT EXISTS idx_pnl_ticker_year ON profit_loss(ticker, year);
CREATE INDEX IF NOT EXISTS idx_bs_ticker_year ON balance_sheet(ticker, year);
CREATE INDEX IF NOT EXISTS idx_cf_ticker_year ON cash_flow(ticker, year);
CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON stock_prices(ticker, date);
