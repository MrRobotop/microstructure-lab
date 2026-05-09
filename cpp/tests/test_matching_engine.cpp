#include <cassert>
#include <cstdint>
#include <functional>
#include <optional>
#include <stdexcept>
#include <string>

#include "microstructure/event.hpp"
#include "microstructure/matching_engine.hpp"
#include "microstructure/order.hpp"
#include "microstructure/snapshot.hpp"
#include "microstructure/trade.hpp"

namespace {

template <typename Exception>
void expect_throws(const std::function<void()>& fn) {
  bool thrown = false;
  try {
    fn();
  } catch (const Exception&) {
    thrown = true;
  }
  assert(thrown);
}

void test_order_constructor_and_fill_states() {
  microstructure::Order order(
      "order-1", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Limit, 101, 50);

  assert(order.order_id() == "order-1");
  assert(order.timestamp() == 100);
  assert(order.symbol() == "XYZ");
  assert(order.side() == microstructure::OrderSide::Buy);
  assert(order.type() == microstructure::OrderType::Limit);
  assert(order.price_ticks() == 101);
  assert(order.quantity() == 50);
  assert(order.remaining_quantity() == 50);
  assert(order.status() == microstructure::OrderStatus::New);
  assert(order.is_active());

  order.apply_fill(20);
  assert(order.remaining_quantity() == 30);
  assert(order.status() == microstructure::OrderStatus::PartiallyFilled);

  order.apply_fill(30);
  assert(order.remaining_quantity() == 0);
  assert(order.status() == microstructure::OrderStatus::Filled);
  assert(!order.is_active());
}

void test_order_validation() {
  expect_throws<std::invalid_argument>([] {
    microstructure::Order(
        "", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Limit, 101, 50);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Order(
        "order-1", 100, "", microstructure::OrderSide::Buy, microstructure::OrderType::Limit, 101, 50);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Order(
        "order-1", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Limit, 0, 50);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Order(
        "order-1", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Limit, 101, 0);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Order(
        "order-1", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Market, 101, 50);
  });
}

void test_order_invalid_state_transitions() {
  microstructure::Order order(
      "order-1", 100, "XYZ", microstructure::OrderSide::Sell, microstructure::OrderType::Limit, 101, 50);

  expect_throws<std::invalid_argument>([&order] { order.apply_fill(0); });
  expect_throws<std::invalid_argument>([&order] { order.apply_fill(51); });

  order.cancel();
  assert(order.status() == microstructure::OrderStatus::Cancelled);
  assert(!order.is_active());

  expect_throws<std::logic_error>([&order] { order.cancel(); });
  expect_throws<std::logic_error>([&order] { order.apply_fill(1); });
}

void test_market_order_validation() {
  microstructure::Order order(
      "market-1", 100, "XYZ", microstructure::OrderSide::Buy, microstructure::OrderType::Market, 0, 10);

  assert(order.type() == microstructure::OrderType::Market);
  assert(order.price_ticks() == 0);
  assert(order.remaining_quantity() == 10);
}

void test_trade_constructor_and_validation() {
  microstructure::Trade trade("trade-1",
                              101,
                              "XYZ",
                              102,
                              25,
                              microstructure::OrderSide::Buy,
                              "maker-1",
                              "taker-1");

  assert(trade.trade_id() == "trade-1");
  assert(trade.timestamp() == 101);
  assert(trade.symbol() == "XYZ");
  assert(trade.price_ticks() == 102);
  assert(trade.quantity() == 25);
  assert(trade.aggressor_side() == microstructure::OrderSide::Buy);
  assert(trade.maker_order_id() == "maker-1");
  assert(trade.taker_order_id() == "taker-1");

  expect_throws<std::invalid_argument>([] {
    microstructure::Trade(
        "trade-1", 101, "XYZ", 0, 25, microstructure::OrderSide::Buy, "maker-1", "taker-1");
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Trade(
        "trade-1", 101, "XYZ", 102, 0, microstructure::OrderSide::Buy, "maker-1", "taker-1");
  });
}

void test_event_factories() {
  const auto add = microstructure::Event::add_limit(
      100, "XYZ", "order-1", microstructure::OrderSide::Buy, 101, 50);
  assert(add.type() == microstructure::EventType::Add);
  assert(add.side().value() == microstructure::OrderSide::Buy);
  assert(add.price_ticks().value() == 101);
  assert(add.quantity().value() == 50);

  const auto cancel = microstructure::Event::cancel(101, "XYZ", "order-1");
  assert(cancel.type() == microstructure::EventType::Cancel);
  assert(!cancel.side().has_value());
  assert(!cancel.price_ticks().has_value());
  assert(!cancel.quantity().has_value());

  const auto modify = microstructure::Event::modify(102, "XYZ", "order-1", 103, 20);
  assert(modify.type() == microstructure::EventType::Modify);
  assert(!modify.side().has_value());
  assert(modify.price_ticks().value() == 103);
  assert(modify.quantity().value() == 20);

  const auto market = microstructure::Event::market(
      103, "XYZ", "market-1", microstructure::OrderSide::Sell, 15);
  assert(market.type() == microstructure::EventType::Market);
  assert(market.side().value() == microstructure::OrderSide::Sell);
  assert(!market.price_ticks().has_value());
  assert(market.quantity().value() == 15);

  expect_throws<std::invalid_argument>([] {
    microstructure::Event::add_limit(
        100, "XYZ", "order-1", microstructure::OrderSide::Buy, -1, 50);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Event::market(100, "XYZ", "market-1", microstructure::OrderSide::Buy, 0);
  });
}

void test_snapshot_metrics_and_validation() {
  const microstructure::Snapshot snapshot(100, "XYZ", 99, 101, 500, 400);

  assert(snapshot.timestamp() == 100);
  assert(snapshot.symbol() == "XYZ");
  assert(snapshot.best_bid_ticks().value() == 99);
  assert(snapshot.best_ask_ticks().value() == 101);
  assert(snapshot.spread_ticks().value() == 2);
  assert(snapshot.mid_price_ticks_x2().value() == 200);
  assert(snapshot.bid_depth() == 500);
  assert(snapshot.ask_depth() == 400);

  const microstructure::Snapshot one_sided(100, "XYZ", std::optional<std::int64_t>{99}, std::nullopt, 500, 0);
  assert(!one_sided.spread_ticks().has_value());
  assert(!one_sided.mid_price_ticks_x2().has_value());

  expect_throws<std::invalid_argument>([] {
    microstructure::Snapshot(100, "XYZ", 101, 101, 500, 400);
  });
  expect_throws<std::invalid_argument>([] {
    microstructure::Snapshot(100, "XYZ", 99, 101, -1, 400);
  });
}

microstructure::Order limit_order(const std::string& order_id,
                                  std::int64_t timestamp,
                                  microstructure::OrderSide side,
                                  std::int64_t price_ticks,
                                  std::int64_t quantity) {
  return microstructure::Order(
      order_id, timestamp, "XYZ", side, microstructure::OrderType::Limit, price_ticks, quantity);
}

microstructure::Order market_order(const std::string& order_id,
                                   std::int64_t timestamp,
                                   microstructure::OrderSide side,
                                   std::int64_t quantity) {
  return microstructure::Order(
      order_id, timestamp, "XYZ", side, microstructure::OrderType::Market, 0, quantity);
}

void test_buy_limit_rests_when_not_crossing() {
  microstructure::MatchingEngine engine;
  const auto result = engine.add_limit_order(
      limit_order("buy-1", 100, microstructure::OrderSide::Buy, 99, 50));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.empty());

