#include "microstructure/book.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

namespace microstructure {

Book::Book(std::string symbol) : symbol_(std::move(symbol)), next_trade_sequence_(1) {
  if (symbol_.empty()) {
    throw std::invalid_argument("book symbol must not be empty");
  }
}

const std::string& Book::symbol() const noexcept { return symbol_; }

bool Book::has_order(const std::string& order_id) const {
  return order_index_.find(order_id) != order_index_.end();
}

std::optional<Order> Book::find_order(const std::string& order_id) const {
  const auto location = order_index_.find(order_id);
  if (location == order_index_.end()) {
    return std::nullopt;
  }
  return find_order_on_side(location->second, order_id);
}

Snapshot Book::snapshot(std::int64_t timestamp) const {
  const std::optional<std::int64_t> best_bid =
      bids_.empty() ? std::nullopt : std::optional<std::int64_t>{bids_.begin()->first};
  const std::optional<std::int64_t> best_ask =
      asks_.empty() ? std::nullopt : std::optional<std::int64_t>{asks_.begin()->first};
  return Snapshot(timestamp, symbol_, best_bid, best_ask, best_bid_depth(), best_ask_depth());
}

const std::vector<Trade>& Book::trades() const noexcept { return trades_; }

std::vector<Trade> Book::add_limit_order(const Order& order) {
  validate_order_for_book(order);
  if (order.type() != OrderType::Limit) {
    throw std::invalid_argument("add_limit_order requires a limit order");
  }
  if (has_order(order.order_id())) {
    throw std::invalid_argument("duplicate order_id");
  }

  Order incoming = order;
  auto generated_trades = match(incoming);
  if (incoming.remaining_quantity() > 0) {
    rest_order(incoming);
  }
  return generated_trades;
}

std::vector<Trade> Book::submit_market_order(const Order& order) {
  validate_order_for_book(order);
  if (order.type() != OrderType::Market) {
    throw std::invalid_argument("submit_market_order requires a market order");
  }
  if (has_order(order.order_id())) {
    throw std::invalid_argument("duplicate order_id");
  }

  Order incoming = order;
  return match(incoming);
}

CancelResult Book::cancel_order(const std::string& order_id) {
  const auto location_iter = order_index_.find(order_id);
  if (location_iter == order_index_.end()) {
    return {false, "order_id not found"};
  }

  const auto location = location_iter->second;
  if (location.side == OrderSide::Buy) {
    auto level = bids_.find(location.price_ticks);
    if (level == bids_.end()) {
      order_index_.erase(order_id);
      return {false, "order_id index pointed to missing bid level"};
    }
    auto& orders = level->second;
    const auto order_iter = std::find_if(orders.begin(), orders.end(), [&order_id](const Order& order) {
      return order.order_id() == order_id;
    });
    if (order_iter == orders.end()) {
      order_index_.erase(order_id);
      return {false, "order_id index pointed to missing bid order"};
    }
    order_iter->cancel();
    orders.erase(order_iter);
    if (orders.empty()) {
      bids_.erase(level);
    }
  } else {
    auto level = asks_.find(location.price_ticks);
    if (level == asks_.end()) {
      order_index_.erase(order_id);
      return {false, "order_id index pointed to missing ask level"};
    }
    auto& orders = level->second;
    const auto order_iter = std::find_if(orders.begin(), orders.end(), [&order_id](const Order& order) {
      return order.order_id() == order_id;
    });
    if (order_iter == orders.end()) {
      order_index_.erase(order_id);
      return {false, "order_id index pointed to missing ask order"};
    }
    order_iter->cancel();
    orders.erase(order_iter);
    if (orders.empty()) {
      asks_.erase(level);
    }
  }

  order_index_.erase(order_id);
  return {true, "cancelled"};
}

std::vector<Trade> Book::modify_order(std::int64_t timestamp,
                                      const std::string& order_id,
                                      std::int64_t new_price_ticks,
                                      std::int64_t new_quantity) {
  const auto existing = find_order(order_id);
  if (!existing.has_value()) {
    throw std::out_of_range("order_id not found");
  }

  const auto side = existing->side();
  const auto cancel = cancel_order(order_id);
  if (!cancel.accepted) {
    throw std::logic_error(cancel.message);
  }

  return add_limit_order(Order(order_id,
                               timestamp,
                               symbol_,
                               side,
                               OrderType::Limit,
                               new_price_ticks,
                               new_quantity));
}

bool Book::can_match(const Order& incoming) const {
  return incoming.side() == OrderSide::Buy ? !asks_.empty() : !bids_.empty();
}

bool Book::crosses(const Order& incoming) const {
  if (!can_match(incoming)) {
    return false;
  }
  if (incoming.type() == OrderType::Market) {
    return true;
  }
  if (incoming.side() == OrderSide::Buy) {
    return incoming.price_ticks() >= asks_.begin()->first;
  }
  return incoming.price_ticks() <= bids_.begin()->first;
}

std::int64_t Book::next_trade_id() { return next_trade_sequence_++; }

std::int64_t Book::best_bid_depth() const {
  if (bids_.empty()) {
    return 0;
  }
  std::int64_t depth = 0;
  for (const auto& order : bids_.begin()->second) {
    depth += order.remaining_quantity();
  }
  return depth;
}

std::int64_t Book::best_ask_depth() const {
  if (asks_.empty()) {
    return 0;
  }
  std::int64_t depth = 0;
  for (const auto& order : asks_.begin()->second) {
    depth += order.remaining_quantity();
  }
  return depth;
}

std::vector<Trade> Book::match(Order& incoming) {
  std::vector<Trade> generated_trades;

  while (incoming.remaining_quantity() > 0 && crosses(incoming)) {
    auto& opposite_level =
        incoming.side() == OrderSide::Buy ? asks_.begin()->second : bids_.begin()->second;
    auto& resting = opposite_level.front();
    const auto fill_quantity = std::min(incoming.remaining_quantity(), resting.remaining_quantity());
    const auto trade_price = resting.price_ticks();

    resting.apply_fill(fill_quantity);
    incoming.apply_fill(fill_quantity);

    Trade trade("trade-" + std::to_string(next_trade_id()),
                incoming.timestamp(),
                symbol_,
                trade_price,
                fill_quantity,
                incoming.side(),
                resting.order_id(),
                incoming.order_id());
    generated_trades.push_back(trade);
    trades_.push_back(trade);

    if (resting.status() == OrderStatus::Filled) {
      order_index_.erase(resting.order_id());
      erase_filled_front(resting.side(), trade_price);
    }
  }

  return generated_trades;
}

void Book::rest_order(const Order& order) {
  if (!order.is_active()) {
    return;
  }
  order_index_.emplace(order.order_id(), OrderLocation{order.side(), order.price_ticks()});
  if (order.side() == OrderSide::Buy) {
    bids_[order.price_ticks()].push_back(order);
  } else {
    asks_[order.price_ticks()].push_back(order);
  }
}

void Book::validate_order_for_book(const Order& order) const {
  if (order.symbol() != symbol_) {
    throw std::invalid_argument("order symbol does not match book symbol");
  }
  if (!order.is_active()) {
    throw std::invalid_argument("order must be active");
  }
}

void Book::erase_filled_front(OrderSide side, std::int64_t price_ticks) {
  if (side == OrderSide::Buy) {
    auto level = bids_.find(price_ticks);
    if (level != bids_.end()) {
      level->second.pop_front();
      if (level->second.empty()) {
        bids_.erase(level);
      }
    }
  } else {
    auto level = asks_.find(price_ticks);
    if (level != asks_.end()) {
      level->second.pop_front();
      if (level->second.empty()) {
        asks_.erase(level);
      }
    }
  }
}

std::optional<Order> Book::find_order_on_side(const OrderLocation& location,
                                              const std::string& order_id) const {
  if (location.side == OrderSide::Buy) {
    const auto level = bids_.find(location.price_ticks);
    if (level == bids_.end()) {
      return std::nullopt;
    }
    for (const auto& order : level->second) {
      if (order.order_id() == order_id) {
        return order;
      }
    }
  } else {
    const auto level = asks_.find(location.price_ticks);
    if (level == asks_.end()) {
      return std::nullopt;
    }
    for (const auto& order : level->second) {
      if (order.order_id() == order_id) {
        return order;
      }
    }
  }
  return std::nullopt;
}

}  // namespace microstructure
