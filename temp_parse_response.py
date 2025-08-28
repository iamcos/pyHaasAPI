import json
from backtest_runtime_data_processed import BacktestData
import dacite

def main():
    with open("/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/documentation/get_backtest_runtime_response.json", "r") as f:
        response_json = json.load(f)

    data = response_json.get('Data', {})

    try:
        backtest_data = dacite.from_dict(data_class=BacktestData, data=data)
        print("Successfully parsed the response!")
        print(backtest_data)
    except Exception as e:
        print(f"Failed to parse response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