  const auto snapshot = engine.snapshot(101, "XYZ");
  assert(snapshot.best_bid_ticks().value() == 99);
  assert(!snapshot.best_ask_ticks().has_value());
  assert(snapshot.bid_depth() == 50);
}

void test_sell_limit_rests_when_not_crossing() {
  microstructure::MatchingEngine engine;
  const auto result = engine.add_limit_order(
      limit_order("sell-1", 100, microstructure::OrderSide::Sell, 101, 40));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.empty());

  const auto snapshot = engine.snapshot(101, "XYZ");
  assert(!snapshot.best_bid_ticks().has_value());
  assert(snapshot.best_ask_ticks().value() == 101);
  assert(snapshot.ask_depth() == 40);
}

void test_market_buy_consumes_best_asks() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("ask-102", 100, microstructure::OrderSide::Sell, 102, 10));
  engine.add_limit_order(limit_order("ask-101", 101, microstructure::OrderSide::Sell, 101, 10));

  const auto result =
      engine.submit_market_order(market_order("market-buy", 102, microstructure::OrderSide::Buy, 15));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 2);
  assert(result.trades[0].price_ticks() == 101);
  assert(result.trades[0].quantity() == 10);
  assert(result.trades[0].maker_order_id() == "ask-101");
  assert(result.trades[1].price_ticks() == 102);
  assert(result.trades[1].quantity() == 5);
  assert(result.trades[1].maker_order_id() == "ask-102");

  const auto remaining = engine.find_order("XYZ", "ask-102");
  assert(remaining.has_value());
  assert(remaining->remaining_quantity() == 5);
}

