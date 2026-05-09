#include "microstructure/order.hpp"

#include <stdexcept>
#include <utility>

namespace microstructure {

namespace {

void validate_common(const std::string& order_id,
                     const std::string& symbol,
                     OrderType type,
                     std::int64_t price_ticks,
                     std::int64_t quantity) {
  if (order_id.empty()) {
    throw std::invalid_argument("order_id must not be empty");
  }
  if (symbol.empty()) {
    throw std::invalid_argument("symbol must not be empty");
  }
  if (quantity <= 0) {
    throw std::invalid_argument("quantity must be positive");
  }
  if (type == OrderType::Limit && price_ticks <= 0) {
    throw std::invalid_argument("limit order price_ticks must be positive");
  }
  if (type == OrderType::Market && price_ticks != 0) {
    throw std::invalid_argument("market order price_ticks must be zero");
  }
}

}  // namespace

Order::Order(std::string order_id,
             std::int64_t timestamp,
             std::string symbol,
             OrderSide side,
             OrderType type,
             std::int64_t price_ticks,
             std::int64_t quantity)
    : order_id_(std::move(order_id)),
      timestamp_(timestamp),
      symbol_(std::move(symbol)),
      side_(side),
      type_(type),
      price_ticks_(price_ticks),
      quantity_(quantity),
      remaining_quantity_(quantity),
      status_(OrderStatus::New) {
  validate_common(order_id_, symbol_, type_, price_ticks_, quantity_);
}

const std::string& Order::order_id() const noexcept { return order_id_; }

std::int64_t Order::timestamp() const noexcept { return timestamp_; }

const std::string& Order::symbol() const noexcept { return symbol_; }

OrderSide Order::side() const noexcept { return side_; }

OrderType Order::type() const noexcept { return type_; }

std::int64_t Order::price_ticks() const noexcept { return price_ticks_; }

std::int64_t Order::quantity() const noexcept { return quantity_; }

std::int64_t Order::remaining_quantity() const noexcept { return remaining_quantity_; }

OrderStatus Order::status() const noexcept { return status_; }

bool Order::is_active() const noexcept {
  return status_ == OrderStatus::New || status_ == OrderStatus::PartiallyFilled;
}

void Order::apply_fill(std::int64_t fill_quantity) {
  if (!is_active()) {
    throw std::logic_error("cannot fill inactive order");
  }
  if (fill_quantity <= 0) {
    throw std::invalid_argument("fill_quantity must be positive");
  }
  if (fill_quantity > remaining_quantity_) {
    throw std::invalid_argument("fill_quantity exceeds remaining quantity");
  }

  remaining_quantity_ -= fill_quantity;
  status_ = remaining_quantity_ == 0 ? OrderStatus::Filled : OrderStatus::PartiallyFilled;
}

void Order::cancel() {
  if (!is_active()) {
    throw std::logic_error("cannot cancel inactive order");
  }
  status_ = OrderStatus::Cancelled;
}

void Order::reject() {
  if (status_ == OrderStatus::Filled || status_ == OrderStatus::Cancelled) {
    throw std::logic_error("cannot reject terminal order");
  }
  status_ = OrderStatus::Rejected;
}

}  // namespace microstructure
