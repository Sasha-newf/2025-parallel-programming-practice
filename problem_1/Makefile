BUILD_DIR = build
TARGET = $(BUILD_DIR)/solution
CXX = g++
CXXFLAGS = -O3 -std=c++20 -pthread
SRC = $(wildcard *.cpp)

.PHONY: prepare run clean

prepare: $(TARGET)

$(TARGET): $(SRC)
	-@mkdir $(BUILD_DIR)
	@$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

run:
	@$(TARGET)

clean:
	-@rm -rf $(BUILD_DIR)
