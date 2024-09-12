def generate_python_template():
    return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def main():
    pass

if __name__ == "__main__":
    main()
"""

def generate_cpp_template():
    return """#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
"""