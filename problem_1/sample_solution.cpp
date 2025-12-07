#include <iostream>
#include <vector>
#include <cstdint>
#include <algorithm>
#include <iomanip>
#include <thread>


std::vector<std::vector<double>> read_matrix() {
    size_t rows, cols;
    std::cin >> rows >> cols;

    size_t a, b, x, y, z, p;
    std::cin >> a >> b >> x >> y >> z >> p;
    std::vector<std::vector<size_t>> intermediate(rows, std::vector<size_t>(cols, b % p));
    intermediate[0][0] = a % p;
    for (size_t i = 0; i < rows; ++i) {
        for (size_t j = 0; j < cols; ++j) {
            if (i > 0 && j > 0) {
                intermediate[i][j] = (intermediate[i][j] + intermediate[i - 1][j - 1] * x) % p;
            }
            if (i > 0) {
                intermediate[i][j] = (intermediate[i][j] + intermediate[i - 1][j] * y) % p;
            }
            if (j > 0) {
                intermediate[i][j] = (intermediate[i][j] + intermediate[i][j - 1] * z) % p;
            }
        }
    }
    size_t max_value = 0;
    for (size_t i = 0; i < rows; ++i) {
        for (size_t j = 0; j < cols; ++j) {
            max_value = std::max(max_value, intermediate[i][j]);
        }
    }

    std::vector<std::vector<double>> result(rows, std::vector<double>(cols));
    for (size_t i = 0; i < rows; ++i) {
        for (size_t j = 0; j < cols; ++j) {
            result[i][j] = static_cast<double>(intermediate[i][j]) / static_cast<double>(max_value);
        }
    }

    return result;
}


std::vector<std::vector<double>> multiply_parallel(
    const std::vector<std::vector<double>>& left,
    const std::vector<std::vector<double>>& right
) {
    const size_t left_rows  = left.size();
    const size_t left_cols  = left[0].size();
    const size_t right_cols = right[0].size();

    std::vector<std::vector<double>> result(left_rows, std::vector<double>(right_cols, 0.0));


    unsigned int threads_count = std::thread::hardware_concurrency();
    if (threads_count == 0) {
        threads_count = 4;
    }
    if (threads_count > left_rows) {
        threads_count = static_cast<unsigned int>(left_rows);
    }

    std::vector<std::thread> threads;
    threads.reserve(threads_count);

    auto worker = [&](size_t row_begin, size_t row_end) {
        for (size_t i = row_begin; i < row_end; ++i) {
            for (size_t j = 0; j < right_cols; ++j) {
                double sum = 0.0;
                for (size_t k = 0; k < left_cols; ++k) {
                    sum += left[i][k] * right[k][j];
                }
                result[i][j] = sum;
            }
        }
    };

    size_t rows_per_thread = left_rows / threads_count;
    size_t remainder = left_rows % threads_count;
    size_t current_row = 0;

    for (unsigned int t = 0; t < threads_count; ++t) {
        size_t start = current_row;
        size_t count = rows_per_thread + (t < remainder ? 1 : 0);
        size_t end = start + count;
        current_row = end;

        threads.emplace_back(worker, start, end);
    }

    for (auto& th : threads) {
        th.join();
    }

    return result;
}

int main() {
    auto left = read_matrix();
    auto right = read_matrix();

    if (left.empty() || right.empty() || left[0].size() != right.size()) {
        std::cerr << "Wrong matrices";
        return 1;
    }

    auto left_rows  = left.size();
    auto right_cols = right[0].size();

    auto result = multiply_parallel(left, right);

    std::cout << left_rows << ' ' << right_cols << "\n";
    for (size_t i = 0; i < left_rows; ++i) {
        for (size_t j = 0; j < right_cols; ++j) {
            std::cout << std::setprecision(12) << result[i][j] << ' ';
        }
        std::cout << "\n";
    }

    return 0;
}
