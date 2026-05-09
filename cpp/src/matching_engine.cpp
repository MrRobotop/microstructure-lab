#include "microstructure/matching_engine.hpp"

#include <stdexcept>
#include <utility>

namespace microstructure {

namespace {

EngineResult accepted(std::vector<Trade> trades = {}) {
  return {EngineStatus::Accepted, "accepted", std::move(trades)};
}

EngineResult rejected(std::string message) {
  return {EngineStatus::Rejected, std::move(message), {}};
}

EngineResult not_found(std::string message) {
  return {EngineStatus::NotFound, std::move(message), {}};
}

}  // namespace

EngineResult MatchingEngine::add_limit_order(const Order& order) {
  try {
    return accepted(book_for_symbol(order.symbol()).add_limit_order(order));
  } catch (const std::exception& exc) {
    return rejected(exc.what());
  }
}

EngineResult MatchingEngine::submit_market_order(const Order& order) {
  try {
    return accepted(book_for_symbol(order.symbol()).submit_market_order(order));
  } catch (const std::exception& exc) {
    return rejected(exc.what());
  }
}

EngineResult MatchingEngine::cancel_order(const std::string& symbol, const std::string& order_id) {
  auto* book = find_book(symbol);
  if (book == nullptr) {
    return not_found("symbol not found");
  }
  const auto result = book->cancel_order(order_id);
  if (!result.accepted) {
    return not_found(result.message);
  }
  return accepted();
}

EngineResult MatchingEngine::modify_order(std::int64_t timestamp,
                                          const std::string& symbol,
                                          const std::string& order_id,
                                          std::int64_t new_price_ticks,
                                          std::int64_t new_quantity) {
  auto* book = find_book(symbol);
  if (book == nullptr) {
    return not_found("symbol not found");
  }
  try {
    return accepted(book->modify_order(timestamp, order_id, new_price_ticks, new_quantity));
  } catch (const std::out_of_range& exc) {
    return not_found(exc.what());
  } catch (const std::exception& exc) {
    return rejected(exc.what());
  }
}

EngineResult MatchingEngine::apply_event(const Event& event) {
  switch (event.type()) {
    case EventType::Add:
      return add_limit_order(Order(event.order_id(),
                                   event.timestamp(),
                                   event.symbol(),
                                   event.side().value(),
                                   OrderType::Limit,
                                   event.price_ticks().value(),
                                   event.quantity().value()));
    case EventType::Cancel:
      return cancel_order(event.symbol(), event.order_id());
    case EventType::Modify:
      return modify_order(event.timestamp(),
                          event.symbol(),
                          event.order_id(),
                          event.price_ticks().value(),
                          event.quantity().value());
    case EventType::Market:
      return submit_market_order(Order(event.order_id(),
                                       event.timestamp(),
                                       event.symbol(),
                                       event.side().value(),
                                       OrderType::Market,
                                       0,
                                       event.quantity().value()));
  }
  return rejected("unknown event type");
}

Snapshot MatchingEngine::snapshot(std::int64_t timestamp, const std::string& symbol) const {
  const auto* book = find_book(symbol);
  if (book == nullptr) {
    return Snapshot(timestamp, symbol, std::nullopt, std::nullopt, 0, 0);
  }
  return book->snapshot(timestamp);
}

std::optional<Order> MatchingEngine::find_order(const std::string& symbol,
                                                const std::string& order_id) const {
  const auto* book = find_book(symbol);
  if (book == nullptr) {
    return std::nullopt;
  }
  return book->find_order(order_id);
}

const std::vector<Trade>& MatchingEngine::trades(const std::string& symbol) const {
  const auto* book = find_book(symbol);
  if (book == nullptr) {
    return empty_trades_;
  }
  return book->trades();
}

Book& MatchingEngine::book_for_symbol(const std::string& symbol) {
  auto [iter, inserted] = books_.try_emplace(symbol, symbol);
  (void)inserted;
  return iter->second;
}

Book* MatchingEngine::find_book(const std::string& symbol) {
  const auto iter = books_.find(symbol);
  if (iter == books_.end()) {
    return nullptr;
  }
  return &iter->second;
}

const Book* MatchingEngine::find_book(const std::string& symbol) const {
  const auto iter = books_.find(symbol);
  if (iter == books_.end()) {
    return nullptr;
  }
  return &iter->second;
}

}  // namespace microstructure
