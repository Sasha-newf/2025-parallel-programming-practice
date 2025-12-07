#include <iostream>
#include <vector>
#include <cstdint>
#include <algorithm>
#include <thread>
#include <atomic>
#include <numeric>


std::istream& operator>>(std::istream& in, __int128& value) {
    std::string s;
    in >> s;
    value = 0;
    bool negative = false;
    std::size_t i = 0;
    if (!s.empty() && s[0] == '-') {
        negative = true;
        i = 1;
    }
    for (; i < s.size(); ++i) {
        value = value * 10 + (s[i] - '0');
    }
    if (negative) value = -value;
    return in;
}

std::ostream& operator<<(std::ostream& out, __int128 value) {
    if (value == 0) {
        out << '0';
        return out;
    }
    std::string s;
    bool negative = false;
    if (value < 0) {
        negative = true;
        value = -value;
    }
    while (value > 0) {
        s += char('0' + int(value % 10));
        value /= 10;
    }
    if (negative) s += '-';
    std::reverse(s.begin(), s.end());
    out << s;
    return out;
}


using u64  = unsigned long long;
using u128 = __uint128_t;

u64 mul_mod(u64 a, u64 b, u64 mod) {
    return (u128)a * b % mod;
}

u64 pow_mod(u64 a, u64 d, u64 mod) {
    u64 res = 1;
    while (d) {
        if (d & 1) {
            res = mul_mod(res, a, mod);
        }
        a = mul_mod(a, a, mod);
        d >>= 1;
    }
    return res;
}

bool miller_test(u64 n, u64 a, u64 d, int s) {
    if (a % n == 0) return true;
    u64 x = pow_mod(a, d, n);
    if (x == 1 || x == n - 1) return true;
    for (int r = 1; r < s; ++r) {
        x = mul_mod(x, x, n);
        if (x == n - 1) return true;
    }
    return false;
}

bool is_prime(u64 n) {
    if (n < 2) return false;
    static const u64 small_primes[] =
        {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37};
    for (u64 p : small_primes) {
        if (n == p) return true;
        if (n % p == 0) return n == p;
    }

    u64 d = n - 1;
    int s = 0;
    while ((d & 1) == 0) {
        d >>= 1;
        ++s;
    }

    static const u64 test_bases[] =
        {2ull, 325ull, 9375ull, 28178ull,
         450775ull, 9780504ull, 1795265022ull};

    for (u64 a : test_bases) {
        if (a == 0 || a >= n) continue;
        if (!miller_test(n, a, d, s)) return false;
    }
    return true;
}

u64 f_pollard(u64 x, u64 c, u64 mod) {
    return (mul_mod(x, x, mod) + c) % mod;
}

u64 pollard_rho(u64 n, u64 x0, u64 c) {
    if (n % 2 == 0) return 2;
    u64 x = x0 % n;
    if (x == 0) x = 2;
    u64 y = x;
    u64 d = 1;

    while (d == 1) {
        x = f_pollard(x, c, n);
        y = f_pollard(f_pollard(y, c, n), c, n);
        u64 diff = x > y ? x - y : y - x;
        d = std::gcd(diff, n);
        if (d == n) return 0;
    }
    return d;
}

u64 find_factor_parallel(u64 n) {
    if (n % 2 == 0) return 2;

    unsigned int threads_count = std::thread::hardware_concurrency();
    if (threads_count == 0) threads_count = 4;
    if (threads_count > 8) threads_count = 8;

    std::atomic<u64> factor(0);
    std::vector<std::thread> threads;
    threads.reserve(threads_count);

    for (unsigned int t = 0; t < threads_count; ++t) {
        threads.emplace_back([&, t]() {
            u64 x0 = 2 + 2 * t;
            u64 c  = 1 + 2 * t;

            while (factor.load(std::memory_order_relaxed) == 0) {
                u64 d = pollard_rho(n, x0, c);
                if (d > 1 && d < n) {
                    u64 expected = 0;
                    if (factor.compare_exchange_strong(
                            expected, d, std::memory_order_relaxed)) {
                        break;
                    }
                }
                x0 += 2 * threads_count;
                c  += 2 * threads_count;
            }
        });
    }

    for (auto &th : threads) {
        th.join();
    }

    u64 d = factor.load(std::memory_order_relaxed);
    if (d == 0) {
        d = n;
    }
    return d;
}

void factor_rec(u64 n, std::vector<u64> &factors) {
    if (n == 1) return;
    if (is_prime(n)) {
        factors.push_back(n);
        return;
    }
    u64 d = find_factor_parallel(n);
    if (d == n) {
        factors.push_back(n);
        return;
    }
    factor_rec(d, factors);
    factor_rec(n / d, factors);
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    __int128 n128;
    if (!(std::cin >> n128)) {
        return 0;
    }

    if (n128 <= 1) {
        return 0;
    }

    u64 n = static_cast<u64>(n128);

    std::vector<u64> factors;
    factor_rec(n, factors);

    std::sort(factors.begin(), factors.end());

    for (std::size_t i = 0; i < factors.size(); ++i) {
        if (i > 0) {
            std::cout << ' ';
        }
        __int128 f128 = static_cast<__int128>(factors[i]);
        std::cout << f128;
    }
    std::cout << '\n';

    return 0;
}
