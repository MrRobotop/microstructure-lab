set(MICROSTRUCTURE_CORE_SOURCES
  src/book.cpp
  src/event.cpp
  src/matching_engine.cpp
  src/order.cpp
  src/snapshot.cpp
  src/trade.cpp
)

add_library(microstructure_core STATIC ${MICROSTRUCTURE_CORE_SOURCES})
set_target_properties(microstructure_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  microstructure_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_compile_features(microstructure_core PUBLIC cxx_std_17)

if(SKBUILD)
  find_package(pybind11 CONFIG REQUIRED)
  pybind11_add_module(_core bindings/pybind_module.cpp)
  target_link_libraries(_core PRIVATE microstructure_core)
  install(TARGETS _core LIBRARY DESTINATION microstructure_lab)
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(test_matching_engine tests/test_matching_engine.cpp)
  target_link_libraries(test_matching_engine PRIVATE microstructure_core)
  add_test(NAME test_matching_engine COMMAND test_matching_engine)
endif()
