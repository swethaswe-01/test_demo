def get_global_variables(env):
    env = env.lower()
    if env == "qa":
        params = {
            "test_data_path": "../test_data/zakkpay.xlsx",
            "DB_Host": "10.20.51.232",
            "DB_Port": 8123,
            "DB_Name":"rcm_billing",
            "Authentication": "Bearer Cv4zdo706u0P7YrwUMwRZA==",
            "Sender_ID": "917391093716",  
            "URL": "https://rcmqa.karix.com/services/rcm/sendMessage" 
        }

    elif env == "preprod":
        params = {
            "test_data_path": "../test_data/zakkpay.xlsx",
            "DB_Host": "10.20.51.220",
            "DB_Port": 8123,
            "DB_User": "wmdev",
            "DB_Password": "pXzEQYcM",
            "DB_Name": "rcm_billing",
            "Sender_ID": "918657878932",
            "URL": "https://rcmpreprod.karix.solutions/services/rcm/sendMessage",
            "Authentication": "Bearer nZzS0bxw6ktdt18/EofjfQ=="
        }

    elif env == "prod":
        params = {
            "test_data_path": "../test_data/zakkpay.xlsx",
            "DB_Host": "10.150.206.154",
            "DB_Port": 8123,
            "Sender_ID": "917997987578",
            "URL": "https://rcmapi.instaalerts.zone/services/rcm/sendMessage",
            "Authentication": "Bearer nZzS0bxw6ktdt18/EofjfQ=="
        }
    else:
        raise Exception(f"The given input environment '{env}' does not exist.")
    return params