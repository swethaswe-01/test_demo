import json
import requests
import time
from robot.api.deco import keyword
from environment import get_global_variables

def connect_to_db(env):
    params = get_global_variables(env)
    try:
        if "DB_User" in params and "DB_Password" in params:
            db_host = params["DB_Host"]
            db_port = params["DB_Port"]
            db_user = params["DB_User"]
            db_password = params["DB_Password"]
            db_name = params["DB_Name"]

            jdbc_url = f"jdbc:clickhouse://{db_host}:{db_port}/{db_name}"
            print(f"Connected to ClickHouse '{env}' using JDBC URL: {jdbc_url}")
            return {
                "jdbc_url": jdbc_url,
                "username": db_user,
                "password": db_password
            }

        else:
            db_host = params["DB_Host"]
            db_port = params["DB_Port"]

            url = f"http://{db_host}:{db_port}"
            print(f"Connected to ClickHouse ({env.capitalize()}) at {url}")
            return url

    except Exception as e:
        print(f"Error connecting to database for {env.upper()} environment: {e}")
        return None

def send_api_request(env, payload):
    params = get_global_variables(env)
    url = params["URL"]
    print("URL :", url)
    
    headers = {
        "Content-Type": "application/json",
        "Authentication": params["Authentication"]
    }
    
    print("Headers:")
    print(json.dumps(headers, indent=4))  
    
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    print(f"Sender ID for environment '{env}': {params.get('Sender_ID')}")
    
    if params["Sender_ID"]:
        if "message" in payload and "sender" in payload["message"] and isinstance(payload["message"]["sender"], dict):
            payload["message"]["sender"]["from"] = params["Sender_ID"]  
        elif "message" in payload:
            payload["message"]["sender"] = {"from": params["Sender_ID"]}  
    
    if "sender" in payload:
        del payload["sender"]
    
    print("Payload:")
    print(json.dumps(payload, indent=4))
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print("\n--- Response Received ---")
        print(f"Status Code: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=4)) 
        except ValueError:
            print(response.text) 
        print("-------------------------\n")
        
        if response.status_code == 200:
            return response.json(), 'PASS'
        else:
            return None, 'FAIL'
    except Exception as e:
        print(f"Error sending API request: {e}")
        return None, 'FAIL'
    
def execute_query_using_requests(url, query):
    try:
        response = requests.post(url, data=query)

        if response.status_code == 200:
            result = response.text.strip()
            return result
        else:
            print(f"Failed to execute query. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    
def check_message_id_in_db(env, message_id, disable_flags):
    db_connection = connect_to_db(env)

    queries = {
        "RCM_MT_HANDOVER_STATS": f"SELECT mid FROM rcm_billing.RCM_MT_HANDOVER_STATS WHERE mid = '{message_id}'",
        "RCM_MT_SUB_STATS": f"SELECT message_id FROM rcm_billing.RCM_MT_SUB_STATS WHERE message_id = '{message_id}'",
        "RCM_MT_DN_STATS": f"SELECT message_id FROM rcm_billing.RCM_MT_DN_STATS WHERE message_id = '{message_id}'"
    }

    def execute_query(query_key, connection, db_type):
        query = queries[query_key]
        print(f"Executing Query: {query}")
        if db_type == "JDBC":
            return False  
        elif db_type == "HTTP":
            result = execute_query_using_requests(connection, query)
            # print(f"Query Result: {result}")
            return bool(result)

    try:
        if isinstance(db_connection, dict): 
            db_type = "JDBC"
        elif isinstance(db_connection, str):  
            db_type = "HTTP"
        else:
            print("Invalid database connection type.")
            return False

        results = []

        for flag, is_enabled in disable_flags.items():
            if is_enabled and flag in queries:
                result = execute_query(flag, db_connection, db_type)
                results.append(result)
        return any(results)
    except Exception as e:
        print(f"Error connecting to database for {env.upper()} environment: {e}")
        return False
    
def fetch_message_id_from_response(response):
    try:
        message_id = response.get('mid', None)
        if message_id:
            return message_id
        else:
            print("messageId not found in the response.")
            return None
    except Exception as e:
        print(f"Error while extracting messageId: {e}")
        return None

def retry_check_message_id(env, message_id, disable_flags, max_retries=5, delay=10):
    attempt = 0
    print(f"--- Database Validation ---\nMessage ID: {message_id}\nWaiting for updates in the database...\n")

    while attempt < max_retries:
        print(f"Retry {attempt + 1}:")

        message_id_status = check_message_id_in_db(env, message_id, disable_flags)

        if message_id_status:  
            print(f"- Message ID {message_id} found in the database.\n")
            return True
        else:
            print(f"- Message ID {message_id} not found.\nRetrying after {delay} seconds...\n")
            time.sleep(delay)
            attempt += 1

    print(f"Result:\nMessage ID {message_id} not found in the database after {max_retries} retries.\nTest Case Result: FAIL\n")
    return False

def compare_json(actual, expected):
    actual_response = {
        "statusCode": actual.get("statusCode"),
        "statusDesc": actual.get("statusDesc"),
    }
    expected_response = {
        "statusCode": expected.get("statusCode"),
        "statusDesc": expected.get("statusDesc"),
    }
    
    return actual_response == expected_response

@keyword
def run_api_test(env, test_case_id, test_desc, url, payload, expected_response):
    print("\n---Test Case ---")
    print(f"Environment: {env}")
    print(f"Test Case ID: {test_case_id}")
    print("--------------------------\n")
    
    api_response, test_result = send_api_request(env, payload)
    
    print("\n--- Test Results ---")
    print(f"Actual Response: {json.dumps(api_response, indent=4) if api_response else 'No Response'}")
    print(f"Expected Response: {expected_response}")
    print("---------------------\n")

    if api_response:
        if api_response.get("statusCode") == "200":
            if 'mid' in api_response:
                message_id = api_response.get('mid', None)
                print(f"Message ID: {message_id if message_id else 'Not Found'}")
                
                if message_id:
                    print("\n--- Database Validation ---")
                    print(f"Waiting for updates in the database for messageId: {message_id}...")
                    
                    disable_flags = {
                        "RCM_MT_HANDOVER_STATS": True,
                        "RCM_MT_SUB_STATS": True,
                        "RCM_MT_DN_STATS": False
                    }
                    
                    message_id_status = retry_check_message_id(env, message_id, disable_flags)
                    
                    if message_id_status:
                        test_result = 'PASS'
                    else:
                        test_result = 'FAIL'
                else:
                    print("Message ID is missing in the response. Test case FAILED.")
                    test_result = 'FAIL'
            else:
                print("MID is missing in the response. Test case FAILED.")
                test_result = 'FAIL'
        else:
            if compare_json(api_response, json.loads(expected_response)):
                test_result = 'PASS'
            else:
                print("Response mismatch. Test case FAILED.")
                test_result = 'FAIL'
    else:
        print(f"Test Case ID {test_case_id}: API request failed.")
        test_result = 'FAIL'

    print(f"Test Case Result: {test_result}")
    print("---------------------\n")
    return test_result