void test_market_sell_consumes_best_bids() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("bid-99", 100, microstructure::OrderSide::Buy, 99, 10));
  engine.add_limit_order(limit_order("bid-100", 101, microstructure::OrderSide::Buy, 100, 10));

  const auto result =
      engine.submit_market_order(market_order("market-sell", 102, microstructure::OrderSide::Sell, 15));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 2);
  assert(result.trades[0].price_ticks() == 100);
  assert(result.trades[0].quantity() == 10);
  assert(result.trades[0].maker_order_id() == "bid-100");
  assert(result.trades[1].price_ticks() == 99);
  assert(result.trades[1].quantity() == 5);
  assert(result.trades[1].maker_order_id() == "bid-99");
}

void test_crossing_limit_executes_and_rests_remainder() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("ask-100", 100, microstructure::OrderSide::Sell, 100, 10));

  const auto result =
      engine.add_limit_order(limit_order("buy-cross", 101, microstructure::OrderSide::Buy, 101, 15));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 1);
  assert(result.trades[0].price_ticks() == 100);
  assert(result.trades[0].quantity() == 10);

  assert(!engine.find_order("XYZ", "ask-100").has_value());
  const auto remainder = engine.find_order("XYZ", "buy-cross");
  assert(remainder.has_value());
  assert(remainder->remaining_quantity() == 5);
  assert(remainder->status() == microstructure::OrderStatus::PartiallyFilled);
}

void test_full_fill_removes_resting_order() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("ask-100", 100, microstructure::OrderSide::Sell, 100, 10));

  const auto result =
      engine.submit_market_order(market_order("market-buy", 101, microstructure::OrderSide::Buy, 10));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 1);
  assert(!engine.find_order("XYZ", "ask-100").has_value());

  const auto snapshot = engine.snapshot(102, "XYZ");
  assert(!snapshot.best_ask_ticks().has_value());
  assert(snapshot.ask_depth() == 0);
}

void test_price_time_priority_at_same_price() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("ask-first", 100, microstructure::OrderSide::Sell, 101, 10));
  engine.add_limit_order(limit_order("ask-second", 101, microstructure::OrderSide::Sell, 101, 10));

  const auto result =
      engine.submit_market_order(market_order("market-buy", 102, microstructure::OrderSide::Buy, 15));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 2);
  assert(result.trades[0].maker_order_id() == "ask-first");
  assert(result.trades[0].quantity() == 10);
  assert(result.trades[1].maker_order_id() == "ask-second");
  assert(result.trades[1].quantity() == 5);

  const auto remaining = engine.find_order("XYZ", "ask-second");
  assert(remaining.has_value());
  assert(remaining->remaining_quantity() == 5);
}

