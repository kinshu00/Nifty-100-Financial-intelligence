def validate_data(data):
    errors = []
    warnings = []

    companies = data["companies"]
    for name, df in data.items():
        if df.empty:
            errors.append(f"{name}: dataset is empty")

    if companies["ticker"].duplicated().any():
        errors.append("companies: duplicate ticker values found")

    known_tickers = set(companies["ticker"])
    for name, df in data.items():
        if name != "companies" and "ticker" in df.columns:
            unknown = set(df["ticker"].dropna()) - known_tickers
            if unknown:
                errors.append(f"{name}: unknown tickers: {sorted(unknown)}")

    for name, df in data.items():
        nulls = int(df.isna().sum().sum())
        if nulls:
            warnings.append(f"{name}: {nulls} missing values")

    for name in ["profit_loss", "balance_sheet", "cash_flow"]:
        df = data[name]
        if df.duplicated(["ticker", "year"]).any():
            errors.append(f"{name}: duplicate ticker/year records found")

    prices = data["stock_prices"]
    if prices.duplicated(["ticker", "date"]).any():
        errors.append("stock_prices: duplicate ticker/date records found")

    pnl = data["profit_loss"]
    if (pnl["sales"] < 0).any():
        errors.append("profit_loss: negative sales detected")

    invalid_ohlc = (
        (prices["high"] < prices[["open", "close"]].max(axis=1)) |
        (prices["low"] > prices[["open", "close"]].min(axis=1)) |
        (prices["low"] <= 0) |
        (prices["close"] <= 0)
    ).any()
    if invalid_ohlc:
        errors.append("stock_prices: invalid OHLC relationship")

    return errors, warnings
