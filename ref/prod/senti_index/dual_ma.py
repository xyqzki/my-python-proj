from zipline.api import order_target, record, symbol

ticker = 'AAPL'


def initialize(context):
    context.sym = symbol(ticker)
    context.i = 0


def handle_data(context, data):
    # Skip first 300 days to get full windows
    context.i += 1

    n_short = 100
    n_long = 300

    if context.i < n_long:
        return

    # Compute averages
    # history() has to be called with the same params
    # from above and returns a pandas dataframe.
    short_mavg = data.history(context.sym, 'price', n_short, '1d').mean()
    long_mavg = data.history(context.sym, 'price', n_long, '1d').mean()

    # Trading logic
    if short_mavg > long_mavg:
        # order_target orders as many shares as needed to
        # achieve the desired number of shares.
        order_target(context.sym, 100)
    elif short_mavg < long_mavg:
        order_target(context.sym, 0)

    # Save values for later inspection
    record(**{
        ticker: data.current(context.sym, "price"),
        'short_mavg': short_mavg,
        'long_mavg': long_mavg
    })


# Note: this function can be removed if running
# this algorithm on quantopian.com
def analyze(context=None, results=None):
    import matplotlib.pyplot as plt
    import logbook
    logbook.StderrHandler().push_application()
    log = logbook.Logger('Algorithm')

    fig = plt.figure(figsize=(12, 12))
    ax1 = fig.add_subplot(211)
    results.portfolio_value.plot(ax=ax1)
    ax1.set_ylabel('Portfolio value (USD)')

    ax2 = fig.add_subplot(212)
    ax2.set_ylabel('Price (USD)')

    # If data has been record()ed, then plot it.
    # Otherwise, log the fact that no data has been recorded.
    if (ticker in results and 'short_mavg' in results and
            'long_mavg' in results):
        results[ticker].plot(ax=ax2)
        results[['short_mavg', 'long_mavg']].plot(ax=ax2)

        trans = results.ix[[t != [] for t in results.transactions]]
        buys = trans.ix[[t[0]['amount'] > 0 for t in
                         trans.transactions]]
        sells = trans.ix[
            [t[0]['amount'] < 0 for t in trans.transactions]]
        ax2.plot(buys.index, results.short_mavg.ix[buys.index],
                 '^', markersize=10, color='m')
        ax2.plot(sells.index, results.short_mavg.ix[sells.index],
                 'v', markersize=10, color='k')
        plt.legend(loc=0)
    else:
        msg = '{}, short_mavg & long_mavg data not captured using record().'.format(ticker)
        ax2.annotate(msg, xy=(0.1, 0.5))
        log.info(msg)

    plt.show()
