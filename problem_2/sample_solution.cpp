#include <iostream>
#include <vector>
#include <cstdint>
#include <algorithm>
#include <iomanip>
#include <thread>

std::vector<size_t> read_array() {
    size_t length, a, b, p;
    std::cin >> length >> a >> b >> p;
    std::vector<size_t> result(length);
    if (length == 0) {
        return result;
    }
    result[0] = a % p;
    for (size_t i = 1; i < result.size(); ++i) {
        result[i] = (result[i - 1] * a + b) % p;
    }
    return result;
}


void parallel_sort(std::vector<size_t>& arr) {
    const size_t n = arr.size();
    if (n <= 1) {
        return;
    }

    unsigned int threads_count = std::thread::hardware_concurrency();
    if (threads_count == 0) {
        threads_count = 4;
    }
    if (threads_count > n) {
        threads_count = static_cast<unsigned int>(n);
    }

    std::vector<std::thread> threads;
    threads.reserve(threads_count);

    std::vector<size_t> starts(threads_count + 1);
    size_t base_block = n / threads_count;
    size_t remainder  = n % threads_count;

    size_t current = 0;
    for (unsigned int t = 0; t < threads_count; ++t) {
        starts[t] = current;
        size_t block_size = base_block + (t < remainder ? 1 : 0);
        current += block_size;
    }
    starts[threads_count] = n;

    for (unsigned int t = 0; t < threads_count; ++t) {
        size_t begin = starts[t];
        size_t end   = starts[t + 1];
        threads.emplace_back([&, begin, end]() {
            std::sort(arr.begin() + static_cast<std::ptrdiff_t>(begin),
                      arr.begin() + static_cast<std::ptrdiff_t>(end));
        });
    }

    for (auto& th : threads) {
        th.join();
    }

    for (unsigned int step = 1; step < threads_count; step *= 2) {
        for (unsigned int i = 0; i + step < threads_count; i += 2 * step) {
            size_t left_begin  = starts[i];
            size_t left_mid    = starts[i + step];
            size_t left_end    = starts[std::min<unsigned int>(i + 2 * step, threads_count)];

            std::inplace_merge(
                arr.begin() + static_cast<std::ptrdiff_t>(left_begin),
                arr.begin() + static_cast<std::ptrdiff_t>(left_mid),
                arr.begin() + static_cast<std::ptrdiff_t>(left_end)
            );
        }
    }
}

int main() {
    auto array = read_array();

    parallel_sort(array);

    size_t k;
    std::cin >> k;

    for (size_t i = k - 1; i < array.size(); i += k) {
        std::cout << array[i] << ' ';
    }
    std::cout << "\n";

    return 0;
}