void test_better_price_priority_across_levels() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("ask-worse", 100, microstructure::OrderSide::Sell, 102, 10));
  engine.add_limit_order(limit_order("ask-better", 101, microstructure::OrderSide::Sell, 101, 10));

  const auto result =
      engine.submit_market_order(market_order("market-buy", 102, microstructure::OrderSide::Buy, 10));

  assert(result.status == microstructure::EngineStatus::Accepted);
  assert(result.trades.size() == 1);
  assert(result.trades[0].maker_order_id() == "ask-better");
  assert(result.trades[0].price_ticks() == 101);
  assert(engine.find_order("XYZ", "ask-worse").has_value());
}

void test_cancel_removes_order_and_missing_cancel_fails() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("bid-1", 100, microstructure::OrderSide::Buy, 99, 10));

  const auto cancel = engine.cancel_order("XYZ", "bid-1");
  assert(cancel.status == microstructure::EngineStatus::Accepted);
  assert(!engine.find_order("XYZ", "bid-1").has_value());

  const auto missing = engine.cancel_order("XYZ", "missing");
  assert(missing.status == microstructure::EngineStatus::NotFound);

  const auto snapshot = engine.snapshot(101, "XYZ");
  assert(!snapshot.best_bid_ticks().has_value());
}

void test_snapshot_updates_after_trades_and_cancels() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("bid-1", 100, microstructure::OrderSide::Buy, 99, 10));
  engine.add_limit_order(limit_order("bid-2", 101, microstructure::OrderSide::Buy, 98, 20));
  engine.add_limit_order(limit_order("ask-1", 102, microstructure::OrderSide::Sell, 101, 10));
  engine.add_limit_order(limit_order("ask-2", 103, microstructure::OrderSide::Sell, 102, 20));

  auto snapshot = engine.snapshot(104, "XYZ");
  assert(snapshot.best_bid_ticks().value() == 99);
  assert(snapshot.best_ask_ticks().value() == 101);
  assert(snapshot.spread_ticks().value() == 2);
  assert(snapshot.bid_depth() == 10);
  assert(snapshot.ask_depth() == 10);

  engine.submit_market_order(market_order("market-buy", 105, microstructure::OrderSide::Buy, 10));
  snapshot = engine.snapshot(106, "XYZ");
  assert(snapshot.best_ask_ticks().value() == 102);
  assert(snapshot.ask_depth() == 20);

  engine.cancel_order("XYZ", "bid-1");
  snapshot = engine.snapshot(107, "XYZ");
  assert(snapshot.best_bid_ticks().value() == 98);
  assert(snapshot.bid_depth() == 20);
}

void test_deterministic_event_replay() {
  microstructure::MatchingEngine engine;
  std::vector<microstructure::Event> events{
      microstructure::Event::add_limit(
          100, "XYZ", "ask-1", microstructure::OrderSide::Sell, 101, 10),
      microstructure::Event::add_limit(
          101, "XYZ", "ask-2", microstructure::OrderSide::Sell, 102, 10),
      microstructure::Event::market(102, "XYZ", "buy-1", microstructure::OrderSide::Buy, 15),
  };

  std::vector<microstructure::Trade> replay_trades;
  for (const auto& event : events) {
    const auto result = engine.apply_event(event);
    assert(result.status == microstructure::EngineStatus::Accepted);
    replay_trades.insert(replay_trades.end(), result.trades.begin(), result.trades.end());
  }

  assert(replay_trades.size() == 2);
  assert(replay_trades[0].trade_id() == "trade-1");
  assert(replay_trades[0].maker_order_id() == "ask-1");
  assert(replay_trades[0].quantity() == 10);
  assert(replay_trades[1].trade_id() == "trade-2");
  assert(replay_trades[1].maker_order_id() == "ask-2");
  assert(replay_trades[1].quantity() == 5);
}

