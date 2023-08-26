# Copyright (c) 2023 Bela Schaum, X-Ryl669, Denis Mikhailov.
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)


# Initial implementation by Bela Schaum, https://github.com/schaumb
# The way to make it union and UB free by X-Ryl669, https://github.com/X-Ryl669
#

############################################################################################################################

import sys
import string
import random

# a bigger value might lead to compiler out of heap space error on MSVC
STRUCT_COUNT = 50
MAX_FIELD_COUNT = 50

MAIN_TEMPLATE = """#include <boost/pfr/core_name.hpp>
#include <array>
#include <type_traits>

#include <boost/core/lightweight_test.hpp>

namespace testing {

template <class... Types>
auto make_stdarray(const Types&... t) {
    return std::array<std::common_type_t<Types...>, sizeof...(Types)>{t...};
}

%STRUCTS_LIST%

%TEST_GET_NAME_DEFINITIONS_LIST%

%TEST_GET_NAMES_AS_ARRAY_DEFINITIONS_LIST%


} // namespace testing

int main() {
    %TEST_GET_NAME_CALLS_LIST%
    %TEST_GET_NAMES_AS_ARRAY_CALLS_LIST%

    return boost::report_errors();
}
"""

STRUCT_TEMPLATE = """struct Aggregate%STRUCT_ID% {
    %FIELD_DEFINITIONS_LIST%
};
"""

STRUCT_FIELD_DEFINITION_TEMPLATE = """int %FIELD_NAME%;
"""

TEST_GET_NAME_TEMPLATE = """void test_get_name_%TEST_ID%() {
    %CHECKERS_LIST%
}
"""

TEST_GET_NAME_CHECKER_TEMPLATE = """BOOST_TEST_EQ( ((boost::pfr::get_name<%FIELD_ID%, Aggregate%STRUCT_ID%>())), "%FIELD_NAME%");
"""

TEST_GET_NAMES_AS_ARRAY_TEMPLATE = """void test_names_as_array_%TEST_ID%() {
    const auto expected = make_stdarray(
        %FIELD_NAMES_LIST%
    );
    const auto value = boost::pfr::names_as_array<Aggregate%STRUCT_ID%>();
    BOOST_TEST_EQ(expected.size(), value.size());
    for (std::size_t i=0;i<expected.size();++i) {
        BOOST_TEST_EQ(value[i], expected[i]);
    }
}
"""

FIELD_NAME_TEMPLATE = """std::string_view{"%FIELD_NAME%"}
"""

TEST_GET_NAME_CALL_TEMPLATE = """testing::test_get_name_%TEST_ID%();
"""

TEST_GET_NAMES_AS_ARRAY_CALL_TEMPLATE = """testing::test_names_as_array_%TEST_ID%();
"""

############################################################################################################################

field_names = {
    "alignas": True,
    "alignof": True,
    "and": True,
    "and_eq": True,
    "asm": True,
    "atomic_cancel": True,
    "atomic_commit": True,
    "atomic_noexcept": True,
    "auto": True,
    "bitand": True,
    "bitor": True,
    "bool": True,
    "break": True,
    "case": True,
    "catch": True,
    "char": True,
    "char8_t": True,
    "char16_t": True,
    "char32_t": True,
    "class": True,
    "compl": True,
    "concept": True,
    "const": True,
    "consteval": True,
    "constexpr": True,
    "constinit": True,
    "const_cast": True,
    "continue": True,
    "co_await": True,
    "co_return": True,
    "co_yield": True,
    "decltype": True,
    "default": True,
    "delete": True,
    "do": True,
    "double": True,
    "dynamic_cast": True,
    "else": True,
    "enum": True,
    "explicit": True,
    "export": True,
    "extern": True,
    "false": True,
    "float": True,
    "for": True,
    "friend": True,
    "goto": True,
    "if": True,
    "inline": True,
    "int": True,
    "long": True,
    "mutable": True,
    "namespace": True,
    "new": True,
    "noexcept": True,
    "not": True,
    "not_eq": True,
    "nullptr": True,
    "operator": True,
    "or": True,
    "or_eq": True,
    "private": True,
    "protected": True,
    "public": True,
    "reflexpr": True,
    "register": True,
    "reinterpret_cast": True,
    "requires": True,
    "return": True,
    "short": True,
    "signed": True,
    "sizeof": True,
    "static": True,
    "static_assert": True,
    "static_cast": True,
    "struct": True,
    "switch": True,
    "synchronized": True,
    "template": True,
    "this": True,
    "thread_local": True,
    "throw": True,
    "true": True,
    "try": True,
    "typedef": True,
    "typeid": True,
    "typename": True,
    "union": True,
    "unsigned": True,
    "using": True,
    "virtual": True,
    "void": True,
    "volatile": True,
    "wchar_t": True,
    "while": True,
    "xor": True,
    "xor_eq": True
}
field_names_by_id = {}

