#pragma once

#include <cstdint>
#include <optional>
#include <string>

#include "microstructure/order.hpp"

namespace microstructure {

enum class EventType {
  Add,
  Cancel,
  Modify,
  Market,
};

class Event {
 public:
  static Event add_limit(std::int64_t timestamp,
                         std::string symbol,
                         std::string order_id,
                         OrderSide side,
                         std::int64_t price_ticks,
                         std::int64_t quantity);

  static Event cancel(std::int64_t timestamp, std::string symbol, std::string order_id);

  static Event modify(std::int64_t timestamp,
                      std::string symbol,
                      std::string order_id,
                      std::int64_t new_price_ticks,
                      std::int64_t new_quantity);

  static Event market(std::int64_t timestamp,
                      std::string symbol,
                      std::string order_id,
                      OrderSide side,
                      std::int64_t quantity);

  [[nodiscard]] EventType type() const noexcept;
  [[nodiscard]] std::int64_t timestamp() const noexcept;
  [[nodiscard]] const std::string& symbol() const noexcept;
  [[nodiscard]] const std::string& order_id() const noexcept;
  [[nodiscard]] std::optional<OrderSide> side() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> price_ticks() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> quantity() const noexcept;

 private:
  Event(EventType type,
        std::int64_t timestamp,
        std::string symbol,
        std::string order_id,
        std::optional<OrderSide> side,
        std::optional<std::int64_t> price_ticks,
        std::optional<std::int64_t> quantity);

  EventType type_;
  std::int64_t timestamp_;
  std::string symbol_;
  std::string order_id_;
  std::optional<OrderSide> side_;
  std::optional<std::int64_t> price_ticks_;
  std::optional<std::int64_t> quantity_;
};

}  // namespace microstructure
