import json
import sys
import urllib.request


def main():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(exc)
        sys.exit(1)

    if payload.get("status") == "healthy" and payload.get("rag_ready") is True:
        sys.exit(0)

    print(payload)
    sys.exit(1)


if __name__ == "__main__":
    main()
