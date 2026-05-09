#pragma once

#include <cstdint>
#include <string>

#include "microstructure/order.hpp"

namespace microstructure {

class Trade {
 public:
  Trade(std::string trade_id,
        std::int64_t timestamp,
        std::string symbol,
        std::int64_t price_ticks,
        std::int64_t quantity,
        OrderSide aggressor_side,
        std::string maker_order_id,
        std::string taker_order_id);

  [[nodiscard]] const std::string& trade_id() const noexcept;
  [[nodiscard]] std::int64_t timestamp() const noexcept;
  [[nodiscard]] const std::string& symbol() const noexcept;
  [[nodiscard]] std::int64_t price_ticks() const noexcept;
  [[nodiscard]] std::int64_t quantity() const noexcept;
  [[nodiscard]] OrderSide aggressor_side() const noexcept;
  [[nodiscard]] const std::string& maker_order_id() const noexcept;
  [[nodiscard]] const std::string& taker_order_id() const noexcept;

 private:
  std::string trade_id_;
  std::int64_t timestamp_;
  std::string symbol_;
  std::int64_t price_ticks_;
  std::int64_t quantity_;
  OrderSide aggressor_side_;
  std::string maker_order_id_;
  std::string taker_order_id_;
};

}  // namespace microstructure
