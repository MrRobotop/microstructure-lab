#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace microstructure {

class Snapshot {
 public:
  Snapshot(std::int64_t timestamp,
           std::string symbol,
           std::optional<std::int64_t> best_bid_ticks,
           std::optional<std::int64_t> best_ask_ticks,
           std::int64_t bid_depth,
           std::int64_t ask_depth);

  [[nodiscard]] std::int64_t timestamp() const noexcept;
  [[nodiscard]] const std::string& symbol() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> best_bid_ticks() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> best_ask_ticks() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> spread_ticks() const noexcept;
  [[nodiscard]] std::optional<std::int64_t> mid_price_ticks_x2() const noexcept;
  [[nodiscard]] std::int64_t bid_depth() const noexcept;
  [[nodiscard]] std::int64_t ask_depth() const noexcept;

 private:
  std::int64_t timestamp_;
  std::string symbol_;
  std::optional<std::int64_t> best_bid_ticks_;
  std::optional<std::int64_t> best_ask_ticks_;
  std::int64_t bid_depth_;
  std::int64_t ask_depth_;
};

}  // namespace microstructure
