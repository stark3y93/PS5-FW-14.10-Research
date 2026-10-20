// Confirms that the local PC AddressSanitizer reports a simple heap violation.
#include <cstdlib>
int main() {
    auto* bytes = static_cast<volatile char*>(std::malloc(8));
    bytes[8] = 1;
    std::free(const_cast<char*>(bytes));
}
