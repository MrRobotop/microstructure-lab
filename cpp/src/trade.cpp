#include "microstructure/trade.hpp"

#include <stdexcept>
#include <utility>

namespace microstructure {

Trade::Trade(std::string trade_id,
             std::int64_t timestamp,
             std::string symbol,
             std::int64_t price_ticks,
             std::int64_t quantity,
             OrderSide aggressor_side,
             std::string maker_order_id,
             std::string taker_order_id)
    : trade_id_(std::move(trade_id)),
      timestamp_(timestamp),
      symbol_(std::move(symbol)),
      price_ticks_(price_ticks),
      quantity_(quantity),
      aggressor_side_(aggressor_side),
      maker_order_id_(std::move(maker_order_id)),
      taker_order_id_(std::move(taker_order_id)) {
  if (trade_id_.empty()) {
    throw std::invalid_argument("trade_id must not be empty");
  }
  if (symbol_.empty()) {
    throw std::invalid_argument("symbol must not be empty");
  }
  if (price_ticks_ <= 0) {
    throw std::invalid_argument("trade price_ticks must be positive");
  }
  if (quantity_ <= 0) {
    throw std::invalid_argument("trade quantity must be positive");
  }
  if (maker_order_id_.empty()) {
    throw std::invalid_argument("maker_order_id must not be empty");
  }
  if (taker_order_id_.empty()) {
    throw std::invalid_argument("taker_order_id must not be empty");
  }
}

const std::string& Trade::trade_id() const noexcept { return trade_id_; }

std::int64_t Trade::timestamp() const noexcept { return timestamp_; }

const std::string& Trade::symbol() const noexcept { return symbol_; }

std::int64_t Trade::price_ticks() const noexcept { return price_ticks_; }

std::int64_t Trade::quantity() const noexcept { return quantity_; }

OrderSide Trade::aggressor_side() const noexcept { return aggressor_side_; }

const std::string& Trade::maker_order_id() const noexcept { return maker_order_id_; }

const std::string& Trade::taker_order_id() const noexcept { return taker_order_id_; }

}  // namespace microstructure
