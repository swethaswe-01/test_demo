*** Settings ***
Library    ../test_scripts/zakkpay.py
Variables  ../test_scripts/environment.py
Library    DataDriver  file=../test_data/zakkpay.xlsx  encoding=utf-8  dialect=xlsx

Test Template  Execute APIs

*** Variables ***
${env}       qa

*** Test Cases ***
${test_case_id} - ${test_desc}
    [Template]    ${test_case_id}    ${test_desc}    ${url}    ${payload}    ${expected_response}

*** Keywords ***
Execute APIs
    [Arguments]    ${test_case_id}    ${test_desc}    ${url}    ${payload}    ${expected_response}
    ${result}=    Run Api Test    ${env}    ${test_case_id}  ${url}   ${test_desc}    ${payload}    ${expected_response}
    Log           "Test Case ID: ${test_case_id}, Result: ${result}"
    Run Keyword If    '${result}' == 'FAIL'    Fail