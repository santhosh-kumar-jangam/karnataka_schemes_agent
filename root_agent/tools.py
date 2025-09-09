def save_application(app_uuid: str, scheme_name: str, aadhar_number: str, applicant_name: str, phone: str) -> dict:
    """
    Save a new scheme application into the database.

    Args:
        app_uuid (str): Application ID (uuid)
        scheme_name (str): Name of the scheme applied for
        aadhar_number (str): User's Aadhaar number
        applicant_name (str): Name of the applicant
        phone (str): Phone number of the applicant

    Returns:
        dict: {"application_uuid": str, "status": str}
    """
    import sqlite3, os

    from dotenv import load_dotenv
    load_dotenv()

    DB_PATH = os.getenv("APPLICATION_DB_PATH")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (application_uuid, scheme_name, aadhar_number, applicant_name, phone)
        VALUES (?, ?, ?, ?, ?)
        """, (app_uuid, scheme_name, aadhar_number, applicant_name, phone)
    )

    conn.commit()
    conn.close()

    return {"application_uuid": app_uuid, "status": "Submitted"}

def check_application_status(application_uuid: str) -> dict:
    """
    Fetch the status of a scheme application by its UUID.

    Args:
        application_uuid (str): Unique application ID

    Returns:
        dict: { "application_uuid": str, "status": str } if found,
              { "error": "Application not found" } otherwise
    """
    import sqlite3, os

    from dotenv import load_dotenv
    load_dotenv()

    DB_PATH = os.getenv("APPLICATION_DB_PATH")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT application_uuid, scheme_name, status
        FROM applications
        WHERE application_uuid = ?
        """, (application_uuid,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"application_uuid": row[0], "scheme_name": row[1], "status": row[2]}
    else:
        return {"error": "Application not found"}
    

from typing import Union

def api_gateway(endpoint:str, method:str, query_params: Union[dict, None], body: Union[dict, None]) -> dict :
    """
    Universal API Gateway to interact with any API endpoint.

    Args:
        endpoint (str): API endpoint URL.
        method (str): HTTP method (e.g., "GET", "POST", "PUT", etc.).
        query_params (Union[dict, None]): Dictionary of query parameters. Pass None if not applicable.
        body (Union[dict, None]): Dictionary of request body data. Pass None if not applicable.

    Returns:
        dict: Response received from the API call.

    Raises:
        ValueError: If any mandatory parameter is omitted.
    """
    import requests

    match method.upper():
        case "GET":
            response = requests.get(endpoint, params=query_params)
        case "POST":
            response = requests.post(endpoint, params=query_params, json=body)
        case "PUT":
            response = requests.put(endpoint, params=query_params, json=body)
        case "DELETE":
            response = requests.delete(endpoint, params=query_params, json=body)
        case _:
            return {
                "status_code": 400,
                "response_body": f"Unsupported HTTP method: {method}"
            }

    return {
        "status_code": response.status_code,
        "response_body": response.json() if response.headers.get("Content-Type", "").startswith("application/json") else response.text
    }