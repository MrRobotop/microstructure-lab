#pragma once

#include <cstdint>
#include <deque>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "microstructure/order.hpp"
#include "microstructure/snapshot.hpp"
#include "microstructure/trade.hpp"

namespace microstructure {

struct CancelResult {
  bool accepted;
  std::string message;
};

class Book {
 public:
  explicit Book(std::string symbol);

  [[nodiscard]] const std::string& symbol() const noexcept;
  [[nodiscard]] bool has_order(const std::string& order_id) const;
  [[nodiscard]] std::optional<Order> find_order(const std::string& order_id) const;
  [[nodiscard]] Snapshot snapshot(std::int64_t timestamp) const;
  [[nodiscard]] const std::vector<Trade>& trades() const noexcept;

  std::vector<Trade> add_limit_order(const Order& order);
  std::vector<Trade> submit_market_order(const Order& order);
  CancelResult cancel_order(const std::string& order_id);
  std::vector<Trade> modify_order(std::int64_t timestamp,
                                  const std::string& order_id,
                                  std::int64_t new_price_ticks,
                                  std::int64_t new_quantity);

 private:
  struct OrderLocation {
    OrderSide side;
    std::int64_t price_ticks;
  };

  using BidLevels = std::map<std::int64_t, std::deque<Order>, std::greater<std::int64_t>>;
  using AskLevels = std::map<std::int64_t, std::deque<Order>>;

  [[nodiscard]] bool can_match(const Order& incoming) const;
  [[nodiscard]] bool crosses(const Order& incoming) const;
  [[nodiscard]] std::int64_t next_trade_id();
  [[nodiscard]] std::int64_t best_bid_depth() const;
  [[nodiscard]] std::int64_t best_ask_depth() const;

  std::vector<Trade> match(Order& incoming);
  void rest_order(const Order& order);
  void validate_order_for_book(const Order& order) const;
  void erase_filled_front(OrderSide side, std::int64_t price_ticks);
  std::optional<Order> find_order_on_side(const OrderLocation& location,
                                          const std::string& order_id) const;

  std::string symbol_;
  BidLevels bids_;
  AskLevels asks_;
  std::unordered_map<std::string, OrderLocation> order_index_;
  std::vector<Trade> trades_;
  std::int64_t next_trade_sequence_;
};

}  // namespace microstructure
