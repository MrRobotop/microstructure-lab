#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "microstructure/book.hpp"
#include "microstructure/event.hpp"
#include "microstructure/order.hpp"
#include "microstructure/snapshot.hpp"
#include "microstructure/trade.hpp"

namespace microstructure {

enum class EngineStatus {
  Accepted,
  Rejected,
  NotFound,
};

struct EngineResult {
  EngineStatus status;
  std::string message;
  std::vector<Trade> trades;
};

class MatchingEngine {
 public:
  MatchingEngine() = default;

  EngineResult add_limit_order(const Order& order);
  EngineResult submit_market_order(const Order& order);
  EngineResult cancel_order(const std::string& symbol, const std::string& order_id);
  EngineResult modify_order(std::int64_t timestamp,
                            const std::string& symbol,
                            const std::string& order_id,
                            std::int64_t new_price_ticks,
                            std::int64_t new_quantity);
  EngineResult apply_event(const Event& event);

  [[nodiscard]] Snapshot snapshot(std::int64_t timestamp, const std::string& symbol) const;
  [[nodiscard]] std::optional<Order> find_order(const std::string& symbol,
                                                const std::string& order_id) const;
  [[nodiscard]] const std::vector<Trade>& trades(const std::string& symbol) const;

 private:
  Book& book_for_symbol(const std::string& symbol);
  [[nodiscard]] Book* find_book(const std::string& symbol);
  [[nodiscard]] const Book* find_book(const std::string& symbol) const;

  std::unordered_map<std::string, Book> books_;
  std::vector<Trade> empty_trades_;
};

}  // namespace microstructure
