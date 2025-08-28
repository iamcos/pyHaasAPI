#!/usr/bin/env python3
"""
Test for single backtest data retrieval and structure verification.
"""

import unittest
import os
from dotenv import load_dotenv
from pyHaasAPI import api
from pyHaasAPI.backtest_object import BacktestObject
from pydantic import ValidationError
import io
import sys
import json

class TestSingleBacktestRetrieval(unittest.TestCase):

    def setUp(self):
        """Set up the test environment by loading credentials and authenticating."""
        load_dotenv()

        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        self.assertIsNotNone(api_email, "API_EMAIL not set")
        self.assertIsNotNone(api_password, "API_PASSWORD not set")

        self.executor = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        ).authenticate(
            email=api_email,
            password=api_password
        )

    def test_retrieve_and_verify_backtest_data(self):
        """Retrieve a single backtest and print the request/response."""
        lab_id = "6e04e13c-1a12-4759-b037-b6997f830edf"
        backtest_id = "0e3a5382-3de3-4be4-935e-9511bd3d7f66"

        # Capture stdout to see the request and response printed from api.py
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        bt_object = None
        try:
            bt_object = BacktestObject(self.executor, lab_id, backtest_id)
        except ValidationError as e:
            print(f"Pydantic validation error during BacktestObject creation: {e}")

        # Restore stdout
        sys.stdout = old_stdout

        # Print captured output for analysis
        output = captured_output.getvalue()
        
        print("---" + " Captured API Communication " + "---")
        print(output)
        print("---------------------------------")
        
        if bt_object:
            print("Backtest Object Metadata:", bt_object.metadata)
            print("Backtest Object Runtime:", bt_object.runtime)

        # Manually print the request and response from the captured output
        request_url_str = ""
        request_params_str = ""
        response_str = ""

        try:
            # Extract Request URL
            url_start = output.find('Request URL: ') + len('Request URL: ')
            url_end = output.find('Request Params: ')
            request_url_str = output[url_start:url_end].strip()

            # Extract Request Params
            params_start = output.find('Request Params: ') + len('Request Params: ')
            params_end = output.find('Response: ')
            request_params_str = output[params_start:params_end].strip()

            # Extract Response
            response_start = output.find('Response: ') + len('Response: ')
            response_end = output.find('---END_OF_RESPONSE---')
            response_str = output[response_start:response_end].strip()

            # Save the clean JSON response to a file
            with open("/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/documentation/get_backtest_runtime_response.json", "w") as f:
                json.dump(json.loads(response_str), f, indent=2)

        except Exception as e:
            print(f"Could not parse request/response from output: {e}")

        print("---" + " Raw Request " + "---")
        print(f"URL: {request_url_str}")
        print(f"Params: {request_params_str}")
        print("--------------------")

        print("---" + " Raw Response " + "---")
        print(response_str)
        print("---------------------")

        print("\n--- Analysis ---")
        print("Comparing with documentation/get_backtest_runtime.txt")
        
        try:
            with open('/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/documentation/get_backtest_runtime.txt', 'r') as f:
                expected_response_str = f.read()
            
            print("\nExpected Response from get_backtest_runtime.txt:")
            print(expected_response_str)
            
            # Basic comparison
            if response_str and expected_response_str:
                # Pre-process the expected response to remove the curl command
                expected_json_str = expected_response_str.split('response: ')[-1]
                if json.loads(response_str) == json.loads(expected_json_str):
                    print("\nResponse matches the expected example.")
                else:
                    print("\nResponse DOES NOT match the expected example.")
                    # Further analysis could be added here, e.g., comparing keys

        except FileNotFoundError:
            print("\nCould not find documentation/get_backtest_runtime.txt for comparison.")
        except json.JSONDecodeError:
            print("\nCould not parse JSON from response or expected response for comparison.")
        except Exception as e:
            print(f"An error occurred during comparison: {e}")


if __name__ == '__main__':
    unittest.main()
