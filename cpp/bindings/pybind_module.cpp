#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "microstructure/event.hpp"
#include "microstructure/matching_engine.hpp"
#include "microstructure/order.hpp"
#include "microstructure/snapshot.hpp"
#include "microstructure/trade.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
  m.doc() = "Microstructure-Lab C++ core module";

  py::enum_<microstructure::OrderSide>(m, "OrderSide")
      .value("BUY", microstructure::OrderSide::Buy)
      .value("SELL", microstructure::OrderSide::Sell)
      .export_values();

  py::enum_<microstructure::OrderType>(m, "OrderType")
      .value("LIMIT", microstructure::OrderType::Limit)
      .value("MARKET", microstructure::OrderType::Market)
      .export_values();

  py::enum_<microstructure::OrderStatus>(m, "OrderStatus")
      .value("NEW", microstructure::OrderStatus::New)
      .value("PARTIALLY_FILLED", microstructure::OrderStatus::PartiallyFilled)
      .value("FILLED", microstructure::OrderStatus::Filled)
      .value("CANCELLED", microstructure::OrderStatus::Cancelled)
      .value("REJECTED", microstructure::OrderStatus::Rejected)
      .export_values();

  py::enum_<microstructure::EventType>(m, "EventType")
      .value("ADD", microstructure::EventType::Add)
      .value("CANCEL", microstructure::EventType::Cancel)
      .value("MODIFY", microstructure::EventType::Modify)
      .value("MARKET", microstructure::EventType::Market)
      .export_values();

  py::enum_<microstructure::EngineStatus>(m, "EngineStatus")
      .value("ACCEPTED", microstructure::EngineStatus::Accepted)
      .value("REJECTED", microstructure::EngineStatus::Rejected)
      .value("NOT_FOUND", microstructure::EngineStatus::NotFound)
      .export_values();

  py::class_<microstructure::Order>(m, "Order")
      .def(py::init<std::string,
                    std::int64_t,
                    std::string,
                    microstructure::OrderSide,
                    microstructure::OrderType,
                    std::int64_t,
                    std::int64_t>(),
           py::arg("order_id"),
           py::arg("timestamp"),
           py::arg("symbol"),
           py::arg("side"),
           py::arg("type"),
           py::arg("price_ticks"),
           py::arg("quantity"))
      .def_property_readonly("order_id", &microstructure::Order::order_id)
      .def_property_readonly("timestamp", &microstructure::Order::timestamp)
      .def_property_readonly("symbol", &microstructure::Order::symbol)
      .def_property_readonly("side", &microstructure::Order::side)
      .def_property_readonly("type", &microstructure::Order::type)
      .def_property_readonly("price_ticks", &microstructure::Order::price_ticks)
      .def_property_readonly("quantity", &microstructure::Order::quantity)
      .def_property_readonly("remaining_quantity", &microstructure::Order::remaining_quantity)
      .def_property_readonly("status", &microstructure::Order::status)
      .def("is_active", &microstructure::Order::is_active)
      .def("apply_fill", &microstructure::Order::apply_fill, py::arg("fill_quantity"))
      .def("cancel", &microstructure::Order::cancel)
      .def("reject", &microstructure::Order::reject);

  py::class_<microstructure::Trade>(m, "Trade")
      .def_property_readonly("trade_id", &microstructure::Trade::trade_id)
      .def_property_readonly("timestamp", &microstructure::Trade::timestamp)
      .def_property_readonly("symbol", &microstructure::Trade::symbol)
      .def_property_readonly("price_ticks", &microstructure::Trade::price_ticks)
      .def_property_readonly("quantity", &microstructure::Trade::quantity)
      .def_property_readonly("aggressor_side", &microstructure::Trade::aggressor_side)
      .def_property_readonly("maker_order_id", &microstructure::Trade::maker_order_id)
      .def_property_readonly("taker_order_id", &microstructure::Trade::taker_order_id);

  py::class_<microstructure::Snapshot>(m, "Snapshot")
      .def_property_readonly("timestamp", &microstructure::Snapshot::timestamp)
      .def_property_readonly("symbol", &microstructure::Snapshot::symbol)
      .def_property_readonly("best_bid_ticks", &microstructure::Snapshot::best_bid_ticks)
      .def_property_readonly("best_ask_ticks", &microstructure::Snapshot::best_ask_ticks)
      .def_property_readonly("spread_ticks", &microstructure::Snapshot::spread_ticks)
      .def_property_readonly("mid_price_ticks_x2", &microstructure::Snapshot::mid_price_ticks_x2)
      .def_property_readonly("bid_depth", &microstructure::Snapshot::bid_depth)
      .def_property_readonly("ask_depth", &microstructure::Snapshot::ask_depth);

  py::class_<microstructure::Event>(m, "Event")
      .def_static("add_limit",
                  &microstructure::Event::add_limit,
                  py::arg("timestamp"),
                  py::arg("symbol"),
                  py::arg("order_id"),
                  py::arg("side"),
                  py::arg("price_ticks"),
                  py::arg("quantity"))
      .def_static("cancel",
                  &microstructure::Event::cancel,
                  py::arg("timestamp"),
                  py::arg("symbol"),
                  py::arg("order_id"))
      .def_static("modify",
                  &microstructure::Event::modify,
                  py::arg("timestamp"),
                  py::arg("symbol"),
                  py::arg("order_id"),
                  py::arg("new_price_ticks"),
                  py::arg("new_quantity"))
      .def_static("market",
                  &microstructure::Event::market,
                  py::arg("timestamp"),
                  py::arg("symbol"),
                  py::arg("order_id"),
                  py::arg("side"),
                  py::arg("quantity"))
      .def_property_readonly("type", &microstructure::Event::type)
      .def_property_readonly("timestamp", &microstructure::Event::timestamp)
      .def_property_readonly("symbol", &microstructure::Event::symbol)
      .def_property_readonly("order_id", &microstructure::Event::order_id)
      .def_property_readonly("side", &microstructure::Event::side)
      .def_property_readonly("price_ticks", &microstructure::Event::price_ticks)
      .def_property_readonly("quantity", &microstructure::Event::quantity);

  py::class_<microstructure::EngineResult>(m, "EngineResult")
      .def_readonly("status", &microstructure::EngineResult::status)
      .def_readonly("message", &microstructure::EngineResult::message)
      .def_readonly("trades", &microstructure::EngineResult::trades);

  py::class_<microstructure::MatchingEngine>(m, "MatchingEngine")
      .def(py::init<>())
      .def("add_limit_order", &microstructure::MatchingEngine::add_limit_order, py::arg("order"))
      .def("submit_market_order",
           &microstructure::MatchingEngine::submit_market_order,
           py::arg("order"))
      .def("cancel_order",
           &microstructure::MatchingEngine::cancel_order,
           py::arg("symbol"),
           py::arg("order_id"))
      .def("modify_order",
           &microstructure::MatchingEngine::modify_order,
           py::arg("timestamp"),
           py::arg("symbol"),
           py::arg("order_id"),
           py::arg("new_price_ticks"),
           py::arg("new_quantity"))
      .def("apply_event", &microstructure::MatchingEngine::apply_event, py::arg("event"))
      .def("snapshot",
           &microstructure::MatchingEngine::snapshot,
           py::arg("timestamp"),
           py::arg("symbol"))
      .def("find_order",
           &microstructure::MatchingEngine::find_order,
           py::arg("symbol"),
           py::arg("order_id"))
      .def("trades", &microstructure::MatchingEngine::trades, py::arg("symbol"));

  m.def("engine_model_version", []() { return 4; });
}
