#pragma once

#include <cstdint>
#include <string>

namespace microstructure {

enum class OrderSide {
  Buy,
  Sell,
};

enum class OrderType {
  Limit,
  Market,
};

enum class OrderStatus {
  New,
  PartiallyFilled,
  Filled,
  Cancelled,
  Rejected,
};

class Order {
 public:
  Order(std::string order_id,
        std::int64_t timestamp,
        std::string symbol,
        OrderSide side,
        OrderType type,
        std::int64_t price_ticks,
        std::int64_t quantity);

  [[nodiscard]] const std::string& order_id() const noexcept;
  [[nodiscard]] std::int64_t timestamp() const noexcept;
  [[nodiscard]] const std::string& symbol() const noexcept;
  [[nodiscard]] OrderSide side() const noexcept;
  [[nodiscard]] OrderType type() const noexcept;
  [[nodiscard]] std::int64_t price_ticks() const noexcept;
  [[nodiscard]] std::int64_t quantity() const noexcept;
  [[nodiscard]] std::int64_t remaining_quantity() const noexcept;
  [[nodiscard]] OrderStatus status() const noexcept;
  [[nodiscard]] bool is_active() const noexcept;

  void apply_fill(std::int64_t fill_quantity);
  void cancel();
  void reject();

 private:
  std::string order_id_;
  std::int64_t timestamp_;
  std::string symbol_;
  OrderSide side_;
  OrderType type_;
  std::int64_t price_ticks_;
  std::int64_t quantity_;
  std::int64_t remaining_quantity_;
  OrderStatus status_;
};

}  // namespace microstructure
