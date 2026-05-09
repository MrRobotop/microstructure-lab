# Market Microstructure Notes

Microstructure-Lab models a simplified limit order book so execution workflows can be
tested without paid market data.

## Limit Order Book

The matching engine maintains bids and asks for each symbol. Prices are integer ticks.
Bids are prioritized from highest to lowest price; asks are prioritized from lowest to
highest price.

Within one price level, resting orders are matched by time priority. Earlier orders fill
before later orders at the same price.

## Order Types

The current engine supports:

- resting limit orders
- crossing limit orders
- market orders
- cancellations
- cancel-replace modifications

Crossing limit orders and market orders remove liquidity from the opposite side of the
book. Resting limit orders add liquidity when they do not cross.

## Fills

Orders can partially fill or fully fill. Every trade records:

- trade id
- timestamp
- symbol
- price in ticks
- quantity
- aggressor side
- maker order id
- taker order id

Execution strategies consume these fills to compute realized quantity, fill rate,
average fill price, and cost metrics.

## Synthetic Regimes

The synthetic generator provides deterministic scenarios:

- `normal`
- `thin_liquidity`
- `wide_spread`
- `volatility_spike`
- `toxic_flow`

These scenarios are controlled engineering inputs. They are useful for exercising
different book states and execution outcomes, but they are not calibrated to a real
venue.

## Execution Cost Intuition

The analytics layer focuses on costs that matter for execution research:

- spread cost
- slippage versus arrival price
- implementation shortfall
- VWAP slippage when a benchmark is supplied
- fill rate
- unfilled quantity
- opportunity cost
- participation rate

The platform intentionally avoids ranking strategies by one metric only. A strategy that
looks cheap on average fill price can still be poor if it leaves too much quantity
unfilled.

