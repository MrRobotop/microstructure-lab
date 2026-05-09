#include "microstructure/snapshot.hpp"

#include <stdexcept>
#include <utility>

namespace microstructure {

Snapshot::Snapshot(std::int64_t timestamp,
                   std::string symbol,
                   std::optional<std::int64_t> best_bid_ticks,
                   std::optional<std::int64_t> best_ask_ticks,
                   std::int64_t bid_depth,
                   std::int64_t ask_depth)
    : timestamp_(timestamp),
      symbol_(std::move(symbol)),
      best_bid_ticks_(best_bid_ticks),
      best_ask_ticks_(best_ask_ticks),
      bid_depth_(bid_depth),
      ask_depth_(ask_depth) {
  if (symbol_.empty()) {
    throw std::invalid_argument("symbol must not be empty");
  }
  if (best_bid_ticks_.has_value() && *best_bid_ticks_ <= 0) {
    throw std::invalid_argument("best_bid_ticks must be positive when present");
  }
  if (best_ask_ticks_.has_value() && *best_ask_ticks_ <= 0) {
    throw std::invalid_argument("best_ask_ticks must be positive when present");
  }
  if (best_bid_ticks_.has_value() && best_ask_ticks_.has_value() &&
      *best_bid_ticks_ >= *best_ask_ticks_) {
    throw std::invalid_argument("best_bid_ticks must be less than best_ask_ticks");
  }
  if (bid_depth_ < 0 || ask_depth_ < 0) {
    throw std::invalid_argument("depth values must be nonnegative");
  }
}

std::int64_t Snapshot::timestamp() const noexcept { return timestamp_; }

const std::string& Snapshot::symbol() const noexcept { return symbol_; }

std::optional<std::int64_t> Snapshot::best_bid_ticks() const noexcept {
  return best_bid_ticks_;
}

std::optional<std::int64_t> Snapshot::best_ask_ticks() const noexcept {
  return best_ask_ticks_;
}

std::optional<std::int64_t> Snapshot::spread_ticks() const noexcept {
  if (!best_bid_ticks_.has_value() || !best_ask_ticks_.has_value()) {
    return std::nullopt;
  }
  return *best_ask_ticks_ - *best_bid_ticks_;
}

std::optional<std::int64_t> Snapshot::mid_price_ticks_x2() const noexcept {
  if (!best_bid_ticks_.has_value() || !best_ask_ticks_.has_value()) {
    return std::nullopt;
  }
  return *best_bid_ticks_ + *best_ask_ticks_;
}

std::int64_t Snapshot::bid_depth() const noexcept { return bid_depth_; }

std::int64_t Snapshot::ask_depth() const noexcept { return ask_depth_; }

}  // namespace microstructure
