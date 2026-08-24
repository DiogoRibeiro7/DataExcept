# main.py

from example_usage import perform_operation

from dataexcept import JobError


def main():
    user_data = {"name": "Alice"}  # missing email
    config = {"timeout": -5}  # invalid timeout

    try:
        result = perform_operation(user_data, config)
        print("Job completed:", result)
    except JobError as err:
        # Catches *any* of our custom exceptions
        print(f"[JobError] {err}")
    except Exception as exc:
        # Any other unforeseen error
        print(f"[Unexpected] {exc}")


if __name__ == "__main__":
    main()