void test_modify_is_cancel_replace() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(limit_order("bid-1", 100, microstructure::OrderSide::Buy, 99, 10));

  const auto result = engine.modify_order(101, "XYZ", "bid-1", 100, 7);
  assert(result.status == microstructure::EngineStatus::Accepted);

  const auto modified = engine.find_order("XYZ", "bid-1");
  assert(modified.has_value());
  assert(modified->price_ticks() == 100);
  assert(modified->remaining_quantity() == 7);

  const auto snapshot = engine.snapshot(102, "XYZ");
  assert(snapshot.best_bid_ticks().value() == 100);
  assert(snapshot.bid_depth() == 7);
}

void test_duplicate_order_id_rejected_without_corrupting_book() {
  microstructure::MatchingEngine engine;
  const auto first =
      engine.add_limit_order(limit_order("bid-1", 100, microstructure::OrderSide::Buy, 99, 10));
  const auto duplicate =
      engine.add_limit_order(limit_order("bid-1", 101, microstructure::OrderSide::Buy, 98, 20));

  assert(first.status == microstructure::EngineStatus::Accepted);
  assert(duplicate.status == microstructure::EngineStatus::Rejected);

  const auto order = engine.find_order("XYZ", "bid-1");
  assert(order.has_value());
  assert(order->price_ticks() == 99);
  assert(order->remaining_quantity() == 10);

  const auto snapshot = engine.snapshot(102, "XYZ");
  assert(snapshot.best_bid_ticks().value() == 99);
  assert(snapshot.bid_depth() == 10);
}

void test_symbol_isolation() {
  microstructure::MatchingEngine engine;
  engine.add_limit_order(
      microstructure::Order("xyz-bid",
                            100,
                            "XYZ",
                            microstructure::OrderSide::Buy,
                            microstructure::OrderType::Limit,
                            99,
                            10));
  engine.add_limit_order(
      microstructure::Order("abc-ask",
                            101,
                            "ABC",
                            microstructure::OrderSide::Sell,
                            microstructure::OrderType::Limit,
                            101,
                            20));

  auto xyz_snapshot = engine.snapshot(102, "XYZ");
  auto abc_snapshot = engine.snapshot(102, "ABC");

  assert(xyz_snapshot.best_bid_ticks().value() == 99);
  assert(!xyz_snapshot.best_ask_ticks().has_value());
  assert(!abc_snapshot.best_bid_ticks().has_value());
  assert(abc_snapshot.best_ask_ticks().value() == 101);

  const auto missing_cross_symbol_cancel = engine.cancel_order("ABC", "xyz-bid");
  assert(missing_cross_symbol_cancel.status == microstructure::EngineStatus::NotFound);
  assert(engine.find_order("XYZ", "xyz-bid").has_value());
}

}  // namespace

int main() {
  test_order_constructor_and_fill_states();
  test_order_validation();
  test_order_invalid_state_transitions();
  test_market_order_validation();
  test_trade_constructor_and_validation();
  test_event_factories();
  test_snapshot_metrics_and_validation();
  test_buy_limit_rests_when_not_crossing();
  test_sell_limit_rests_when_not_crossing();
  test_market_buy_consumes_best_asks();
  test_market_sell_consumes_best_bids();
  test_crossing_limit_executes_and_rests_remainder();
  test_full_fill_removes_resting_order();
  test_price_time_priority_at_same_price();
  test_better_price_priority_across_levels();
  test_cancel_removes_order_and_missing_cancel_fails();
  test_snapshot_updates_after_trades_and_cancels();
  test_deterministic_event_replay();
  test_modify_is_cancel_replace();
  test_duplicate_order_id_rejected_without_corrupting_book();
  test_symbol_isolation();
  return 0;
}
