from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json, yfinance as yf
from .models import Holding, Transaction
from login.models import Profile
from django.db.models import Sum

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
    return render(request, 'stocks/transactions.html', {'transactions': txns})

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
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_search(request, ticker):
    try:
        stock = yf.Ticker(ticker.upper())
        history = stock.history(period='5d')
        info = stock.info
        if history.empty or not info.get('longName'):
            return JsonResponse({'error': 'Not found'}, status=404)
        current = round(history['Close'].iloc[-1], 2)
        prev = round(history['Close'].iloc[-2], 2) if len(history) > 1 else current
        change_pct = round(((current - prev) / prev) * 100, 2)
        return JsonResponse({'ticker': ticker.upper(), 'name': info.get('longName'), 'current_price': current, 'change_pct': change_pct})
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