#include "microstructure/event.hpp"

#include <stdexcept>
#include <utility>

namespace microstructure {

namespace {

void validate_identity(const std::string& symbol, const std::string& order_id) {
  if (symbol.empty()) {
    throw std::invalid_argument("symbol must not be empty");
  }
  if (order_id.empty()) {
    throw std::invalid_argument("order_id must not be empty");
  }
}

void validate_quantity(std::int64_t quantity) {
  if (quantity <= 0) {
    throw std::invalid_argument("quantity must be positive");
  }
}

void validate_price(std::int64_t price_ticks) {
  if (price_ticks <= 0) {
    throw std::invalid_argument("price_ticks must be positive");
  }
}

}  // namespace

Event Event::add_limit(std::int64_t timestamp,
                       std::string symbol,
                       std::string order_id,
                       OrderSide side,
                       std::int64_t price_ticks,
                       std::int64_t quantity) {
  validate_identity(symbol, order_id);
  validate_price(price_ticks);
  validate_quantity(quantity);
  return Event(EventType::Add,
               timestamp,
               std::move(symbol),
               std::move(order_id),
               side,
               price_ticks,
               quantity);
}

Event Event::cancel(std::int64_t timestamp, std::string symbol, std::string order_id) {
  validate_identity(symbol, order_id);
  return Event(EventType::Cancel,
               timestamp,
               std::move(symbol),
               std::move(order_id),
               std::nullopt,
               std::nullopt,
               std::nullopt);
}

Event Event::modify(std::int64_t timestamp,
                    std::string symbol,
                    std::string order_id,
                    std::int64_t new_price_ticks,
                    std::int64_t new_quantity) {
  validate_identity(symbol, order_id);
  validate_price(new_price_ticks);
  validate_quantity(new_quantity);
  return Event(EventType::Modify,
               timestamp,
               std::move(symbol),
               std::move(order_id),
               std::nullopt,
               new_price_ticks,
               new_quantity);
}

Event Event::market(std::int64_t timestamp,
                    std::string symbol,
                    std::string order_id,
                    OrderSide side,
                    std::int64_t quantity) {
  validate_identity(symbol, order_id);
  validate_quantity(quantity);
  return Event(EventType::Market,
               timestamp,
               std::move(symbol),
               std::move(order_id),
               side,
               std::nullopt,
               quantity);
}

Event::Event(EventType type,
             std::int64_t timestamp,
             std::string symbol,
             std::string order_id,
             std::optional<OrderSide> side,
             std::optional<std::int64_t> price_ticks,
             std::optional<std::int64_t> quantity)
    : type_(type),
      timestamp_(timestamp),
      symbol_(std::move(symbol)),
      order_id_(std::move(order_id)),
      side_(side),
      price_ticks_(price_ticks),
      quantity_(quantity) {}

EventType Event::type() const noexcept { return type_; }

std::int64_t Event::timestamp() const noexcept { return timestamp_; }

const std::string& Event::symbol() const noexcept { return symbol_; }

const std::string& Event::order_id() const noexcept { return order_id_; }

std::optional<OrderSide> Event::side() const noexcept { return side_; }

std::optional<std::int64_t> Event::price_ticks() const noexcept { return price_ticks_; }

std::optional<std::int64_t> Event::quantity() const noexcept { return quantity_; }

}  // namespace microstructure
