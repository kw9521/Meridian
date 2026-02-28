from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random
import json, yfinance as yf

from .models import Holding, Transaction
from login.models import Profile
from django.db.models import Sum
from django.conf import settings


@login_required
def api_simulate(request, ticker):
    """Returns a slightly randomized price for demo purposes."""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period='1d')
        base_price = round(hist['Close'].iloc[-1], 2)
        
        # Random walk: ±0.5% per tick
        change_pct = random.uniform(-0.005, 0.005)
        simulated_price = round(base_price * (1 + change_pct), 2)
        change = round(simulated_price - base_price, 2)
        change_pct_display = round(change_pct * 100, 3)
        
        return JsonResponse({
            'ticker': ticker.upper(),
            'current_price': simulated_price,
            'change': change,
            'change_pct': change_pct_display,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


@login_required
def dashboard(request):
    return render(request, 'stocks/dashboard.html')

@login_required
def stock_view(request, ticker):
    return render(request, 'stocks/stock.html', {'ticker': ticker.upper()})

@login_required
def portfolio_view(request):
    return render(request, 'stocks/portfolio.html')

@login_required
def transactions_view(request):
    txns = Transaction.objects.filter(user=request.user).order_by('-created_at')[:50]
    profile = Profile.objects.get(user=request.user)
    
    # Calculate summary stats
    total_spent = sum(t.total for t in txns if t.action == 'BUY')
    total_received = sum(t.total for t in txns if t.action == 'SELL')
    net = round(total_received - total_spent, 2)
    total_trades = txns.count()
    buy_count = sum(1 for t in txns if t.action == 'BUY')
    sell_count = sum(1 for t in txns if t.action == 'SELL')

    # Best and worst single trade
    sell_txns = [t for t in txns if t.action == 'SELL']
    best_trade = None
    worst_trade = None

    if sell_txns:
        # For each sell, find the avg buy price for that ticker to compute gain
        trade_gains = []
        for t in sell_txns:
            buys = Transaction.objects.filter(
                user=request.user, ticker=t.ticker, action='BUY',
                created_at__lte=t.created_at
            )
            if buys.exists():
                avg_buy = sum(b.price for b in buys) / buys.count()
                gain = round((t.price - avg_buy) * t.shares, 2)
                trade_gains.append((t, gain))
        if trade_gains:
            best_trade = max(trade_gains, key=lambda x: x[1])
            worst_trade = min(trade_gains, key=lambda x: x[1])

    context = {
        'transactions': txns,
        'total_spent': round(total_spent, 2),
        'total_received': round(total_received, 2),
        'net': net,
        'total_trades': total_trades,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
    }
    return render(request, 'stocks/transactions.html', context)


# ── API endpoints ──────────────────────────────────────

@login_required
def api_stock(request, ticker):
    try:
        ticker = ticker.upper()
        period = request.GET.get('period', '3mo')
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        if history.empty:
            return JsonResponse({'error': 'Not found'}, status=404)
        info = stock.info
        data = [{'date': str(d.date()), 'close': round(r['Close'], 2)}
                for d, r in history.iterrows()]
        current = data[-1]['close']
        prev = data[-2]['close'] if len(data) > 1 else current
        change = round(current - prev, 2)
        change_pct = round((change / prev) * 100, 2) if prev else 0
        return JsonResponse({
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'current_price': current,
            'change': change,
            'change_pct': change_pct,
            'sector': info.get('sector', 'N/A'),
            'market_cap': info.get('marketCap'),
            'history': data,
            'description': info.get('longBusinessSummary', ''),
            'week_52_high': info.get('fiftyTwoWeekHigh'),
            'week_52_low': info.get('fiftyTwoWeekLow'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume'),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'pe_ratio': info.get('trailingPE'),
            'dividend_yield': info.get('dividendYield'),
            'employees': info.get('fullTimeEmployees'),
            'website': info.get('website', ''),
            'exchange': info.get('exchange', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# dict to map company name to their ticker for search bar
COMPANY_NAME_MAP = {
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'amazon': 'AMZN',
    'tesla': 'TSLA',
    'nvidia': 'NVDA',
    'meta': 'META',
    'facebook': 'META',
    'netflix': 'NFLX',
    'spotify': 'SPOT',
    'uber': 'UBER',
    'lyft': 'LYFT',
    'airbnb': 'ABNB',
    'paypal': 'PYPL',
    'visa': 'V',
    'mastercard': 'MA',
    'jpmorgan': 'JPM',
    'jp morgan': 'JPM',
    'goldman sachs': 'GS',
    'bank of america': 'BAC',
    'disney': 'DIS',
    'walmart': 'WMT',
    'target': 'TGT',
    'nike': 'NKE',
    'coca cola': 'KO',
    'cocacola': 'KO',
    'pepsi': 'PEP',
    'pepsico': 'PEP',
    'mcdonalds': 'MCD',
    "mcdonald's": 'MCD',
    'starbucks': 'SBUX',
    'intel': 'INTC',
    'amd': 'AMD',
    'advanced micro devices': 'AMD',
    'qualcomm': 'QCOM',
    'salesforce': 'CRM',
    'oracle': 'ORCL',
    'adobe': 'ADBE',
    'zoom': 'ZM',
    'shopify': 'SHOP',
    'twitter': 'TWTR',
    'snapchat': 'SNAP',
    'snap': 'SNAP',
    'coinbase': 'COIN',
    'robinhood': 'HOOD',
    'palantir': 'PLTR',
    'spy': 'SPY',
    's&p 500': 'SPY',
    'sp500': 'SPY',
    'boeing': 'BA',
    'ford': 'F',
    'gm': 'GM',
    'general motors': 'GM',
    'exxon': 'XOM',
    'chevron': 'CVX',
    'johnson and johnson': 'JNJ',
    'johnson & johnson': 'JNJ',
    'pfizer': 'PFE',
    'moderna': 'MRNA',
    'at&t': 'T',
    'att': 'T',
    'verizon': 'VZ',
    'comcast': 'CMCSA',
    'berkshire': 'BRK-B',
    'berkshire hathaway': 'BRK-B',
}

@login_required
def api_search(request, query):
    try:
        # First check if the query matches a company name
        normalized = query.lower().strip()
        ticker = COMPANY_NAME_MAP.get(normalized, query.upper())

        stock = yf.Ticker(ticker)
        history = stock.history(period='5d')
        info = stock.info

        if history.empty or not info.get('longName'):
            return JsonResponse({'error': 'Not found'}, status=404)

        current = round(history['Close'].iloc[-1], 2)
        prev = round(history['Close'].iloc[-2], 2) if len(history) > 1 else current
        change_pct = round(((current - prev) / prev) * 100, 2)

        return JsonResponse({
            'ticker': ticker,
            'name': info.get('longName'),
            'current_price': current,
            'change_pct': change_pct,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required
def api_portfolio(request):
    profile = Profile.objects.get(user=request.user)
    holdings_qs = (Holding.objects
                   .filter(user=request.user)
                   .values('ticker')
                   .annotate(total_shares=Sum('shares')))
    holdings = []
    total_invested = 0
    for h in holdings_qs:
        if h['total_shares'] <= 0:
            continue
        try:
            hist = yf.Ticker(h['ticker']).history(period='2d')
            current_price = round(hist['Close'].iloc[-1], 2)
        except:
            current_price = 0
        avg_price = Holding.objects.filter(user=request.user, ticker=h['ticker']).aggregate(avg=Sum('buy_price'))
        # compute weighted avg
        all_lots = Holding.objects.filter(user=request.user, ticker=h['ticker'])
        weighted = sum(l.shares * l.buy_price for l in all_lots) / h['total_shares']
        market_value = round(current_price * h['total_shares'], 2)
        cost_basis = round(weighted * h['total_shares'], 2)
        gain_loss = round(market_value - cost_basis, 2)
        gain_loss_pct = round((gain_loss / cost_basis) * 100, 2) if cost_basis else 0
        total_invested += market_value
        holdings.append({
            'ticker': h['ticker'],
            'shares': h['total_shares'],
            'avg_price': round(weighted, 2),
            'current_price': current_price,
            'market_value': market_value,
            'cost_basis': cost_basis,
            'gain_loss': gain_loss,
            'gain_loss_pct': gain_loss_pct,
        })
    total_value = round(profile.balance + total_invested, 2)
    overall_gain = round(total_value - 100000, 2)
    return JsonResponse({
        'balance': round(profile.balance, 2),
        'invested_value': round(total_invested, 2),
        'total_value': total_value,
        'overall_gain': overall_gain,
        'overall_gain_pct': round((overall_gain / 100000) * 100, 2),
        'holdings': holdings,
    })

@login_required
@require_POST
def api_buy(request):
    data = json.loads(request.body)
    ticker = data['ticker'].upper()
    shares = float(data['shares'])
    price = float(data['price'])
    total = shares * price
    profile = Profile.objects.get(user=request.user)
    if profile.balance < total:
        return JsonResponse({'error': 'Insufficient funds'}, status=400)
    profile.balance -= total
    profile.save()
    Holding.objects.create(user=request.user, ticker=ticker, shares=shares, buy_price=price)
    Transaction.objects.create(user=request.user, ticker=ticker, action='BUY', shares=shares, price=price, total=total)
    return JsonResponse({'success': True, 'message': f'Bought {shares} shares of {ticker} at ${price:.2f}'})

@login_required
@require_POST
def api_sell(request):
    data = json.loads(request.body)
    ticker = data['ticker'].upper()
    shares = float(data['shares'])
    price = float(data['price'])
    total_shares = Holding.objects.filter(user=request.user, ticker=ticker).aggregate(s=Sum('shares'))['s'] or 0
    if total_shares < shares:
        return JsonResponse({'error': 'Not enough shares'}, status=400)
    total = shares * price
    profile = Profile.objects.get(user=request.user)
    profile.balance += total
    profile.save()
    Holding.objects.create(user=request.user, ticker=ticker, shares=-shares, buy_price=price)
    Transaction.objects.create(user=request.user, ticker=ticker, action='SELL', shares=shares, price=price, total=total)
    return JsonResponse({'success': True, 'message': f'Sold {shares} shares of {ticker} at ${price:.2f}'})

@login_required
def api_user(request):
    profile = Profile.objects.get(user=request.user)
    return JsonResponse({'username': request.user.username, 'balance': profile.balance})

# stimulate time traveling to see gains/losses on a past date using real historical data
@login_required
def api_timetravel(request):
    """
    Given a date offset (days ago), return what each holding would be worth
    at that point in time using real historical data.
    """
    days_ago = int(request.GET.get('days', 0))
    from datetime import datetime, timedelta
    import pandas as pd
    
    target_date = datetime.now() - timedelta(days=days_ago)
    
    conn_holdings = Holding.objects.filter(user=request.user).values('ticker').annotate(total_shares=Sum('shares'))
    
    results = []
    total_then = 0
    total_now = 0
    
    for h in conn_holdings:
        if h['total_shares'] <= 0:
            continue
        try:
            stock = yf.Ticker(h['ticker'])
            # Pull enough history to cover the range
            history = stock.history(period='1y')
            if history.empty:
                continue
            
            # Get price at target date (closest trading day)
            history.index = history.index.tz_localize(None)
            past = history[history.index <= target_date]
            now = history
            
            if past.empty:
                continue
                
            price_then = round(float(past['Close'].iloc[-1]), 2)
            price_now = round(float(now['Close'].iloc[-1]), 2)
            shares = h['total_shares']
            value_then = round(price_then * shares, 2)
            value_now = round(price_now * shares, 2)
            gain = round(value_now - value_then, 2)
            gain_pct = round((gain / value_then) * 100, 2) if value_then else 0
            
            total_then += value_then
            total_now += value_now
            
            results.append({
                'ticker': h['ticker'],
                'shares': shares,
                'price_then': price_then,
                'price_now': price_now,
                'value_then': value_then,
                'value_now': value_now,
                'gain': gain,
                'gain_pct': gain_pct,
            })
        except Exception as e:
            continue
    
    total_gain = round(total_now - total_then, 2)
    total_gain_pct = round((total_gain / total_then) * 100, 2) if total_then else 0
    
    return JsonResponse({
        'days_ago': days_ago,
        'date': target_date.strftime('%b %d, %Y'),
        'total_then': round(total_then, 2),
        'total_now': round(total_now, 2),
        'total_gain': total_gain,
        'total_gain_pct': total_gain_pct,
        'holdings': results,
    })

# to get real life articles as to what might have happened to a stock over a given time period
# and use Gemini to explain the move in simple terms
@login_required  
def api_stock_story(request, ticker):
    """
    Returns real news headlines + a Gemini-powered explanation
    of why a stock moved over a given time period.
    """
    days = int(request.GET.get('days', 30))
    
    # ── Pull real news from Yahoo Finance ──────────────────────────
    try:
        import requests as req
        headers = {'User-Agent': 'Mozilla/5.0'}
        news_url = f'https://query2.finance.yahoo.com/v1/finance/search?q={ticker}&quotesCount=0&newsCount=5'
        news_res = req.get(news_url, headers=headers, timeout=5)
        news_data = news_res.json()
        articles = news_data.get('news', [])
        headlines = [a.get('title', '') for a in articles if a.get('title')][:5]
    except:
        headlines = []

    # ── Get price change data ──────────────────────────────────────
    try:
        from datetime import datetime, timedelta
        stock = yf.Ticker(ticker)
        history = stock.history(period='1y')
        history.index = history.index.tz_localize(None)
        target = datetime.now() - timedelta(days=days)
        past = history[history.index <= target]
        price_then = round(float(past['Close'].iloc[-1]), 2) if not past.empty else None
        price_now = round(float(history['Close'].iloc[-1]), 2)
        info = stock.info
        company_name = info.get('longName', ticker)
        sector = info.get('sector', '')
    except:
        price_then = None
        price_now = None
        company_name = ticker
        sector = ''

    # ── Ask Gemini to explain the move ────────────────────────────
    ai_summary = None
    try:
        import requests as req
        change_str = ''
        if price_then and price_now:
            change = round(price_now - price_then, 2)
            change_pct = round((change / price_then) * 100, 1)
            direction = 'up' if change >= 0 else 'down'
            change_str = f"The stock moved {direction} {abs(change_pct)}% (from ${price_then} to ${price_now}) over the past {days} days."

        headlines_str = '\n'.join(f'- {h}' for h in headlines) if headlines else 'No headlines available.'

        prompt = f"""You are a financial educator helping beginners understand the stock market.

Company: {company_name} ({ticker}), Sector: {sector}
{change_str}

Recent headlines:
{headlines_str}

In 2-3 short, plain-English sentences, explain to a beginner WHY this stock likely moved the way it did over this period. Reference the headlines if relevant. Be specific but avoid jargon. Do not use bullet points."""

        gemini_res = req.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}',
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=10
        )
        gemini_data = gemini_res.json()
        ai_summary = gemini_data['candidates'][0]['content']['parts'][0]['text']
    except:
        ai_summary = None

    return JsonResponse({
        'ticker': ticker,
        'headlines': [{'title': a.get('title',''), 'link': a.get('link',''), 'publisher': a.get('publisher','')} for a in articles[:5]] if articles else [],
        'ai_summary': ai_summary,
        'price_then': price_then,
        'price_now': price_now,
    })