def generate_new_field_name():
    result = ''
    name_len = random.randint(1,100)
    result += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    for i in range(name_len-1):
        result += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")
    return result

def generate_field_name(struct_id, field_id):
    key = (struct_id, field_id)
    if not key in field_names_by_id:
        new_name = generate_new_field_name()
        while new_name in field_names:
            new_name = generate_new_field_name()
        field_names[new_name] = True
        field_names_by_id[key] = new_name
    return field_names_by_id[key]

def generate_struct(struct_id):
    field_definitions = ''
    fields_count = struct_id
    for i in range(fields_count):
        field_definitions += STRUCT_FIELD_DEFINITION_TEMPLATE.replace('%FIELD_NAME%', generate_field_name(struct_id, i))
    return STRUCT_TEMPLATE.replace('%FIELD_DEFINITIONS_LIST%', field_definitions).replace('%STRUCT_ID%', str(struct_id))

def generate_structs_list():
    result = ''
    for i in range(STRUCT_COUNT):
        result += generate_struct(i+1)
    return result

def generate_test_get_name_definition(struct_id):
    checkers_list = ''
    fields_count = struct_id
    for i in range(fields_count):
        checkers_list += TEST_GET_NAME_CHECKER_TEMPLATE.replace('%FIELD_ID%', str(i)).replace('%STRUCT_ID%', str(struct_id)).replace('%FIELD_NAME%', generate_field_name(struct_id, i))
    return TEST_GET_NAME_TEMPLATE.replace('%TEST_ID%', str(struct_id)).replace('%CHECKERS_LIST%', checkers_list)

def generate_test_get_name_definitions_list():
    result = ''
    for i in range(STRUCT_COUNT):
        result += generate_test_get_name_definition(i+1)
    return result

def generate_test_names_as_array_definition(struct_id):
    field_names_list = FIELD_NAME_TEMPLATE.replace('%FIELD_NAME%', generate_field_name(struct_id, 0))
    fields_count = struct_id
    for i in range(1, fields_count):
        field_names_list += ', ' + FIELD_NAME_TEMPLATE.replace('%FIELD_NAME%', generate_field_name(struct_id, i))
    return TEST_GET_NAMES_AS_ARRAY_TEMPLATE.replace('%TEST_ID%', str(struct_id)).replace('%FIELD_NAMES_LIST%', field_names_list).replace('%STRUCT_ID%', str(struct_id))

def generate_test_names_as_array_definitions_list():
    result = ''
    for i in range(STRUCT_COUNT):
        result += generate_test_names_as_array_definition(i+1)
    return result

def generate_test_get_name_calls_list():
    result = ''
    for i in range(STRUCT_COUNT):
        result += TEST_GET_NAME_CALL_TEMPLATE.replace('%TEST_ID%', str(i+1))
    return result

def generate_test_names_as_array_calls_list():
    result = ''
    for i in range(STRUCT_COUNT):
        result += TEST_GET_NAMES_AS_ARRAY_CALL_TEMPLATE.replace('%TEST_ID%', str(i+1))
    return result

print(MAIN_TEMPLATE.replace('%STRUCTS_LIST%', generate_structs_list()).replace('%TEST_GET_NAME_DEFINITIONS_LIST%', generate_test_get_name_definitions_list()).replace('%TEST_GET_NAMES_AS_ARRAY_DEFINITIONS_LIST%', generate_test_names_as_array_definitions_list()).replace('%TEST_GET_NAME_CALLS_LIST%', generate_test_get_name_calls_list()).replace('%TEST_GET_NAMES_AS_ARRAY_CALLS_LIST%', generate_test_names_as_array_calls_list()))

